"""
手動登録タイトルの通知機能。

dアニメストアのスクレイピングとは完全に独立した仕組みで、ユーザーが指定した
曜日・時刻に毎週通知を出し続ける。削除されるまで自動削除は行わない。
永続化からループまでこのモジュール内で完結させ、既存の watchlist 側
（storage.py / checker.py）には一切依存しない。
"""

import os
import json
import datetime as dt

import discord
from discord.ext import tasks

from bot.config import TARGET_CHANNEL_ID as CHANNEL_ID
from bot.utils.manual_embeds import make_manual_notification_embed

# opt ディレクトリへのパス設定（storage.py と同じ場所を使う）
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'opt'))
MANUAL_FILE = 'manual_info.json'

# tzdata に依存せずに JST を扱う（通知は時刻精度が本質のため UTC 環境でもズラさない）
JST = dt.timezone(dt.timedelta(hours=9), 'JST')

# 曜日の表示名。インデックスは dt.date.weekday() と同じ（0=月 … 6=日）
WEEKDAY_NAMES = ["月", "火", "水", "木", "金", "土", "日"]


def _path() -> str:
    return os.path.join(BASE_DIR, MANUAL_FILE)


def load_manual_list() -> list:
    """手動登録リストを読み込む。ファイルが無ければ空リスト。"""
    if not os.path.exists(_path()):
        return []
    with open(_path(), 'r', encoding='utf-8') as f:
        return json.load(f)


def save_manual_list(data: list):
    """手動登録リストを保存する。"""
    os.makedirs(BASE_DIR, exist_ok=True)
    with open(_path(), 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _next_entry_id(data: list) -> str:
    """既存の m1, m2 … と衝突しない ID を採番する。"""
    used = set()
    for item in data:
        entry_id = item.get('entry_id', '')
        if entry_id.startswith('m') and entry_id[1:].isdigit():
            used.add(int(entry_id[1:]))
    return f"m{max(used) + 1 if used else 1}"


def parse_time(value: str):
    """"HH:MM" を検証して正規化する。不正なら None。"""
    try:
        parsed = dt.datetime.strptime(value.strip(), "%H:%M")
    except ValueError:
        return None
    return parsed.strftime("%H:%M")


def parse_day(value: str):
    """"月"〜"日"（"月曜日" 等も可）を曜日インデックスに変換する。不正なら None。"""
    head = value.strip()[:1]
    return WEEKDAY_NAMES.index(head) if head in WEEKDAY_NAMES else None


def _is_valid_image_url(url: str) -> bool:
    return url.startswith("http://") or url.startswith("https://")


async def add_manual_entry(title: str, day: str, time: str, image_url: str = None):
    """
    手動登録タイトルを追加する。表示は行わず、結果ステータスを返す。
    戻り値: (status, entry)
      - ("bad_day", None)   : 曜日の指定が不正
      - ("bad_time", None)  : 時刻の指定が不正
      - ("bad_image", None) : 画像URLが http(s) で始まっていない
      - ("ok", entry)       : 追加成功
    """
    day_index = parse_day(day)
    if day_index is None:
        return ("bad_day", None)

    normalized_time = parse_time(time)
    if normalized_time is None:
        return ("bad_time", None)

    if image_url and not _is_valid_image_url(image_url):
        return ("bad_image", None)

    data = load_manual_list()
    now = dt.datetime.now(JST)
    # 追加時点で今週の通知時刻を過ぎていれば、その回は済み扱いにして即時通知を防ぐ
    already_passed = _is_past_today(day_index, normalized_time, now)
    entry = {
        "entry_id": _next_entry_id(data),
        "title": title,
        "schedule_day": day_index,
        "schedule_time": normalized_time,
        # 追加完了時と通知時で同じ画像を使い続けるため、URL をそのまま保持する
        "image_url": image_url or None,
        "last_notified": now.strftime("%Y-%m-%d") if already_passed else None,
    }
    data.append(entry)
    save_manual_list(data)
    return ("ok", entry)


async def remove_manual_entry(entry_id: str):
    """
    手動登録タイトルを削除する。表示は行わず、結果ステータスを返す。
    戻り値: (status, deleted)
      - ("not_found", None) : 未登録
      - ("ok", deleted)     : 削除成功
    """
    entry_id = entry_id.strip()
    data = load_manual_list()
    new_list = [item for item in data if item['entry_id'] != entry_id]
    if len(new_list) == len(data):
        return ("not_found", None)
    deleted = next(item for item in data if item['entry_id'] == entry_id)
    save_manual_list(new_list)
    return ("ok", deleted)


def _is_past_today(entry_day: int, entry_time: str, now: dt.datetime) -> bool:
    """now が entry の曜日で、かつ通知時刻を過ぎているか。"""
    return now.weekday() == entry_day and now.strftime("%H:%M") >= entry_time


def _should_notify(entry: dict, now: dt.datetime) -> bool:
    """
    今この entry を通知すべきか。
    「該当曜日で通知時刻を過ぎており、当日まだ通知していない」を条件にすることで、
    通知時刻の瞬間に Bot が落ちていても復帰後に取りこぼしを拾える。
    """
    if not _is_past_today(entry['schedule_day'], entry['schedule_time'], now):
        return False
    return entry.get('last_notified') != now.strftime("%Y-%m-%d")


def _mark_notified(entry_id: str, date_str: str):
    """通知済みフラグを立てる。コマンド側の追加/削除を潰さないよう読み直して保存する。"""
    data = load_manual_list()
    for item in data:
        if item['entry_id'] == entry_id:
            item['last_notified'] = date_str
            break
    else:
        # ループ中に削除された場合は何もしない
        return
    save_manual_list(data)


class ManualNotifier:
    """手動登録タイトルの通知ループ。"""

    def __init__(self, bot):
        self.bot = bot

    def start(self):
        """通知ループを開始する。"""
        @tasks.loop(seconds=30)
        async def notify_loop():
            await self.bot.wait_until_ready()
            await self.run_once()

        notify_loop.start()

    async def run_once(self):
        """通知対象を1周ぶん確認して送信する。"""
        now = dt.datetime.now(JST)
        today = now.strftime("%Y-%m-%d")
        channel = self.bot.get_channel(CHANNEL_ID)
        if channel is None:
            return

        for entry in load_manual_list():
            if not _should_notify(entry, now):
                continue
            try:
                await channel.send(embed=make_manual_notification_embed(entry))
            except discord.DiscordException as e:
                print(f"手動通知の送信に失敗しました（{entry['entry_id']}）。エラー: {e}")
                continue
            _mark_notified(entry['entry_id'], today)


def start_manual_notify_loop(bot):
    """通知ループを生成・開始し、インスタンスを bot に保持させる。"""
    notifier = ManualNotifier(bot)
    bot.manual_notifier = notifier
    notifier.start()
