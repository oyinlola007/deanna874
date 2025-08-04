import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional
from src.core.database import Database

dao = Database()


class SlashCampaignCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="ttp-createcampaign", description="Create a new campaign"
    )
    @app_commands.describe(
        channel="The channel for the campaign",
        name="Name of the campaign",
        multiplier="Point multiplier (e.g., 2.0 for double points)",
        start_date="Start date (YYYY-MM-DD format)",
        end_date="End date (YYYY-MM-DD format)",
    )
    async def createcampaign(
        self,
        interaction: discord.Interaction,
        channel: discord.TextChannel,
        name: str,
        multiplier: float,
        start_date: str,
        end_date: str,
    ):
        """Create a new campaign"""
        # Check if user is admin
        if not dao.is_admin(str(interaction.user.id)):
            await interaction.response.send_message(
                "❌ You don't have permission to use this command.", ephemeral=True
            )
            return

        try:
            # Validate multiplier
            if multiplier <= 0:
                await interaction.response.send_message(
                    "❌ Multiplier must be greater than 0", ephemeral=True
                )
                return

            # Validate date format
            from datetime import datetime

            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")

            if start_dt >= end_dt:
                await interaction.response.send_message(
                    "❌ End date must be after start date", ephemeral=True
                )
                return

            channel_id = str(channel.id)
            dao.add_campaign_channel(channel_id, name, multiplier, start_date, end_date)
            await interaction.response.send_message(
                f"✅ Campaign '{name}' created for {channel.mention} with {multiplier}x multiplier",
                ephemeral=True,
            )
        except ValueError:
            await interaction.response.send_message(
                "❌ Invalid date format. Use YYYY-MM-DD", ephemeral=True
            )
        except Exception as e:
            await interaction.response.send_message(
                f"❌ Error creating campaign: {e}", ephemeral=True
            )

    @app_commands.command(name="ttp-listcampaigns", description="Show all campaigns")
    async def listcampaigns(self, interaction: discord.Interaction):
        """Show all campaigns"""
        # Check if user is admin
        if not dao.is_admin(str(interaction.user.id)):
            await interaction.response.send_message(
                "❌ You don't have permission to use this command.", ephemeral=True
            )
            return

        campaigns = dao.get_all_campaigns()

        if not campaigns:
            await interaction.response.send_message(
                "📋 No campaigns found.", ephemeral=True
            )
            return

        embed = discord.Embed(
            title="🎯 Campaigns",
            description=f"**{len(campaigns)}** campaigns found",
            color=discord.Color.blue(),
        )

        for channel_id, name, multiplier, start_date, end_date, status in campaigns:
            channel = interaction.guild.get_channel(int(channel_id))
            channel_name = channel.mention if channel else f"<#{channel_id}> (Unknown)"

            # Determine status emoji
            status_emoji = "🟢" if status == "active" else "🔴"

            embed.add_field(
                name=f"{status_emoji} {name}",
                value=f"**Channel:** {channel_name}\n"
                f"**Multiplier:** {multiplier}x\n"
                f"**Period:** {start_date} to {end_date}\n"
                f"**Status:** {status.title()}",
                inline=False,
            )

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="ttp-deletecampaign", description="Delete a campaign")
    @app_commands.describe(channel="The channel of the campaign to delete")
    async def deletecampaign(
        self, interaction: discord.Interaction, channel: discord.TextChannel
    ):
        """Delete a campaign"""
        # Check if user is admin
        if not dao.is_admin(str(interaction.user.id)):
            await interaction.response.send_message(
                "❌ You don't have permission to use this command.", ephemeral=True
            )
            return

        try:
            channel_id = str(channel.id)

            # Delete the campaign and check if it was successful
            if dao.delete_campaign_channel(channel_id):
                await interaction.response.send_message(
                    f"✅ Campaign deleted for {channel.mention}", ephemeral=True
                )
            else:
                await interaction.response.send_message(
                    f"❌ No campaign found for {channel.mention}", ephemeral=True
                )
        except Exception as e:
            await interaction.response.send_message(
                f"❌ Error deleting campaign: {e}", ephemeral=True
            )


async def setup(bot):
    await bot.add_cog(SlashCampaignCommands(bot))
