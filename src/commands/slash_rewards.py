import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional
from src.core.database import Database

dao = Database()


class SlashRewardCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="ttp-markrewarded", description="Mark reward as sent")
    @app_commands.describe(reward_code="The reward code to mark as sent")
    async def markrewarded(self, interaction: discord.Interaction, reward_code: str):
        """Mark reward as sent"""
        # Check if user is admin
        if not dao.is_admin(str(interaction.user.id)):
            await interaction.response.send_message(
                "❌ You don't have permission to use this command.", ephemeral=True
            )
            return

        if dao.mark_reward_given(reward_code):
            await interaction.response.send_message(
                f"✅ Reward '{reward_code}' marked as sent.", ephemeral=True
            )
        else:
            await interaction.response.send_message(
                f"❌ Reward '{reward_code}' not found or already marked as sent.",
                ephemeral=True,
            )

    @app_commands.command(
        name="ttp-pendingrewards", description="List users awaiting rewards"
    )
    async def pendingrewards(self, interaction: discord.Interaction):
        """List users awaiting rewards"""
        # Check if user is admin
        if not dao.is_admin(str(interaction.user.id)):
            await interaction.response.send_message(
                "❌ You don't have permission to use this command.", ephemeral=True
            )
            return

        pending = dao.get_pending_rewards()

        if not pending:
            await interaction.response.send_message(
                "📋 No pending rewards found.", ephemeral=True
            )
            return

        embed = discord.Embed(
            title="🎁 Pending Rewards",
            description="Users awaiting rewards",
            color=discord.Color.orange(),
        )

        for user_id, reward_code, milestone_value in pending:
            embed.add_field(
                name=f"User {user_id}",
                value=f"**Reward:** {reward_code}\n**Milestone:** {milestone_value:,} points",
                inline=False,
            )

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(
        name="ttp-markrewardedbatch", description="Mark multiple rewards as sent"
    )
    @app_commands.describe(codes="Space-separated reward codes to mark as sent")
    async def markrewardedbatch(self, interaction: discord.Interaction, codes: str):
        """Mark multiple rewards as sent"""
        # Check if user is admin
        if not dao.is_admin(str(interaction.user.id)):
            await interaction.response.send_message(
                "❌ You don't have permission to use this command.", ephemeral=True
            )
            return

        code_list = [c.strip() for c in codes.split() if c.strip()]
        if not code_list:
            await interaction.response.send_message(
                "No valid codes provided.", ephemeral=True
            )
            return

        success = []
        failed = []
        for code in code_list:
            if dao.mark_reward_given(code):
                success.append(code)
            else:
                failed.append(code)

        msg = ""
        if success:
            msg += f"✅ Marked as rewarded: {', '.join(success)}\n"
        if failed:
            msg += f"❌ Failed (not found or already rewarded): {', '.join(failed)}"

        await interaction.response.send_message(msg, ephemeral=True)


async def setup(bot):
    await bot.add_cog(SlashRewardCommands(bot))
