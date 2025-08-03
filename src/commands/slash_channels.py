import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional
from src.core.database import Database

dao = Database()


class SlashChannelCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="ttp-trackchannel", description="Start tracking a channel"
    )
    @app_commands.describe(channel="The channel to start tracking")
    async def trackchannel(
        self, interaction: discord.Interaction, channel: discord.TextChannel
    ):
        """Start tracking a channel"""
        # Check if user is admin
        if not dao.is_admin(str(interaction.user.id)):
            await interaction.response.send_message(
                "❌ You don't have permission to use this command.", ephemeral=True
            )
            return

        channel_id = str(channel.id)

        # Check if channel is already being tracked
        if dao.is_tracked_channel(channel_id):
            await interaction.response.send_message(
                f"❌ {channel.mention} is already being tracked", ephemeral=True
            )
            return

        dao.track_channel(channel_id)
        await interaction.response.send_message(
            f"✅ Started tracking {channel.mention}", ephemeral=True
        )

    @app_commands.command(
        name="ttp-untrackchannel", description="Stop tracking a channel"
    )
    @app_commands.describe(channel="The channel to stop tracking")
    async def untrackchannel(
        self, interaction: discord.Interaction, channel: discord.TextChannel
    ):
        """Stop tracking a channel"""
        # Check if user is admin
        if not dao.is_admin(str(interaction.user.id)):
            await interaction.response.send_message(
                "❌ You don't have permission to use this command.", ephemeral=True
            )
            return

        channel_id = str(channel.id)

        # Check if channel is actually being tracked
        if not dao.is_tracked_channel(channel_id):
            await interaction.response.send_message(
                f"❌ {channel.mention} is not being tracked", ephemeral=True
            )
            return

        dao.untrack_channel(channel_id)
        await interaction.response.send_message(
            f"✅ Stopped tracking {channel.mention}", ephemeral=True
        )

    @app_commands.command(
        name="ttp-listtrackedchannels", description="View tracked channels"
    )
    async def listtrackedchannels(self, interaction: discord.Interaction):
        """View tracked channels"""
        # Check if user is admin
        if not dao.is_admin(str(interaction.user.id)):
            await interaction.response.send_message(
                "❌ You don't have permission to use this command.", ephemeral=True
            )
            return

        tracked_channels = dao.get_tracked_channels()

        if not tracked_channels:
            await interaction.response.send_message(
                "📋 No channels are currently being tracked.", ephemeral=True
            )
            return

        embed = discord.Embed(
            title="📺 Tracked Channels",
            description=f"**{len(tracked_channels)}** channels currently being tracked for points",
            color=discord.Color.green(),
        )

        # Group all channels into a single field to avoid Discord's 25 field limit
        channel_list = []
        for channel_id in tracked_channels:
            channel = interaction.guild.get_channel(int(channel_id))
            channel_name = channel.mention if channel else f"<#{channel_id}> (Unknown)"
            channel_list.append(channel_name)

        # Split into chunks if too long for a single field
        if len(channel_list) <= 25:
            embed.add_field(
                name="Tracked Channels", value="\n".join(channel_list), inline=False
            )
        else:
            # Split into multiple fields if more than 25 channels
            chunks = [channel_list[i : i + 25] for i in range(0, len(channel_list), 25)]
            for i, chunk in enumerate(chunks, 1):
                embed.add_field(
                    name=f"Tracked Channels (Part {i})",
                    value="\n".join(chunk),
                    inline=False,
                )

        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot):
    await bot.add_cog(SlashChannelCommands(bot))
