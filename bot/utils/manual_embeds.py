"""手動登録タイトル用の Embed 生成。既存 embeds.py と同じテーマカラーを使う。"""

import discord
from typing import Optional

from bot.utils.embeds import EMBED_COLOR

# 曜日の表示名（manual.py と同じ順序）
WEEKDAY_NAMES = ["月", "火", "水", "木", "金", "土", "日"]


def _schedule_text(entry: dict) -> str:
    return f"毎週{WEEKDAY_NAMES[entry['schedule_day']]}曜日 {entry['schedule_time']}"


def _set_image(embed: discord.Embed, entry: dict) -> discord.Embed:
    """登録時に指定された画像を設定する。未指定なら何もしない。"""
    if entry.get('image_url'):
        embed.set_image(url=entry['image_url'])
    return embed


# --- /madd ---

def make_manual_add_success_embed(entry: dict, author_name: str) -> discord.Embed:
    embed = discord.Embed(
        title="手動通知するタイトルを追加しました。",
        description=f"{entry['title']} (ID: {entry['entry_id']})\n{_schedule_text(entry)}",
        color=EMBED_COLOR,
    )
    _set_image(embed, entry)
    embed.set_footer(text=f"追加者: {author_name}")
    return embed


def make_manual_add_bad_day_embed() -> discord.Embed:
    return discord.Embed(
        title="追加できませんでした。",
        description="曜日は 月・火・水・木・金・土・日 から指定してください。",
        color=EMBED_COLOR,
    )


def make_manual_add_bad_time_embed() -> discord.Embed:
    return discord.Embed(
        title="追加できませんでした。",
        description="時刻は HH:MM 形式（例: 23:30）で指定してください。",
        color=EMBED_COLOR,
    )


def make_manual_add_bad_image_embed() -> discord.Embed:
    return discord.Embed(
        title="追加できませんでした。",
        description="画像URLは http:// または https:// から始まる必要があります。",
        color=EMBED_COLOR,
    )


def make_manual_add_result_embed(status: str, entry: Optional[dict] = None,
                                 author_name: Optional[str] = None) -> discord.Embed:
    """add_manual_entry の返すステータスに対応する Embed を返す。"""
    if status == "ok":
        return make_manual_add_success_embed(entry, author_name)
    if status == "bad_day":
        return make_manual_add_bad_day_embed()
    if status == "bad_time":
        return make_manual_add_bad_time_embed()
    return make_manual_add_bad_image_embed()


# --- /mdel ---

def make_manual_remove_success_embed(deleted: dict) -> discord.Embed:
    return discord.Embed(
        title="手動通知するタイトルを削除しました。",
        description=f"{deleted['title']} (ID: {deleted['entry_id']})",
        color=EMBED_COLOR,
    )


def make_manual_remove_not_found_embed() -> discord.Embed:
    return discord.Embed(title="そのIDは登録されていません。", color=EMBED_COLOR)


def make_manual_remove_result_embed(status: str, deleted: Optional[dict] = None) -> discord.Embed:
    if status == "ok":
        return make_manual_remove_success_embed(deleted)
    return make_manual_remove_not_found_embed()


# --- /mlist ---

def make_manual_list_embed(data: list) -> discord.Embed:
    if not data:
        return discord.Embed(
            title="手動通知タイトル一覧",
            description="登録されているタイトルはありません。",
            color=EMBED_COLOR,
        )

    embed = discord.Embed(title="手動通知タイトル一覧", color=EMBED_COLOR)
    for day in range(7):
        items = [it for it in data if it['schedule_day'] == day]
        if not items:
            continue
        items.sort(key=lambda x: x['schedule_time'])
        text = "\n".join(
            f"{it['schedule_time']} {it['title']} (ID: {it['entry_id']})"
            for it in items
        )
        embed.add_field(name=f"{WEEKDAY_NAMES[day]}曜日", value=text, inline=False)
    return embed


# --- 通知ループ ---

def make_manual_notification_embed(entry: dict) -> discord.Embed:
    embed = discord.Embed(
        title="以下のタイトルの更新時刻になりました。",
        description=f"{entry['title']}\n{_schedule_text(entry)}",
        color=EMBED_COLOR,
    )
    _set_image(embed, entry)
    return embed
