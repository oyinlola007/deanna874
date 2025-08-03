import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional
from src.core.database import Database

dao = Database()


class SlashPointsCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="ttp-resetpoints", description="Reset a user's points to 0"
    )
    @app_commands.describe(user="The user whose points should be reset")
    async def resetpoints(self, interaction: discord.Interaction, user: discord.Member):
        """Reset a user's points to 0"""
        # Check if user is admin
        if not dao.is_admin(str(interaction.user.id)):
            await interaction.response.send_message(
                "❌ You don't have permission to use this command.", ephemeral=True
            )
            return

        user_id = str(user.id)

        if not dao.user_exists(user_id):
            await interaction.response.send_message(
                f"❌ User {user.display_name} does not exist in the database.",
                ephemeral=True,
            )
            return

        dao.reset_user_points(user_id)
        await interaction.response.send_message(
            f"✅ Points reset for {user.mention}", ephemeral=True
        )

    @app_commands.command(
        name="ttp-resetallpoints", description="Reset all user points to 0"
    )
    async def resetallpoints(self, interaction: discord.Interaction):
        """Reset all user points to 0"""
        # Check if user is admin
        if not dao.is_admin(str(interaction.user.id)):
            await interaction.response.send_message(
                "❌ You don't have permission to use this command.", ephemeral=True
            )
            return

        dao.reset_all_points()
        await interaction.response.send_message(
            "✅ All user points have been reset.", ephemeral=True
        )

    @app_commands.command(name="ttp-setpoints", description="Set a user's point total")
    @app_commands.describe(
        user="The user whose points should be set",
        amount="The amount of points to set (1-1,000,000,000)",
    )
    async def setpoints(
        self, interaction: discord.Interaction, user: discord.Member, amount: int
    ):
        """Set a user's point total"""
        # Check if user is admin
        if not dao.is_admin(str(interaction.user.id)):
            await interaction.response.send_message(
                "❌ You don't have permission to use this command.", ephemeral=True
            )
            return

        user_id = str(user.id)

        if not dao.user_exists(user_id):
            await interaction.response.send_message(
                f"❌ User {user.display_name} does not exist in the database.",
                ephemeral=True,
            )
            return

        if amount < 1 or amount > 1_000_000_000:
            await interaction.response.send_message(
                "❌ Amount must be between 1 and 1,000,000,000.", ephemeral=True
            )
            return

        dao.set_user_points(user_id, amount)

        # Update user's level and check for role changes
        dao.update_user_level(user_id, amount)

        # Check for role assignment/downgrading
        if hasattr(self.bot, "role_manager"):
            await self.bot.role_manager.check_and_assign_roles(
                user_id, interaction.guild
            )

        # Update voice channel display
        if hasattr(self.bot, "voice_channel_display"):
            await self.bot.voice_channel_display.update_channel_name(interaction.guild)

        await interaction.response.send_message(
            f"✅ Set points for {user.mention} to {amount:,}.", ephemeral=True
        )

    @app_commands.command(name="ttp-addpoints", description="Add points to a user")
    @app_commands.describe(
        user="The user to add points to",
        amount="The amount of points to add (1-1,000,000,000)",
    )
    async def addpoints(
        self, interaction: discord.Interaction, user: discord.Member, amount: int
    ):
        """Add points to a user"""
        # Check if user is admin
        if not dao.is_admin(str(interaction.user.id)):
            await interaction.response.send_message(
                "❌ You don't have permission to use this command.", ephemeral=True
            )
            return

        user_id = str(user.id)

        if not dao.user_exists(user_id):
            await interaction.response.send_message(
                f"❌ User {user.display_name} does not exist in the database.",
                ephemeral=True,
            )
            return

        if amount < 1 or amount > 1_000_000_000:
            await interaction.response.send_message(
                "❌ Amount must be between 1 and 1,000,000,000.", ephemeral=True
            )
            return

        dao.increment_user_points(user_id, amount)

        # Update user's level and check for role changes
        current_points = dao.get_user_points(user_id)
        dao.update_user_level(user_id, current_points)

        # Check for milestone and role assignment
        if hasattr(self.bot, "role_manager"):
            await self.bot.role_manager.check_and_assign_roles(
                user_id, interaction.guild
            )

        # Update voice channel display
        if hasattr(self.bot, "voice_channel_display"):
            await self.bot.voice_channel_display.update_channel_name(interaction.guild)

        await interaction.response.send_message(
            f"✅ Added {amount:,} points to {user.mention}.", ephemeral=True
        )

    @app_commands.command(
        name="ttp-removepoints", description="Remove points from a user"
    )
    @app_commands.describe(
        user="The user to remove points from",
        amount="The amount of points to remove (1-1,000,000,000)",
    )
    async def removepoints(
        self, interaction: discord.Interaction, user: discord.Member, amount: int
    ):
        """Remove points from a user"""
        # Check if user is admin
        if not dao.is_admin(str(interaction.user.id)):
            await interaction.response.send_message(
                "❌ You don't have permission to use this command.", ephemeral=True
            )
            return

        user_id = str(user.id)

        if not dao.user_exists(user_id):
            await interaction.response.send_message(
                f"❌ User {user.display_name} does not exist in the database.",
                ephemeral=True,
            )
            return

        if amount < 1 or amount > 1_000_000_000:
            await interaction.response.send_message(
                "❌ Amount must be between 1 and 1,000,000,000.", ephemeral=True
            )
            return

        dao.increment_user_points(user_id, -amount)

        # Update user's level and check for role changes
        current_points = dao.get_user_points(user_id)
        dao.update_user_level(user_id, current_points)

        # Check for role assignment/downgrading
        if hasattr(self.bot, "role_manager"):
            await self.bot.role_manager.check_and_assign_roles(
                user_id, interaction.guild
            )

        # Update voice channel display
        if hasattr(self.bot, "voice_channel_display"):
            await self.bot.voice_channel_display.update_channel_name(interaction.guild)

        await interaction.response.send_message(
            f"✅ Removed {amount:,} points from {user.mention}.", ephemeral=True
        )

    @app_commands.command(
        name="ttp-setdailylimit", description="Set daily points limit"
    )
    @app_commands.describe(amount="The daily points limit to set")
    async def setdailylimit(self, interaction: discord.Interaction, amount: int):
        """Set the daily points limit for all users"""
        # Check if user is admin
        if not dao.is_admin(str(interaction.user.id)):
            await interaction.response.send_message(
                "❌ You don't have permission to use this command.", ephemeral=True
            )
            return

        if amount < 0:
            await interaction.response.send_message(
                "❌ Daily limit cannot be negative.", ephemeral=True
            )
            return

        dao.set_config("daily_points_limit", str(amount))
        await interaction.response.send_message(
            f"✅ Daily points limit set to {amount:,}", ephemeral=True
        )


async def setup(bot):
    await bot.add_cog(SlashPointsCommands(bot))
