import discord
from typing import Optional

# 全Embed共通のテーマカラー
EMBED_COLOR = 0xff4500

CI_PC_URL = "https://animestore.docomo.ne.jp/animestore/ci_pc"


def make_schedule_embed(data: list) -> discord.Embed:
    """
    save_info.json の data を受け取って
    曜日ごとのスケジュール Embed を返す
    """
    days = {i: [] for i in range(7)}
    kanji = ["月", "火", "水", "木", "金", "土", "日"]

    # data を曜日ごとに振り分け
    for item in data:
        d = item.get("schedule_day", 7)
        days.setdefault(d, []).append(item)

    embed = discord.Embed(title="更新スケジュール", color=EMBED_COLOR)
    for d, items in days.items():
        if not items:
            continue
        # 時刻ソート
        items.sort(key=lambda x: x["schedule_time"])
        text = "\n".join(
            f"{it['schedule_time']} {it['work_title']} (ID: {it['work_id']})"
            for it in items
        )
        name = kanji[d] + "曜日" if d < 7 else "情報なし"
        embed.add_field(name=name, value=text, inline=False)

    return embed


def make_lineup_embed(season_label: str, items: list[tuple[str, str, bool]], url: Optional[str] = None) -> discord.Embed:
    max_items = 60
    lines = []
    for idx, item in enumerate(items[:max_items]):
        title = item[1]
        available = item[2] if len(item) > 2 else True
        mark = "" if available else "（配信予定）"
        lines.append(f"{idx+1}. {title}{mark}")

    description = "\n".join(lines)
    if len(description) > 3800:
        description = description[:3790] + "\n..."

    if not description:
        description = "該当作品が見つかりませんでした。"

    if url:
        description = f"{description}\n\n[dアニメストアでラインナップを見る]({url})"

    embed = discord.Embed(
        title=f"{season_label} アニメラインナップ",
        description=description,
        color=EMBED_COLOR,
    )
    embed.set_footer(text=f"全{len(items)}件 / 表示{min(len(items), max_items)}件")
    return embed


def make_lineup_fetch_failed_embed() -> discord.Embed:
    return discord.Embed(
        title="ラインナップの取得に失敗しました。",
        description="時間を置いて再試行してください。",
        color=EMBED_COLOR,
    )


# --- /list ---

def make_list_embed(data: list) -> discord.Embed:
    if not data:
        text = "現在通知するアニメタイトルはありません。"
    else:
        text = "\n".join(f"・{item['work_title']} (ID: {item['work_id']})" for item in data)
    return discord.Embed(title="更新通知リスト", description=text, color=EMBED_COLOR)


# --- /search ---

def make_search_results_embed(query: str, season_label: str, results: list, max_results: int = 25) -> discord.Embed:
    text = "".join(
        f"{idx+1}. {title}{'' if available else '（配信予定）'}\n"
        for idx, (work_id, title, available) in enumerate(results[:max_results])
    )
    embed = discord.Embed(title=f"'{query}' 検索結果", description=text, color=EMBED_COLOR)
    embed.set_footer(text=f"{season_label}ラインナップ内 / 該当{len(results)}件")
    return embed


def make_search_no_result_embed(query: str, season_label: str) -> discord.Embed:
    return discord.Embed(
        title=f"'{query}' 検索結果",
        description=(
            f"{season_label}のラインナップ内に該当する作品が見つかりませんでした。\n"
            "一覧にない作品は `/add <作品ID>` で追加できます。"
        ),
        color=EMBED_COLOR,
    )


def make_search_unavailable_embed() -> discord.Embed:
    return discord.Embed(
        title="まだ追加できません。",
        description="この作品は配信開始前です。配信開始後に追加してください。",
        color=EMBED_COLOR,
    )


# --- /add （storage.add_to_watchlist の結果を描画） ---

def make_add_success_embed(info: dict, author_name: str) -> discord.Embed:
    url = f"{CI_PC_URL}?workId={info['work_id']}"
    embed = discord.Embed(
        title="通知するアニメタイトルを追加しました。",
        description=f"{info['work_title']} (ID: {info['work_id']})\n{url}",
        color=EMBED_COLOR,
    )
    embed.set_image(url=info['work_thumbnail_url'])
    embed.set_footer(text=f"追加者: {author_name}")
    return embed


def make_add_duplicate_embed() -> discord.Embed:
    return discord.Embed(title="既に追加されています。", color=EMBED_COLOR)


def make_add_robots_disallowed_embed() -> discord.Embed:
    return discord.Embed(
        title="追加できませんでした。",
        description="robots.txt により許可されていないため取得できません。",
        color=EMBED_COLOR,
    )


def make_add_failed_embed() -> discord.Embed:
    return discord.Embed(
        title="追加できませんでした。",
        description="配信開始前か、作品IDが存在しません。",
        color=EMBED_COLOR,
    )


def make_add_result_embed(status: str, info: Optional[dict] = None, author_name: Optional[str] = None) -> discord.Embed:
    """add_to_watchlist の返すステータスに対応する Embed を返す。"""
    if status == "ok":
        return make_add_success_embed(info, author_name)
    if status == "duplicate":
        return make_add_duplicate_embed()
    if status == "robots":
        return make_add_robots_disallowed_embed()
    return make_add_failed_embed()


# --- /del （storage.remove_from_watchlist の結果を描画） ---

def make_remove_success_embed(deleted: dict) -> discord.Embed:
    return discord.Embed(
        title="通知するアニメタイトルを削除しました。",
        description=f"{deleted['work_title']} (ID: {deleted['work_id']})",
        color=EMBED_COLOR,
    )


def make_remove_not_found_embed() -> discord.Embed:
    return discord.Embed(title="作品IDが存在しないか、追加されていません。", color=EMBED_COLOR)


def make_remove_result_embed(status: str, deleted: Optional[dict] = None) -> discord.Embed:
    if status == "ok":
        return make_remove_success_embed(deleted)
    return make_remove_not_found_embed()


# --- /clear ---

def make_clear_confirm_embed() -> discord.Embed:
    return discord.Embed(
        title="通知するアニメタイトルを全て削除します。",
        description="本当によろしいですか？",
        color=EMBED_COLOR,
    )


def make_clear_done_embed() -> discord.Embed:
    return discord.Embed(title="通知するアニメタイトルを全て削除しました。", color=EMBED_COLOR)


def make_clear_cancel_embed() -> discord.Embed:
    return discord.Embed(title="キャンセルしました。", color=EMBED_COLOR)


# --- 更新ループ（checker） ---

def make_update_notification_embed(info: dict) -> discord.Embed:
    url = f"{CI_PC_URL}?workId={info['work_id']}&partId={info['latest_part_id']}"
    embed = discord.Embed(
        title="以下のアニメが更新されました。",
        description=f"{info['work_title']}\n第{int(info['latest_part_id'][-3:])}話: {info['latest_part_title']}\n{url}",
        color=EMBED_COLOR,
    )
    embed.set_image(url=info['latest_part_thumbnail_url'])
    return embed


def make_auto_delete_embed(item: dict) -> discord.Embed:
    embed = discord.Embed(
        title="以下のアニメは一定期間更新がなかったため、自動削除されました。",
        description=f"{item['work_title']} (ID: {item['work_id']})",
        color=EMBED_COLOR,
    )
    embed.set_image(url=item['work_thumbnail_url'])
    return embed


def make_manual_check_done_embed() -> discord.Embed:
    return discord.Embed(title="更新確認処理が終了しました。", description="", color=EMBED_COLOR)
