from discord.commands import Option
from discord.ext import bridge, commands
from bot.utils.storage import remove_from_watchlist

class DeleteCog(commands.Cog):
    """/del コマンドをまとめた Cog"""

    def __init__(self, bot: bridge.Bot):
        self.bot = bot

    @bridge.bridge_command(name="del", description="通知するアニメタイトルを削除します。")
    async def delete_command(
        self,
        ctx: bridge.BridgeContext,
        workid: Option(int, "作品IDを入力してください", required=True)
        ):
        """作品IDをウォッチリストから削除"""
        await ctx.respond("コマンドを確認しました", delete_after=1)
        await remove_from_watchlist(ctx, workid)

def setup(bot: bridge.Bot):
    bot.add_cog(DeleteCog(bot))


