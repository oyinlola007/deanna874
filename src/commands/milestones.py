from discord.ext import commands
import discord
from src.core.database import Database

dao = Database()


class MilestonesCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.check(lambda ctx: dao.is_admin(str(ctx.author.id)))
    async def listmilestones(self, ctx):
        """List all active milestones with detailed information."""
        milestones = dao.get_active_milestones()
        if not milestones:
            await ctx.send("No milestones configured.")
            return

        embed = discord.Embed(
            title="📈 Active Milestones",
            description="All active milestones with their details",
            color=discord.Color.blue(),
        )

        for value, message, role_name, is_level_based in milestones:
            # Truncate message if too long
            msg = (message or "No message set").strip()
            if len(msg) > 100:
                msg = msg[:97] + "..."

            # Create field name with milestone value
            field_name = f"🎯 {value:,} Points"

            # Create field value with role and message
            role_display = f"**Role:** {role_name}" if role_name else "**Role:** None"
            level_based = (
                "**Level Based:** Yes" if is_level_based else "**Level Based:** No"
            )

            field_value = f"{role_display}\n{level_based}\n**Message:** {msg}"

            embed.add_field(name=field_name, value=field_value, inline=False)

        await ctx.send(embed=embed)

    @commands.command()
    @commands.check(lambda ctx: dao.is_admin(str(ctx.author.id)))
    async def markrewarded(self, ctx, code: str = None):
        if not code:
            await ctx.send("Usage: !markrewarded <reward_code>")
            return

        success = dao.mark_reward_given(code.upper())
        if success:
            await ctx.send(f"✅ Marked reward `{code}` as sent.")
        else:
            await ctx.send(
                f"❌ Could not mark reward `{code}`. It may not exist or was already marked."
            )

    @commands.command()
    @commands.check(lambda ctx: dao.is_admin(str(ctx.author.id)))
    async def pendingrewards(self, ctx):
        entries = dao.get_unrewarded_milestones()
        if not entries:
            await ctx.send("🎉 All milestone rewards have been sent!")
            return
        msg = "**🎯 Pending Rewards:**\n"
        for user_id, milestone, code in entries:
            msg += f"<@{user_id}> — Milestone: {milestone}, Code: `{code}`\n"
        await ctx.send(msg)

    @commands.command()
    @commands.check(lambda ctx: dao.is_admin(str(ctx.author.id)))
    async def setmilestonemessage(self, ctx, value: str = None, *, message: str = None):
        if not value or not value.isdigit() or not message:
            await ctx.send(
                "Usage: `!setmilestonemessage <milestone_value> <custom_message>`"
            )
            return

        updated = dao.update_milestone_message(int(value), message)
        if updated:
            await ctx.send(f"✅ Milestone `{value}` message updated successfully.")
        else:
            await ctx.send(f"❌ No milestone found with value `{value}`.")

    @commands.command()
    @commands.check(lambda ctx: dao.is_admin(str(ctx.author.id)))
    async def addmilestone(self, ctx, value: str = None, *, message: str = None):
        if not value or not value.isdigit():
            await ctx.send("Usage: !addmilestone <value> <milestone achieved message>")
            return

        value = int(value)
        if dao.add_milestone(value, message):
            await ctx.send(f"✅ Milestone `{value}` added successfully.")
        else:
            await ctx.send(f"❌ Milestone `{value}` already exists.")

    @commands.command()
    @commands.check(lambda ctx: dao.is_admin(str(ctx.author.id)))
    async def setmilestonerole(self, ctx, value: str = None, *, role_name: str = None):
        """Set a role for a milestone. Usage: !setmilestonerole <milestone_value> <role_name>"""
        if not value or not value.isdigit() or not role_name:
            await ctx.send("Usage: !setmilestonerole <milestone_value> <role_name>")
            return

        value = int(value)

        # Check if milestone exists
        milestone_details = dao.get_milestone_details(value)
        if not milestone_details:
            await ctx.send(f"❌ Milestone `{value}` not found.")
            return

        # Check if role exists in the server
        role = discord.utils.get(ctx.guild.roles, name=role_name)
        if not role:
            await ctx.send(f"❌ Role `{role_name}` not found in this server.")
            return

        # Check if bot has permission to manage this role
        if not ctx.guild.me.guild_permissions.manage_roles:
            await ctx.send("❌ I don't have permission to manage roles in this server.")
            return

        if role.position >= ctx.guild.me.top_role.position:
            await ctx.send(
                f"❌ I cannot manage role `{role_name}` - it's higher than my highest role."
            )
            return

        # Update the milestone with role information
        if dao.update_milestone_role(value, role_name):
            await ctx.send(f"✅ Role `{role_name}` set for milestone `{value}`.")
        else:
            await ctx.send(f"❌ Failed to update milestone `{value}` with role.")


async def setup(bot):
    await bot.add_cog(MilestonesCommands(bot))
