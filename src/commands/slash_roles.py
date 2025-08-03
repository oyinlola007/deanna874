import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional
from src.core.database import Database

dao = Database()


class SlashRoleCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="ttp-assignroles", description="Assign roles to all members"
    )
    async def assignroles(self, interaction: discord.Interaction):
        """Assign roles to all members based on their current levels"""
        # Check if user is admin
        if not dao.is_admin(str(interaction.user.id)):
            await interaction.response.send_message(
                "❌ You don't have permission to use this command.", ephemeral=True
            )
            return

        await interaction.response.send_message(
            "🔄 Starting bulk role assignment... This may take a while.", ephemeral=True
        )

        try:
            if not hasattr(self.bot, "role_manager"):
                await interaction.followup.send(
                    "❌ Role manager not initialized.", ephemeral=True
                )
                return

            summary = await self.bot.role_manager.assign_roles_for_all_members(
                interaction.guild
            )

            embed = discord.Embed(
                title="📊 Role Assignment Summary", color=discord.Color.green()
            )
            embed.add_field(
                name="Members Checked", value=summary["total_checked"], inline=True
            )
            embed.add_field(
                name="Roles Added", value=summary["roles_added"], inline=True
            )
            embed.add_field(
                name="Roles Removed", value=summary["roles_removed"], inline=True
            )

            if summary["errors"] > 0:
                embed.add_field(name="Errors", value=summary["errors"], inline=True)
                embed.color = discord.Color.orange()

            await interaction.followup.send(embed=embed, ephemeral=True)

        except Exception as e:
            await interaction.followup.send(
                f"❌ Error during role assignment: {str(e)}", ephemeral=True
            )


async def setup(bot):
    await bot.add_cog(SlashRoleCommands(bot))
