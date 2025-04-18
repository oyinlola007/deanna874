from discord.ext import commands
from cogs.dao import Database

dao = Database()


class MilestonesCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.check(lambda ctx: dao.is_admin(str(ctx.author.id)))
    async def listmilestones(self, ctx):
        milestones = dao.get_active_milestones()
        if not milestones:
            await ctx.send("No milestones configured.")
            return

        lines = [
            "**📈 Active Milestones**",
            "```",
            f"{'Milestone':<10} | Message",
            f"{'-'*10}-+-{'-'*50}",
        ]
        for value, message in milestones:
            msg = (message or "No message set").strip().replace("\n", " ")
            if len(msg) > 50:
                msg = msg[:47] + "..."
            lines.append(f"{value:<10} | {msg}")
        lines.append("```")

        await ctx.send("\n".join(lines))

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


async def setup(bot):
    await bot.add_cog(MilestonesCommands(bot))
