import discord

class SimplePaginator(discord.ui.View):
    def __init__(self, pages):
        super().__init__(timeout=120)
        self.pages, self.index = pages, 0
    async def update(self, interaction):
        await interaction.response.edit_message(embed=self.pages[self.index], view=self)
    @discord.ui.button(label="Previous", style=discord.ButtonStyle.secondary)
    async def prev(self, interaction, button):
        self.index = (self.index - 1) % len(self.pages)
        await self.update(interaction)
    @discord.ui.button(label="Next", style=discord.ButtonStyle.secondary)
    async def next(self, interaction, button):
        self.index = (self.index + 1) % len(self.pages)
        await self.update(interaction)
