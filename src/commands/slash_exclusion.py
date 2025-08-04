import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional
from src.core.database import Database

dao = Database()


class SlashExclusionCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="ttp-excludeuser", description="Exclude a user from leaderboard"
    )
    @app_commands.describe(user="The user to exclude from leaderboard")
    async def excludeuser(self, interaction: discord.Interaction, user: discord.Member):
        """Exclude a user from leaderboard"""
        # Check if user is admin
        if not dao.is_admin(str(interaction.user.id)):
            await interaction.response.send_message(
                "❌ You don't have permission to use this command.", ephemeral=True
            )
            return

        user_id = str(user.id)
        if dao.add_excluded_leaderboard_user(user_id):
            await interaction.response.send_message(
                f"✅ Excluded {user.mention} from leaderboard", ephemeral=True
            )
        else:
            await interaction.response.send_message(
                f"❌ {user.mention} is already excluded from leaderboard",
                ephemeral=True,
            )

    @app_commands.command(
        name="ttp-includeuser", description="Include a user back in leaderboard"
    )
    @app_commands.describe(user="The user to include back in leaderboard")
    async def includeuser(self, interaction: discord.Interaction, user: discord.Member):
        """Include a user back in leaderboard"""
        # Check if user is admin
        if not dao.is_admin(str(interaction.user.id)):
            await interaction.response.send_message(
                "❌ You don't have permission to use this command.", ephemeral=True
            )
            return

        user_id = str(user.id)
        if dao.remove_excluded_leaderboard_user(user_id):
            await interaction.response.send_message(
                f"✅ Included {user.mention} back in leaderboard", ephemeral=True
            )
        else:
            await interaction.response.send_message(
                f"❌ {user.mention} is not excluded from leaderboard", ephemeral=True
            )

    @app_commands.command(name="ttp-excludedusers", description="List excluded users")
    async def excludedusers(self, interaction: discord.Interaction):
        """List excluded users"""
        # Check if user is admin
        if not dao.is_admin(str(interaction.user.id)):
            await interaction.response.send_message(
                "❌ You don't have permission to use this command.", ephemeral=True
            )
            return

        excluded_users = dao.get_excluded_leaderboard_users()

        if not excluded_users:
            await interaction.response.send_message(
                "🚫 No users are excluded from leaderboard.", ephemeral=True
            )
            return

        embed = discord.Embed(
            title="🚫 Excluded Users",
            description="Users excluded from leaderboard",
            color=discord.Color.orange(),
        )

        for user_id in excluded_users:
            member = interaction.guild.get_member(int(user_id))
            member_name = member.mention if member else f"User {user_id}"
            embed.add_field(name="Excluded User", value=member_name, inline=True)

        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot):
    await bot.add_cog(SlashExclusionCommands(bot))
