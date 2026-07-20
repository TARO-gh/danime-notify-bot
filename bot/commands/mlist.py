from discord.ext import bridge, commands
from bot.utils.manual import load_manual_list
from bot.utils.manual_embeds import make_manual_list_embed


class ManualListCog(commands.Cog):
    """/mlist コマンドをまとめた Cog"""

    def __init__(self, bot: bridge.Bot):
        self.bot = bot

    @bridge.bridge_command(name="mlist", description="手動通知するタイトルの一覧を表示します。")
    async def manual_list_command(
        self,
        ctx: bridge.BridgeContext,
    ):
        """手動通知リストを曜日ごとに表示"""
        await ctx.respond("コマンドを確認しました", delete_after=1)
        embed = make_manual_list_embed(load_manual_list())
        await ctx.channel.send(embed=embed, delete_after=60)


def setup(bot: bridge.Bot):
    bot.add_cog(ManualListCog(bot))
