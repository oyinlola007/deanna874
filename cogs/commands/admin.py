from discord.ext import commands
from cogs.dao import Database
import discord
import cogs.config as config

dao = Database()


class AdminCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.check(lambda ctx: dao.is_admin(str(ctx.author.id)))
    async def adminhelp(self, ctx):
        help_text = """**🔐 Admin Commands**
```yaml
📊 Points Management
!resetpoints <user_id>                  - Reset a user's points to 0
!resetallpoints                         - Reset all user points
!setpoints <user_id> <amount>           - Set a user's point total
!addpoints <user_id> <amount>           - Add points to a user
!removepoints <user_id> <amount>        - Remove points from a user
!setdailylimit <amount>                 - Set daily points limit (default: 1000)

⚙️ Configuration
!setconfig <key> <value>                - Update config values
!viewconfig                             - Show current config values

🏆 Milestones
!listmilestones                         - Show milestone thresholds
!addmilestone <value> <message>         - Create new milestone
!removemilestone <value>                - Remove (deactivate) a milestone
!setmilestonemessage <value> <message>  - Set/update milestone message
!markrewarded <reward_code>             - Mark reward as sent
!pendingrewards                         - List users awaiting rewards

📡 Channel Tracking
!trackchannel <channel_id>              - Start tracking a channel
!untrackchannel <channel_id>            - Stop tracking a channel
!listtrackedchannels                    - View tracked channels

🛡️ Admin Management
!listadmins                             - View current admins
!addadmin <user_id>                     - Add a new admin
!removeadmin <user_id>                  - Remove an admin

🚫 Leaderboard Exclusion
!excludeuser <user_id>                  - Exclude a user from leaderboard
!includeuser <user_id>                  - Include a user back in leaderboard
!excludedusers                          - List excluded users

🏅 Leaderboard
!leaderboard                            - View top users by points (everyone)

📦 Utilities
!exportdb                               - Export the database file```"""
        await ctx.send(help_text)

    @commands.command()
    @commands.check(lambda ctx: dao.is_admin(str(ctx.author.id)))
    async def setconfig(self, ctx, key: str = None, value: str = None):
        if not key or not value:
            await ctx.send("Usage: !setconfig <key> <value>")
            return
        if dao.update_config(key, value):
            await ctx.send(f"✅ Configuration updated: {key} = {value}")
        else:
            await ctx.send(f"❌ Config key '{key}' does not exist.")

    @commands.command()
    @commands.check(lambda ctx: dao.is_admin(str(ctx.author.id)))
    async def viewconfig(self, ctx):
        configs = dao.get_all_configs()
        if not configs:
            await ctx.send("No config data found.")
            return
        formatted = "\n".join([f"{k}: {v}" for k, v in configs.items()])
        await ctx.send(f"⚙️ **Current Configuration:**\n{formatted}")

    @commands.command()
    @commands.check(lambda ctx: dao.is_admin(str(ctx.author.id)))
    async def listadmins(self, ctx):
        admins = dao.get_all_admin_ids()
        if not admins:
            await ctx.send("No admins registered.")
            return

        lines = [f"<@{admin_id}> — `{admin_id}`" for admin_id in admins]
        await ctx.send("🛡️ **Admins:**\n" + "\n".join(lines))

    @commands.command()
    @commands.check(lambda ctx: dao.is_admin(str(ctx.author.id)))
    async def addadmin(self, ctx, user_id: str = None):
        if not user_id or not user_id.isdigit():
            await ctx.send("Usage: !addadmin <user_id>")
            return
        dao.add_admin(user_id)
        await ctx.send(f"✅ Added admin: {user_id}")

    @commands.command()
    @commands.check(lambda ctx: dao.is_admin(str(ctx.author.id)))
    async def removeadmin(self, ctx, user_id: str = None):
        if not user_id or not user_id.isdigit():
            await ctx.send("Usage: !removeadmin <user_id>")
            return
        dao.remove_admin(user_id)
        await ctx.send(f"🗑️ Removed admin: {user_id}")

    @commands.command()
    @commands.check(lambda ctx: dao.is_admin(str(ctx.author.id)))
    async def exportdb(self, ctx):
        try:
            await ctx.send(
                "📦 Here is the current database file:",
                file=discord.File(config.DATABASE_NAME),
            )
        except Exception as e:
            await ctx.send(f"❌ Failed to export DB: {e}")

    @commands.command()
    @commands.check(lambda ctx: dao.is_admin(str(ctx.author.id)))
    async def excludeuser(self, ctx, user_id: str = None):
        if not user_id or not user_id.isdigit():
            await ctx.send("Usage: !excludeuser <user_id>")
            return
        if dao.add_excluded_leaderboard_user(user_id):
            await ctx.send(f"✅ User {user_id} excluded from leaderboard.")
        else:
            await ctx.send(f"❌ User {user_id} is already excluded.")

    @commands.command()
    @commands.check(lambda ctx: dao.is_admin(str(ctx.author.id)))
    async def includeuser(self, ctx, user_id: str = None):
        if not user_id or not user_id.isdigit():
            await ctx.send("Usage: !includeuser <user_id>")
            return
        if dao.remove_excluded_leaderboard_user(user_id):
            await ctx.send(f"✅ User {user_id} included in leaderboard.")
        else:
            await ctx.send(f"❌ User {user_id} was not excluded.")

    @commands.command()
    @commands.check(lambda ctx: dao.is_admin(str(ctx.author.id)))
    async def excludedusers(self, ctx):
        excluded = dao.get_excluded_leaderboard_users()
        if not excluded:
            await ctx.send("No users are currently excluded from the leaderboard.")
            return
        lines = [f"<@{uid}> — `{uid}`" for uid in excluded]
        await ctx.send("🚫 **Excluded from Leaderboard:**\n" + "\n".join(lines))

    @commands.command()
    async def leaderboard(self, ctx):
        top_users = dao.get_leaderboard()
        if not top_users:
            await ctx.send("No leaderboard data yet.")
            return

        desc = ""
        for i, (user_id, score) in enumerate(top_users, start=1):
            try:
                user = await self.bot.fetch_user(int(user_id))
                username = user.name
            except Exception:
                username = f"Unknown User ({user_id})"
            desc += f"**{i}. {username}** — {score} points\n"

        embed = discord.Embed(title="🏆 Leaderboard", description=desc, color=0x00FF00)
        await ctx.send(embed=embed)

    @commands.command()
    @commands.check(lambda ctx: dao.is_admin(str(ctx.author.id)))
    async def setdailylimit(self, ctx, amount: str = None):
        """Set the daily points limit for all users."""
        if not amount or not amount.isdigit():
            await ctx.send("Usage: !setdailylimit <amount>")
            return

        limit = int(amount)
        if limit < 0:
            await ctx.send("❌ Daily limit cannot be negative.")
            return

        dao.set_config("daily_points_limit", str(limit))
        await ctx.send(f"✅ Daily points limit set to {limit}")

    @commands.command()
    @commands.check(lambda ctx: dao.is_admin(str(ctx.author.id)))
    async def removemilestone(self, ctx, value: str = None):
        """Set a milestone's status to inactive (removes it from active milestones)."""
        if not value or not value.isdigit():
            await ctx.send("Usage: !removemilestone <value>")
            return
        value_int = int(value)
        if dao.update_milestone_status(value_int, "inactive"):
            await ctx.send(
                f"✅ Milestone {value_int} has been removed (set to inactive)."
            )
        else:
            await ctx.send(f"❌ Milestone {value_int} not found.")


async def setup(bot):
    await bot.add_cog(AdminCommands(bot))
