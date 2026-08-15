import discord
from bot.utils.storage import add_to_watchlist
from bot.utils.embeds import make_add_result_embed, make_search_unavailable_embed


class SearchView(discord.ui.View):
    """
    検索結果選択用の View
    options: list of (work_id, title, available)   # title は文字列
    """
    def __init__(self, ctx: discord.ext.bridge.BridgeContext, options: list, timeout: float = 180.0):
        super().__init__(timeout=timeout)
        self.ctx = ctx
        # 配信開始前（available=False）の作品を選択時に判定するためのマップ
        self.availability = {str(work_id): available for work_id, _, available in options}
        select_options = [
            discord.SelectOption(
                label=title.strip()[:25],
                value=str(work_id),
                description=None if available else "配信予定（追加は配信開始後）",
            )
            for work_id, title, available in options[:25]
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
        work_id_str = self.select.values[0]
        # 配信開始前の作品は追加せず、その旨を通知
        if not self.availability.get(work_id_str, True):
            await interaction.channel.send(embed=make_search_unavailable_embed(), delete_after=60)
            self.stop()
            return
        status, info = await add_to_watchlist(int(work_id_str))
        embed = make_add_result_embed(status, info, self.ctx.author.display_name)
        if status == "ok":
            await interaction.channel.send(embed=embed)
        else:
            await interaction.channel.send(embed=embed, delete_after=60)
        self.stop()
