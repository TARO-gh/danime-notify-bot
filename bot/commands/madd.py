from discord.commands import Option
from discord.ext import bridge, commands
from bot.utils.manual import add_manual_entry, WEEKDAY_NAMES
from bot.utils.manual_embeds import make_manual_add_result_embed


class ManualAddCog(commands.Cog):
    """/madd コマンドをまとめた Cog"""

    def __init__(self, bot: bridge.Bot):
        self.bot = bot

    @bridge.bridge_command(
        name="madd",
        description="dアニメストア以外のタイトルを手動で追加し、指定曜日・時刻に毎週通知します。"
    )
    async def manual_add_command(
        self,
        ctx: bridge.BridgeContext,
        title: Option(str, "タイトルを入力してください", required=True),
        day: Option(str, "通知する曜日", choices=WEEKDAY_NAMES, required=True),
        time: Option(str, "通知する時刻（HH:MM 形式、例: 23:30）", required=True),
        image_url: Option(str, "通知に表示する画像のURL", required=False, default=None),
    ):
        await ctx.respond("コマンドを確認しました", delete_after=1)
        status, entry = await add_manual_entry(title, day, time, image_url)
        embed = make_manual_add_result_embed(status, entry, ctx.author.display_name)
        if status == "ok":
            await ctx.send(embed=embed)
        else:
            await ctx.send(embed=embed, delete_after=60)


def setup(bot: bridge.Bot):
    bot.add_cog(ManualAddCog(bot))
