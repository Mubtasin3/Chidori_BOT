import discord

class MusicControls(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    async def dispatch(self, interaction, action):
        cog = interaction.client.get_cog("Music")
        if cog:
            await cog.control(interaction, action)
    @discord.ui.button(label="Previous", emoji="⏮️", style=discord.ButtonStyle.secondary, custom_id="music:previous")
    async def previous(self, i,b): await self.dispatch(i,"previous")
    @discord.ui.button(label="Pause", emoji="⏸️", style=discord.ButtonStyle.secondary, custom_id="music:pause")
    async def pause(self, i,b): await self.dispatch(i,"pause")
    @discord.ui.button(label="Resume", emoji="▶️", style=discord.ButtonStyle.success, custom_id="music:resume")
    async def resume(self, i,b): await self.dispatch(i,"resume")
    @discord.ui.button(label="Skip", emoji="⏭️", style="primary", custom_id="music:skip")
    async def skip(self, i,b): await self.dispatch(i,"skip")
    @discord.ui.button(label="Shuffle", emoji="🔀", style=discord.ButtonStyle.secondary, custom_id="music:shuffle")
    async def shuffle(self, i,b): await self.dispatch(i,"shuffle")
    @discord.ui.button(label="Loop", emoji="🔁", style=discord.ButtonStyle.secondary, custom_id="music:loop")
    async def loop(self, i,b): await self.dispatch(i,"loop")
    @discord.ui.button(label="Stop", emoji="⏹️", style=discord.ButtonStyle.danger, custom_id="music:stop")
    async def stop(self, i,b): await self.dispatch(i,"stop")
