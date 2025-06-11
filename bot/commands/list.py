from discord.ext import bridge, commands
from discord import Embed
from bot.utils.storage import load_watchlist

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
        if not data:
            text = "現在通知するアニメタイトルはありません。"
        else:
            text = "\n".join(f"・{item['work_title']} (ID: {item['work_id']})" for item in data)
        embed = Embed(title="更新通知リスト", description=text, color=0xff4500)
        await ctx.channel.send(embed=embed, delete_after=60)

def setup(bot: bridge.Bot):
    bot.add_cog(ListCog(bot))


