import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional
from src.core.database import Database

dao = Database()


class SlashAdminManagementCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="ttp-listadmins", description="View current admins")
    async def listadmins(self, interaction: discord.Interaction):
        """View current admins"""
        # Check if user is admin
        if not dao.is_admin(str(interaction.user.id)):
            await interaction.response.send_message(
                "❌ You don't have permission to use this command.", ephemeral=True
            )
            return

        admin_ids = dao.get_all_admin_ids()

        if not admin_ids:
            await interaction.response.send_message(
                "🛡️ No admins found.", ephemeral=True
            )
            return

        embed = discord.Embed(
            title="🛡️ Bot Admins",
            description="Users with admin permissions",
            color=discord.Color.red(),
        )

        for admin_id in admin_ids:
            member = interaction.guild.get_member(int(admin_id))
            member_name = member.mention if member else f"User {admin_id}"
            embed.add_field(name="Admin", value=member_name, inline=True)

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="ttp-addadmin", description="Add a new admin")
    @app_commands.describe(user="The user to add as admin")
    async def addadmin(self, interaction: discord.Interaction, user: discord.Member):
        """Add a new admin"""
        # Check if user is admin
        if not dao.is_admin(str(interaction.user.id)):
            await interaction.response.send_message(
                "❌ You don't have permission to use this command.", ephemeral=True
            )
            return

        user_id = str(user.id)

        # Check if user is already an admin
        if dao.is_admin(user_id):
            await interaction.response.send_message(
                f"❌ {user.mention} is already an admin", ephemeral=True
            )
            return

        dao.add_admin(user_id)
        await interaction.response.send_message(
            f"✅ Added {user.mention} as admin", ephemeral=True
        )

    @app_commands.command(name="ttp-removeadmin", description="Remove an admin")
    @app_commands.describe(user="The user to remove as admin")
    async def removeadmin(self, interaction: discord.Interaction, user: discord.Member):
        """Remove an admin"""
        # Check if user is admin
        if not dao.is_admin(str(interaction.user.id)):
            await interaction.response.send_message(
                "❌ You don't have permission to use this command.", ephemeral=True
            )
            return

        user_id = str(user.id)

        # Check if user is actually an admin
        if not dao.is_admin(user_id):
            await interaction.response.send_message(
                f"❌ {user.mention} is not an admin", ephemeral=True
            )
            return

        dao.remove_admin(user_id)
        await interaction.response.send_message(
            f"✅ Removed {user.mention} as admin", ephemeral=True
        )


async def setup(bot):
    await bot.add_cog(SlashAdminManagementCommands(bot))
