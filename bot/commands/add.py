from discord.commands import Option
from discord.ext import bridge, commands
from discord import Embed
from bot.utils.storage import add_to_watchlist
import selenium

class AddCog(commands.Cog):
    """/add コマンドをまとめた Cog"""

    def __init__(self, bot: bridge.Bot):
        self.bot = bot

    @bridge.bridge_command(
        name="add",
        description="通知するアニメタイトルを追加します。"
    )
    async def add_command(
        self,
        ctx: bridge.BridgeContext,
        workid: Option(int, "作品IDを入力してください", required=True)
    ):
        await ctx.respond("コマンドを確認しました", delete_after=1)
        try:
            await add_to_watchlist(ctx, workid)
        except selenium.common.exceptions.TimeoutException as e:
            await ctx.send(embed=Embed(
            title="作品IDが存在しません。", color=0xff4500
        ), delete_after=60)
        return
        

def setup(bot: bridge.Bot):
    bot.add_cog(AddCog(bot))
