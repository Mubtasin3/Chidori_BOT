import discord


class MusicControls(discord.ui.View):
    """Persistent controls shared by music messages."""

    def __init__(self):
        super().__init__(timeout=None)

    async def dispatch(self, interaction: discord.Interaction, action: str):
        cog = interaction.client.get_cog("Music")
        if not cog:
            return await interaction.response.send_message(
                "❌ Music system is not loaded.", ephemeral=True
            )
        await cog.control(interaction, action)

    @discord.ui.button(
        label="Previous", emoji="⏮️", style=discord.ButtonStyle.secondary,
        custom_id="music:previous"
    )
    async def previous(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.dispatch(interaction, "previous")

    @discord.ui.button(
        label="Pause", emoji="⏸️", style=discord.ButtonStyle.secondary,
        custom_id="music:pause"
    )
    async def pause(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.dispatch(interaction, "pause")

    @discord.ui.button(
        label="Resume", emoji="▶️", style=discord.ButtonStyle.success,
        custom_id="music:resume"
    )
    async def resume(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.dispatch(interaction, "resume")

    @discord.ui.button(
        label="Skip", emoji="⏭️", style=discord.ButtonStyle.primary,
        custom_id="music:skip"
    )
    async def skip(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.dispatch(interaction, "skip")

    @discord.ui.button(
        label="Stop", emoji="⏹️", style=discord.ButtonStyle.danger,
        custom_id="music:stop"
    )
    async def stop(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.dispatch(interaction, "stop")

    @discord.ui.button(
        label="Vol -", emoji="🔉", style=discord.ButtonStyle.secondary,
        custom_id="music:vol_down", row=1
    )
    async def vol_down(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.dispatch(interaction, "vol_down")

    @discord.ui.button(
        label="Vol +", emoji="🔊", style=discord.ButtonStyle.secondary,
        custom_id="music:vol_up", row=1
    )
    async def vol_up(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.dispatch(interaction, "vol_up")

    @discord.ui.button(
        label="Shuffle", emoji="🔀", style=discord.ButtonStyle.secondary,
        custom_id="music:shuffle", row=1
    )
    async def shuffle(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.dispatch(interaction, "shuffle")

    @discord.ui.button(
        label="Loop", emoji="🔁", style=discord.ButtonStyle.secondary,
        custom_id="music:loop", row=1
    )
    async def loop(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.dispatch(interaction, "loop")

    @discord.ui.button(
        label="Clear", emoji="🧹", style=discord.ButtonStyle.secondary,
        custom_id="music:clear", row=1
    )
    async def clear(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.dispatch(interaction, "clear")
