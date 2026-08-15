from discord.commands import Option
from discord.ext import bridge, commands
from bot.utils.lineup import get_current_season_and_year, format_season_label
from bot.utils.scraper import fetch_lineup_current_with_links
from bot.utils.embeds import make_search_results_embed, make_search_no_result_embed
from bot.views.search_view import SearchView

# 表示・選択の最大件数（Discordのセレクトは最大25件）
MAX_RESULTS = 25


class SearchCog(commands.Cog):
    """/search コマンドをまとめた Cog"""

    def __init__(self, bot: bridge.Bot):
        self.bot = bot

    @bridge.bridge_command(name="search", description="今季ラインナップからアニメを検索します。")
    async def search_command(
        self,
        ctx: bridge.BridgeContext,
        query: Option(str, "検索ワードを入力してください", required=True)
        ):
        """今季ラインナップ内をキーワードで絞り込み、選択UIを表示"""
        await ctx.respond("コマンドを確認しました", delete_after=1)

        season, year = get_current_season_and_year()
        season_label = format_season_label(year, season)
        items, _links = await fetch_lineup_current_with_links(season)

        # 今季ラインナップ内をタイトル部分一致で絞り込み
        q = query.strip().lower()
        results = [(work_id, title, available) for work_id, title, available in items if q in title.lower()]

        if not results:
            await ctx.channel.send(embed=make_search_no_result_embed(query, season_label), delete_after=60)
            return

        embed = make_search_results_embed(query, season_label, results, MAX_RESULTS)
        view = SearchView(ctx, results[:MAX_RESULTS])
        await ctx.channel.send(embed=embed, view=view, delete_after=60)


def setup(bot: bridge.Bot):
    bot.add_cog(SearchCog(bot))
