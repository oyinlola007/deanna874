import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional
from src.core.database import Database

dao = Database()


class SlashConfigCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="ttp-setconfig", description="Update config values")
    @app_commands.describe(
        key="The config key to update", value="The new value for the config key"
    )
    async def setconfig(self, interaction: discord.Interaction, key: str, value: str):
        """Update config values"""
        # Check if user is admin
        if not dao.is_admin(str(interaction.user.id)):
            await interaction.response.send_message(
                "❌ You don't have permission to use this command.", ephemeral=True
            )
            return

        dao.set_config(key, value)
        await interaction.response.send_message(
            f"✅ Config '{key}' set to '{value}'", ephemeral=True
        )

    @app_commands.command(
        name="ttp-viewconfig", description="Show current config values"
    )
    async def viewconfig(self, interaction: discord.Interaction):
        """Show current config values"""
        # Check if user is admin
        if not dao.is_admin(str(interaction.user.id)):
            await interaction.response.send_message(
                "❌ You don't have permission to use this command.", ephemeral=True
            )
            return

        configs = dao.get_all_configs()

        embed = discord.Embed(
            title="⚙️ Bot Configuration",
            description="Current configuration values",
            color=discord.Color.blue(),
        )

        for key, value in configs:
            embed.add_field(name=key, value=str(value), inline=True)

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(
        name="ttp-setbotchannel", description="Set the channel for general bot commands"
    )
    @app_commands.describe(
        channel="The channel where general commands (dashboard, leaderboard, etc.) can be used"
    )
    async def setbotchannel(
        self, interaction: discord.Interaction, channel: discord.TextChannel
    ):
        """Set the channel for general bot commands"""
        # Check if user is admin
        if not dao.is_admin(str(interaction.user.id)):
            await interaction.response.send_message(
                "❌ You don't have permission to use this command.", ephemeral=True
            )
            return

        # Set the bot channel config
        dao.set_config("bot_channel_id", str(channel.id))

        await interaction.response.send_message(
            f"✅ Bot channel set to {channel.mention}. General commands (dashboard, leaderboard, mystats) can now only be used in this channel.",
            ephemeral=True,
        )


async def setup(bot):
    await bot.add_cog(SlashConfigCommands(bot))
