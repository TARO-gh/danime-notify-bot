from discord.commands import Option
from discord.ext import bridge, commands
from bot.utils.manual import remove_manual_entry
from bot.utils.manual_embeds import make_manual_remove_result_embed


class ManualDeleteCog(commands.Cog):
    """/mdel コマンドをまとめた Cog"""

    def __init__(self, bot: bridge.Bot):
        self.bot = bot

    @bridge.bridge_command(name="mdel", description="手動通知するタイトルを削除します。")
    async def manual_delete_command(
        self,
        ctx: bridge.BridgeContext,
        entry_id: Option(str, "IDを入力してください（例: m1）", required=True),
    ):
        """手動通知リストから削除"""
        await ctx.respond("コマンドを確認しました", delete_after=1)
        status, deleted = await remove_manual_entry(entry_id)
        await ctx.send(embed=make_manual_remove_result_embed(status, deleted), delete_after=60)


def setup(bot: bridge.Bot):
    bot.add_cog(ManualDeleteCog(bot))
