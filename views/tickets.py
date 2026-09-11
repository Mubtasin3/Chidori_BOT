import discord

class TicketPanel(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    @discord.ui.select(
        placeholder="Choose a ticket category...",
        custom_id="ticket:category",
        min_values=1, max_values=1,
        options=[
            discord.SelectOption(label="Purchase", emoji="🛒", value="Purchase"),
            discord.SelectOption(label="Payment", emoji="💳", value="Payment"),
            discord.SelectOption(label="Gaming", emoji="🎮", value="Gaming"),
            discord.SelectOption(label="Technical", emoji="🔧", value="Technical"),
            discord.SelectOption(label="General", emoji="💬", value="General"),
        ])
    async def category(self, interaction, select):
        cog = interaction.client.get_cog("Tickets")
        if cog:
            await cog.create_ticket(interaction, select.values[0])
