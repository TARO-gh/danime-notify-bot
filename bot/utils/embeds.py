import discord

def make_schedule_embed(data: list) -> discord.Embed:
    """
    save_info.json の data を受け取って
    曜日ごとのスケジュール Embed を返す
    """
    days = {i: [] for i in range(7)}
    kanji = ["月","火","水","木","金","土","日"]

    # data を曜日ごとに振り分け
    for item in data:
        d = item.get("schedule_day", 7)
        days.setdefault(d, []).append(item)

    embed = discord.Embed(title="更新スケジュール", color=0xff4500)
    for d, items in days.items():
        if not items: continue
        # 時刻ソート
        items.sort(key=lambda x: x["schedule_time"])
        text = "\n".join(
            f"{it['schedule_time']} {it['work_title']} (ID: {it['work_id']})"
            for it in items
        )
        name = kanji[d] + "曜日" if d < 7 else "情報なし"
        embed.add_field(name=name, value=text, inline=False)

    return embed


def make_lineup_embed(season_label: str, items: list[tuple[str, str]]) -> discord.Embed:
    max_items = 60
    lines = []
    for idx, (_, title) in enumerate(items[:max_items]):
        lines.append(f"{idx+1}. {title}")

    description = "\n".join(lines)
    if len(description) > 3800:
        description = description[:3790] + "\n..."

    embed = discord.Embed(
        title=f"{season_label} アニメラインナップ",
        description=description if description else "該当作品が見つかりませんでした。",
        color=0xff4500,
    )
    embed.set_footer(text=f"全{len(items)}件 / 表示{min(len(items), max_items)}件")
    return embed
