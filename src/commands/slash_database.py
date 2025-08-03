import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional
from src.core.database import Database

dao = Database()


class SlashDatabaseCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="ttp-exportdb", description="Export the database file")
    async def exportdb(self, interaction: discord.Interaction):
        """Export the database file"""
        # Check if user is admin
        if not dao.is_admin(str(interaction.user.id)):
            await interaction.response.send_message(
                "❌ You don't have permission to use this command.", ephemeral=True
            )
            return

        try:
            import shutil
            import os
            from datetime import datetime

            # Create backup filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"database_export_{timestamp}.db"

            # Copy database file
            shutil.copy2("data/database.db", backup_filename)

            # Send the file
            with open(backup_filename, "rb") as f:
                file = discord.File(f, filename=backup_filename)
                await interaction.response.send_message(
                    f"✅ Database exported successfully!\n📁 Filename: {backup_filename}",
                    file=file,
                    ephemeral=True,
                )

            # Clean up the temporary file
            os.remove(backup_filename)

        except Exception as e:
            await interaction.response.send_message(
                f"❌ Error exporting database: {e}", ephemeral=True
            )


async def setup(bot):
    await bot.add_cog(SlashDatabaseCommands(bot))
