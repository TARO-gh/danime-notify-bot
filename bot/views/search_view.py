import discord
from bot.utils.storage import add_to_watchlist
import selenium

class SearchView(discord.ui.View):
    """
    検索結果選択用の View
    options: list of (work_id, title)
    """
    def __init__(self, ctx: discord.ext.bridge.BridgeContext, options: list, timeout: float = 180.0):
        super().__init__(timeout=timeout)
        self.ctx = ctx
        select_options = [
            discord.SelectOption(label=title.text.strip()[:25], value=str(work_id))
            for work_id, title in options[:10]
        ]
        self.select = discord.ui.Select(
            placeholder='追加するアニメを選択',
            options=select_options,
            min_values=1,
            max_values=1
        )
        self.select.callback = self.callback
        self.add_item(self.select)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        await interaction.message.delete()
        work_id = int(self.select.values[0])
        try:
            await add_to_watchlist(self.ctx, work_id)
        except selenium.common.exceptions.TimeoutException:
            await interaction.channel.send(
                embed=discord.Embed(
                    title="エラーが発生しました。",
                    color=0xff4500
                ),
                delete_after=60
            )
            return
        self.stop()
