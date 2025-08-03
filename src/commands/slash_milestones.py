import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional
from src.core.database import Database

dao = Database()


class SlashMilestoneCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="ttp-listmilestones", description="Show all milestones with details"
    )
    async def listmilestones(self, interaction: discord.Interaction):
        """Show all milestones with details"""
        # Check if user is admin
        if not dao.is_admin(str(interaction.user.id)):
            await interaction.response.send_message(
                "❌ You don't have permission to use this command.", ephemeral=True
            )
            return

        milestones = dao.get_active_milestones()

        if not milestones:
            await interaction.response.send_message(
                "📋 No milestones found.", ephemeral=True
            )
            return

        embed = discord.Embed(
            title="🏆 Milestones",
            description="All active milestones with details",
            color=discord.Color.gold(),
        )

        for value, message, role_name, is_level_based, reward in milestones:
            role_info = f"Role: {role_name}" if role_name else "No role"
            level_info = "Level-based" if is_level_based else "Point-based"
            reward_info = f"Reward: {reward}" if reward else "No reward"

            embed.add_field(
                name=f"🟢 {value:,} Points",
                value=f"**{role_info}**\n**Type:** {level_info}\n**{reward_info}**\n**Message:** {message}",
                inline=False,
            )

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="ttp-addmilestone", description="Create new milestone")
    @app_commands.describe(
        value="The point value for the milestone",
        message="The message to display when milestone is reached",
        reward="The reward description for this milestone",
    )
    async def addmilestone(
        self,
        interaction: discord.Interaction,
        value: int,
        message: str,
        reward: Optional[str] = None,
    ):
        """Create new milestone"""
        # Check if user is admin
        if not dao.is_admin(str(interaction.user.id)):
            await interaction.response.send_message(
                "❌ You don't have permission to use this command.", ephemeral=True
            )
            return

        if value < 1:
            await interaction.response.send_message(
                "❌ Milestone value must be at least 1.", ephemeral=True
            )
            return

        dao.add_milestone(value, message, reward=reward)
        await interaction.response.send_message(
            f"✅ Milestone created: {value:,} points", ephemeral=True
        )

    @app_commands.command(
        name="ttp-removemilestone", description="Remove (deactivate) a milestone"
    )
    @app_commands.describe(value="The point value of the milestone to remove")
    async def removemilestone(self, interaction: discord.Interaction, value: int):
        """Remove (deactivate) a milestone"""
        # Check if user is admin
        if not dao.is_admin(str(interaction.user.id)):
            await interaction.response.send_message(
                "❌ You don't have permission to use this command.", ephemeral=True
            )
            return

        # Check if milestone exists first
        milestone_details = dao.get_milestone_details(value)
        if not milestone_details:
            await interaction.response.send_message(
                f"❌ Milestone {value:,} does not exist.", ephemeral=True
            )
            return

        if dao.update_milestone_status(value, "inactive"):
            await interaction.response.send_message(
                f"✅ Milestone {value:,} has been removed (set to inactive).",
                ephemeral=True,
            )
        else:
            await interaction.response.send_message(
                f"❌ Failed to remove milestone {value:,}.", ephemeral=True
            )

    @app_commands.command(
        name="ttp-setmilestonemessage", description="Set/update milestone message"
    )
    @app_commands.describe(
        value="The point value of the milestone",
        message="The new message for the milestone",
    )
    async def setmilestonemessage(
        self, interaction: discord.Interaction, value: int, message: str
    ):
        """Set/update milestone message"""
        # Check if user is admin
        if not dao.is_admin(str(interaction.user.id)):
            await interaction.response.send_message(
                "❌ You don't have permission to use this command.", ephemeral=True
            )
            return

        # Check if milestone exists first
        milestone_details = dao.get_milestone_details(value)
        if not milestone_details:
            await interaction.response.send_message(
                f"❌ Milestone {value:,} does not exist.", ephemeral=True
            )
            return

        if dao.update_milestone_message(value, message):
            await interaction.response.send_message(
                f"✅ Message updated for milestone {value:,}", ephemeral=True
            )
        else:
            await interaction.response.send_message(
                f"❌ Failed to update message for milestone {value:,}.", ephemeral=True
            )

    @app_commands.command(
        name="ttp-setmilestonerole", description="Set role for milestone"
    )
    @app_commands.describe(
        value="The milestone value", role_name="The role name to assign"
    )
    async def setmilestonerole(
        self, interaction: discord.Interaction, value: int, *, role_name: str
    ):
        """Set role for milestone"""
        # Check if user is admin
        if not dao.is_admin(str(interaction.user.id)):
            await interaction.response.send_message(
                "❌ You don't have permission to use this command.", ephemeral=True
            )
            return

        # Check if milestone exists
        milestone_details = dao.get_milestone_details(value)
        if not milestone_details:
            await interaction.response.send_message(
                f"❌ Milestone {value:,} does not exist.", ephemeral=True
            )
            return

        # Check if role exists in the guild
        role = discord.utils.get(interaction.guild.roles, name=role_name)
        if not role:
            await interaction.response.send_message(
                f"❌ Role '{role_name}' not found in this server.", ephemeral=True
            )
            return

        # Check if bot has permission to manage this role
        if role >= interaction.guild.me.top_role:
            await interaction.response.send_message(
                f"❌ I don't have permission to manage the '{role_name}' role.",
                ephemeral=True,
            )
            return

        if dao.update_milestone_role(value, role_name):
            await interaction.response.send_message(
                f"✅ Role '{role_name}' set for milestone {value:,} points",
                ephemeral=True,
            )
        else:
            await interaction.response.send_message(
                f"❌ Failed to set role for milestone {value:,} points", ephemeral=True
            )

    @app_commands.command(
        name="ttp-setmilestonereward", description="Set reward for milestone"
    )
    @app_commands.describe(value="The milestone value", reward="The reward description")
    async def setmilestonereward(
        self, interaction: discord.Interaction, value: int, *, reward: str
    ):
        """Set reward for milestone"""
        # Check if user is admin
        if not dao.is_admin(str(interaction.user.id)):
            await interaction.response.send_message(
                "❌ You don't have permission to use this command.", ephemeral=True
            )
            return

        # Check if milestone exists
        milestone_details = dao.get_milestone_details(value)
        if not milestone_details:
            await interaction.response.send_message(
                f"❌ Milestone {value:,} does not exist.", ephemeral=True
            )
            return

        # Update the milestone with the new reward
        if dao.update_milestone_reward(value, reward):
            await interaction.response.send_message(
                f"✅ Reward set for milestone {value:,} points", ephemeral=True
            )
        else:
            await interaction.response.send_message(
                f"❌ Failed to set reward for milestone {value:,} points",
                ephemeral=True,
            )


async def setup(bot):
    await bot.add_cog(SlashMilestoneCommands(bot))
