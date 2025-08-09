import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional
from src.core.database import Database

dao = Database()


class SlashHelpCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="ttp-help", description="Show all available commands")
    async def help(self, interaction: discord.Interaction):
        """Show all available slash commands"""
        em = discord.Embed(
            title="🤖 TTP Bot Commands",
            color=discord.Color.blurple(),
        )

        # Check if user is admin
        is_admin = dao.is_admin(str(interaction.user.id))

        # Define command categories with admin requirements
        categories = {
            "📊 Points Management": {
                "commands": [
                    "ttp-resetpoints",
                    "ttp-resetallpoints",
                    "ttp-setpoints",
                    "ttp-addpoints",
                    "ttp-removepoints",
                    "ttp-setdailylimit",
                ],
                "admin_only": True,
            },
            "⚙️ Configuration": {
                "commands": ["ttp-setconfig", "ttp-viewconfig", "ttp-setbotchannel"],
                "admin_only": True,
            },
            "🏆 Milestones": {
                "commands": [
                    "ttp-listmilestones",
                    "ttp-addmilestone",
                    "ttp-removemilestone",
                    "ttp-setmilestonemessage",
                    "ttp-setmilestonerole",
                    "ttp-setmilestonereward",
                ],
                "admin_only": True,
            },
            "👥 Role Management": {"commands": ["ttp-assignroles"], "admin_only": True},
            "🎁 Rewards": {
                "commands": [
                    "ttp-markrewarded",
                    "ttp-pendingrewards",
                    "ttp-markrewardedbatch",
                ],
                "admin_only": True,
            },
            "📺 Channel Tracking": {
                "commands": [
                    "ttp-trackchannel",
                    "ttp-untrackchannel",
                    "ttp-listtrackedchannels",
                ],
                "admin_only": True,
            },
            "🛡️ Admin Management": {
                "commands": ["ttp-listadmins", "ttp-addadmin", "ttp-removeadmin"],
                "admin_only": True,
            },
            "🚫 Leaderboard Exclusion": {
                "commands": [
                    "ttp-excludeuser",
                    "ttp-includeuser",
                    "ttp-excludedusers",
                ],
                "admin_only": True,
            },
            "🏅 Leaderboard": {"commands": ["ttp-leaderboard"], "admin_only": False},
            "📊 Dashboard": {
                "commands": ["ttp-dashboard", "ttp-mystats"],
                "admin_only": False,
            },
            "📁 Database": {"commands": ["ttp-exportdb"], "admin_only": True},
            "🎯 Campaign Management": {
                "commands": [
                    "ttp-createcampaign",
                    "ttp-listcampaigns",
                    "ttp-deletecampaign",
                ],
                "admin_only": True,
            },
        }

        # Get all slash commands
        all_commands = {
            cmd.name: cmd.description for cmd in self.bot.tree.walk_commands()
        }

        # Build categorized help (only show commands user can use)
        for category, category_info in categories.items():
            # Skip admin-only categories for non-admins
            if category_info["admin_only"] and not is_admin:
                continue

            category_commands = []
            for cmd_name in category_info["commands"]:
                if cmd_name in all_commands:
                    description = all_commands[cmd_name] or cmd_name
                    category_commands.append(f"`/{cmd_name}` - {description}")

            if category_commands:
                # Join commands with newlines, limit to avoid field length issues
                commands_text = "\n".join(category_commands)
                if len(commands_text) > 1024:  # Discord field limit
                    commands_text = commands_text[:1021] + "..."

                em.add_field(name=category, value=commands_text, inline=False)

        await interaction.response.send_message(embed=em, ephemeral=True)


async def setup(bot):
    await bot.add_cog(SlashHelpCommands(bot))
