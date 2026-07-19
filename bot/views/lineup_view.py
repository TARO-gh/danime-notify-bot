import discord
from bot.utils.scraper import fetch_lineup_from_url
from bot.utils.embeds import make_lineup_embed, make_lineup_fetch_failed_embed


class LineupView(discord.ui.View):
    def __init__(
        self,
        ctx: discord.ext.bridge.BridgeContext,
        links: list[tuple[str, str]],
        current_url: str,
        timeout: float = 180.0,
    ):
        super().__init__(timeout=timeout)
        self.ctx = ctx
        self.links = links
        self.current_url = current_url
        self._build_select()

    def _build_select(self) -> None:
        if hasattr(self, "select"):
            self.remove_item(self.select)

        center_index = 0
        for idx, (_, url) in enumerate(self.links):
            if url == self.current_url:
                center_index = idx
                break

        window = 21
        start = max(center_index - (window // 2), 0)
        end = start + window
        if end > len(self.links):
            end = len(self.links)
            start = max(end - window, 0)

        options = []
        for label, url in self.links[start:end]:
            display = label
            if url == self.current_url:
                display = f"{label} (選択中)"
            options.append(discord.SelectOption(label=display, value=url, default=(url == self.current_url)))

        self.select = discord.ui.Select(
            placeholder="ラインナップの季節を選択",
            options=options,
            min_values=1,
            max_values=1,
        )
        self.select.callback = self.callback
        self.add_item(self.select)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        url = self.select.values[0]
        items = await fetch_lineup_from_url(url)
        if not items:
            await interaction.message.edit(embed=make_lineup_fetch_failed_embed(), view=self)
            return

        selected_label = next((label for label, link in self.links if link == url), "ラインナップ")
        embed = make_lineup_embed(selected_label, items, url)
        self.current_url = url
        self._build_select()
        await interaction.message.edit(embed=embed, view=self)
