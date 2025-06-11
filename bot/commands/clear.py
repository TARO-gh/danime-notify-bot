from discord.ext import bridge, commands
from discord import Embed
from bot.views.clear_view import ClearView

class ClearCog(commands.Cog):
    """/clear コマンドをまとめた Cog"""

    def __init__(self, bot: bridge.Bot):
        self.bot = bot

    @bridge.bridge_command(
        name="clear", 
        description="通知するアニメタイトルを全て削除します。"
    )
    async def clear_command(
        self,
        ctx: bridge.BridgeContext,
        ):
        """全件削除の確認UIを表示"""
        await ctx.respond("コマンドを確認しました", delete_after=1)
        embed = Embed(
            title="通知するアニメタイトルを全て削除します。",
            description="本当によろしいですか？",
            color=0xff4500
        )
        await ctx.channel.send(embed=embed, view=ClearView(), delete_after=60)


def setup(bot: bridge.Bot):
    bot.add_cog(ClearCog(bot))

