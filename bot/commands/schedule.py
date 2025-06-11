from discord.ext import bridge, commands
from bot.utils.embeds import make_schedule_embed
from bot.utils.storage import load_watchlist
import discord

class ScheduleCog(commands.Cog):
    """/schedule コマンドをまとめた Cog"""

    def __init__(self, bot: bridge.Bot):
        self.bot = bot

    @bridge.bridge_command(name="schedule", description="通知するアニメタイトルの更新スケジュールを確認します。")
    async def schedule_command(
        self,
        ctx: bridge.BridgeContext,
        ):
        """曜日ごとの配信予定を表示"""
        await ctx.respond("コマンドを確認しました", delete_after=1)
        data = await load_watchlist()
        # ここで曜日ソート＆Embed作成のロジックを呼び出す
        embed = make_schedule_embed(data)
        await ctx.channel.send(embed=embed, delete_after=60)

def setup(bot: bridge.Bot):
    bot.add_cog(ScheduleCog(bot))


