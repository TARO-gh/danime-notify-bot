import discord
from bot.utils.storage import clear_watchlist
from bot.utils.embeds import make_clear_done_embed, make_clear_cancel_embed


class ClearView(discord.ui.View):
    """
    全件削除確認用の View
    """
    def __init__(self):
        super().__init__(timeout=60)

    @discord.ui.button(label="削除", style=discord.ButtonStyle.danger)
    async def confirm(self, button: discord.ui.Button, interaction: discord.Interaction):
        await interaction.response.defer()
        # 削除処理
        print("全削除処理を開始します。")
        await interaction.message.delete()
        await clear_watchlist()
        print("全削除処理を正しく終了しました。")
        await interaction.channel.send(embed=make_clear_done_embed(), delete_after=60)
        self.stop()

    @discord.ui.button(label="キャンセル", style=discord.ButtonStyle.secondary)
    async def cancel(self, button: discord.ui.Button, interaction: discord.Interaction):
        await interaction.response.defer()
        await interaction.message.delete()
        await interaction.channel.send(embed=make_clear_cancel_embed(), delete_after=60)
        self.stop()
