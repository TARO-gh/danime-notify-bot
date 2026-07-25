import discord
from discord.ext import tasks
import datetime as dt
import selenium
import urllib3

from bot.config import TARGET_CHANNEL_ID as CHANNEL_ID
from bot.utils.storage import load_watchlist, save_watchlist
from bot.utils.scraper import fetch_initial_data
from bot.utils.robots import RobotsDisallowed
from bot.utils.embeds import (
    make_update_notification_embed,
    make_auto_delete_embed,
    make_manual_check_done_embed,
)

# 定期チェックを走らせる分（:01, :31）と多重起動ガード
CHECK_MINUTES = (1, 31)
CHECK_GUARD = dt.timedelta(minutes=5)
# この期間、更新が取得できない作品は自動削除する
STALE_THRESHOLD = dt.timedelta(days=15)
IDLE_ACTIVITY_NAME = "dアニメストアを30分に1回確認します。"

# 取得失敗時にスキップ扱い（＝自動削除の誤爆をさせない）にする例外。
# RobotsDisallowed を含めることで robots.txt 禁止時に watchlist が全消しされるのを防ぐ。
SKIP_EXCEPTIONS = (
    selenium.common.exceptions.TimeoutException,
    urllib3.exceptions.ReadTimeoutError,
    ValueError,
    RobotsDisallowed,
)


class UpdateChecker:
    """dアニメストアの更新確認ループとその実行状態を管理する。"""

    def __init__(self, bot):
        self.bot = bot
        self._running = False
        self._last_check = dt.datetime(2000, 1, 1, 0, 0, 0)

    def start(self):
        """定期チェックループを開始する。"""
        @tasks.loop(seconds=1)
        async def update_loop():
            await self.bot.wait_until_ready()
            now = dt.datetime.now()
            if now.minute in CHECK_MINUTES and now - self._last_check > CHECK_GUARD:
                self._last_check = now
                await self.run()

        update_loop.start()

    async def manual_run(self):
        """/update コマンド用。確認を実行し完了 Embed を返す。"""
        await self.run()
        return make_manual_check_done_embed()

    async def run(self):
        """
        保存データを読み込み、各作品の更新確認・通知を行い、保存を更新する。
        多重起動は self._running でガードする。
        """
        if self._running:
            print("更新確認は既に実行中です。")
            return
        self._running = True
        print(f"更新確認開始: {dt.datetime.now()}")
        try:
            channel = self.bot.get_channel(CHANNEL_ID)
            data = await load_watchlist()
            del_workid_list = []

            for idx, item in enumerate(data):
                await self._set_presence_checking(idx + 1, len(data))
                if await self._process_item(item, channel):
                    del_workid_list.append(item['work_id'])

            # 確認処理中に追加/削除された作品を反映してから自動削除・保存
            data = await self._merge_concurrent_changes(data)
            data = await self._apply_auto_deletes(data, del_workid_list, channel)
            save_watchlist(data)
        finally:
            self._running = False
            await self._set_presence_idle()
            print(f"更新確認終了: {dt.datetime.now()}")

    async def _process_item(self, item, channel) -> bool:
        """
        1作品を処理する。新エピソードがあれば通知し、無ければスケジュールのみ更新。
        一定期間更新が取得できず自動削除の対象となる場合に True を返す。
        """
        work_id = item['work_id']
        last_update = dt.datetime.strptime(item['latest_update_date'], "%Y-%m-%d %H:%M:%S")

        try:
            info = await fetch_initial_data(int(work_id))
        except SKIP_EXCEPTIONS as e:
            print(f"作品ID {work_id} の情報取得中にエラーが発生したため、スキップします。エラー: {e}")
            return False

        if not info:
            print(f"作品ID {work_id} の情報が取得できませんでした。スキップします。")
            return self._is_stale(last_update)

        if info['latest_part_id'] != item.get('latest_part_id'):
            # 新エピソード → 更新して通知
            item.update(info)
            await channel.send(embed=make_update_notification_embed(info))
            return False

        # 変化なし: スケジュール情報だけ更新
        item['schedule_day'] = info['schedule_day']
        item['schedule_time'] = info['schedule_time']
        return self._is_stale(last_update)

    async def _merge_concurrent_changes(self, data):
        """
        確認処理中（数分かかる）に別コマンドで追加/削除された作品を data に反映する。
        """
        orig_ids = {item['work_id'] for item in data}
        latest_file = await load_watchlist()
        latest_ids = {it['work_id'] for it in latest_file}

        # 途中で追加された作品を取り込む
        added_ids = latest_ids - orig_ids
        if added_ids:
            print("途中追加を確認:", added_ids)
            for it in latest_file:
                if it['work_id'] in added_ids:
                    data.append(it)

        # 途中で削除された作品を除外する
        removed_ids = orig_ids - latest_ids
        if removed_ids:
            print("途中削除を確認:", removed_ids)
            data = [it for it in data if it['work_id'] not in removed_ids]

        return data

    async def _apply_auto_deletes(self, data, del_workid_list, channel):
        """一定期間更新がなかった作品を通知して削除し、残りのリストを返す。"""
        if not del_workid_list:
            return data
        print("自動削除対象:", del_workid_list)
        del_data = [item for item in data if item['work_id'] in del_workid_list]
        for item in del_data:
            await channel.send(embed=make_auto_delete_embed(item))
        return [item for item in data if item['work_id'] not in del_workid_list]

    @staticmethod
    def _is_stale(last_update: dt.datetime) -> bool:
        """最終更新から STALE_THRESHOLD を超えていれば True。"""
        return dt.datetime.now() - last_update > STALE_THRESHOLD

    async def _set_presence_checking(self, current: int, total: int):
        await self.bot.change_presence(
            activity=discord.Activity(
                name=f"更新確認中...({current}/{total})",
                type=discord.ActivityType.playing,
            )
        )

    async def _set_presence_idle(self):
        await self.bot.change_presence(
            activity=discord.Activity(
                name=IDLE_ACTIVITY_NAME,
                type=discord.ActivityType.playing,
            )
        )


# --- 既存インターフェース（main.py / update.py はこれを使い続ける） ---

def start_update_loop(bot):
    """
    更新確認ループを生成・開始し、インスタンスを bot に保持させる。

    on_ready は再接続のたびに再発火するため、二重起動を防ぐ。
    ガード状態（_last_check / _running）がインスタンス単位になった結果、
    複数ループが並走すると同じ通知が重複送信される（過去の不具合）ため、
    既に起動済みなら何もしない。
    """
    if getattr(bot, "update_checker", None) is not None:
        print("更新確認ループは既に起動済みのため、再起動をスキップします。")
        return
    checker = UpdateChecker(bot)
    bot.update_checker = checker
    checker.start()


async def manual_check_updates(bot):
    """/update コマンド用の薄いラッパ。"""
    return await bot.update_checker.manual_run()
