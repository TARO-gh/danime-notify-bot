from discord.commands import Option
from discord.ext import bridge, commands
from discord import Embed
from bot.utils.lineup import get_current_season_and_year, format_season_label
from bot.utils.scraper import fetch_lineup_current_with_links
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
            embed = Embed(
                title=f"'{query}' 検索結果",
                description=(
                    f"{season_label}のラインナップ内に該当する作品が見つかりませんでした。\n"
                    "一覧にない作品は `/add <作品ID>` で追加できます。"
                ),
                color=0xff4500
            )
            await ctx.channel.send(embed=embed, delete_after=60)
            return

        text = "".join(
            f"{idx+1}. {title}{'' if available else '（配信予定）'}\n"
            for idx, (work_id, title, available) in enumerate(results[:MAX_RESULTS])
        )
        embed = Embed(
            title=f"'{query}' 検索結果",
            description=text,
            color=0xff4500
        )
        embed.set_footer(text=f"{season_label}ラインナップ内 / 該当{len(results)}件")
        view = SearchView(ctx, results[:MAX_RESULTS])
        await ctx.channel.send(embed=embed, view=view, delete_after=60)


def setup(bot: bridge.Bot):
    bot.add_cog(SearchCog(bot))
