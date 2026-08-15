from discord.ext import bridge, commands
from bot.utils.storage import load_watchlist
from bot.utils.embeds import make_list_embed


class ListCog(commands.Cog):
    """/list コマンドをまとめた Cog"""

    def __init__(self, bot: bridge.Bot):
        self.bot = bot

    @bridge.bridge_command(name="list", description="通知するアニメタイトルのリストを確認します。")
    async def list_command(
        self,
        ctx: bridge.BridgeContext,
        ):
        """現在のウォッチリストを表示"""
        await ctx.respond("コマンドを確認しました", delete_after=1)
        data = await load_watchlist()
        await ctx.channel.send(embed=make_list_embed(data), delete_after=60)


def setup(bot: bridge.Bot):
    bot.add_cog(ListCog(bot))
