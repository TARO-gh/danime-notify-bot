from discord.commands import Option
from discord.ext import bridge, commands
from discord import Embed
from bot.utils.scraper import search_anime
from bot.views.search_view import SearchView

class SearchCog(commands.Cog):
    """/search コマンドをまとめた Cog"""

    def __init__(self, bot: bridge.Bot):
        self.bot = bot

    @bridge.bridge_command(name="search", description="アニメを検索します。")
    async def search_command(
        self,
        ctx: bridge.BridgeContext,
        query: Option(str, "検索ワードを入力してください", required=True)
        ):
        """dアニメストアでアニメを検索し、選択UIを表示"""
        await ctx.respond("コマンドを確認しました", delete_after=1)
        results = await search_anime(query)
        if not results:
            embed = Embed(
                title=f"'{query}'検索結果",
                description=f"'{query}'の検索結果が見つかりませんでした。",
                color=0xff4500
            )
            await ctx.channel.send(embed=embed, delete_after=60)
            return
        text = ""
        for idx, (workid, title) in enumerate(results):
            if idx == 10: break
            workid, title = workid, title.text
            text = text + f"{idx+1}. {title}\n"
        embed = Embed(
                title=f"'{query}'検索結果",
                description = text,
                color=0xff4500
            )
        view = SearchView(ctx, results)
        await ctx.channel.send(embed=embed, view=view, delete_after=60)

def setup(bot: bridge.Bot):
    bot.add_cog(SearchCog(bot))


