from discord.ext import bridge, commands
from bot.utils.checker import manual_check_updates

class UpdateCog(commands.Cog):
    """/update コマンドをまとめた Cog"""

    def __init__(self, bot: bridge.Bot):
        self.bot = bot

    @bridge.bridge_command(name="update", description="更新確認処理を実行します。")
    async def update_command(
        self,
        ctx: bridge.BridgeContext,
        ):
        """即時に更新チェックを実行"""
        await ctx.respond("更新確認処理中...", delete_after=1)
        result = await manual_check_updates(self.bot)
        await ctx.channel.send(embed=result, delete_after=60)

def setup(bot: bridge.Bot):
    bot.add_cog(UpdateCog(bot))


