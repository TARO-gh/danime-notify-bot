from discord.commands import Option
from discord.ext import bridge, commands
from bot.utils.storage import add_to_watchlist
from bot.utils.embeds import make_add_result_embed


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
        status, info = await add_to_watchlist(workid)
        embed = make_add_result_embed(status, info, ctx.author.display_name)
        if status == "ok":
            await ctx.send(embed=embed)
        else:
            await ctx.send(embed=embed, delete_after=60)


def setup(bot: bridge.Bot):
    bot.add_cog(AddCog(bot))
