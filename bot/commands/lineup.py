from discord.ext import bridge, commands
from bot.utils.lineup import get_current_season_and_year, format_season_label
from bot.utils.scraper import fetch_lineup_current_with_links
from bot.utils.embeds import make_lineup_embed
from bot.views.lineup_view import LineupView
import discord


class LineupCog(commands.Cog):
    """/lineup コマンドをまとめた Cog"""

    def __init__(self, bot: bridge.Bot):
        self.bot = bot

    @bridge.bridge_command(name="lineup", description="今季のアニメラインナップを表示します。")
    async def lineup_command(self, ctx: bridge.BridgeContext):
        await ctx.respond("コマンドを確認しました", delete_after=1)

        season, year = get_current_season_and_year()
        items, links = await fetch_lineup_current_with_links(season)
        if not items:
            embed = discord.Embed(
                title="ラインナップの取得に失敗しました。",
                description="時間を置いて再試行してください。",
                color=0xff4500,
            )
            await ctx.channel.send(embed=embed, delete_after=60)
            return

        season_label = format_season_label(year, season)
        embed = make_lineup_embed(season_label, items)
        base_url = f"https://animestore.docomo.ne.jp/animestore/CF/{season}"
        if links:
            existing = {url for _, url in links}
            if base_url not in existing:
                links = [(season_label, base_url)] + links
            else:
                links = [(season_label, base_url)] + [(label, url) for label, url in links if url != base_url]
        else:
            links = [(season_label, base_url)]

        view = LineupView(ctx, links, base_url)
        await ctx.channel.send(embed=embed, view=view, delete_after=60)


def setup(bot: bridge.Bot):
    bot.add_cog(LineupCog(bot))
