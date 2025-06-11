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
