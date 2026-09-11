import discord

class GiveawayView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    @discord.ui.button(label="Enter Giveaway", emoji="🎉", style=discord.ButtonStyle.success, custom_id="giveaway:enter")
    async def enter(self, interaction, button):
        cog = interaction.client.get_cog("Giveaways")
        if cog:
            await cog.enter(interaction)
