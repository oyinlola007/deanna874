from discord.ext import commands
from src.core.database import Database
import discord
import src.core.config as config

dao = Database()


class AdminCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.check(lambda ctx: dao.is_admin(str(ctx.author.id)))
    async def adminhelp(self, ctx):
        help_text_1 = """**🔐 Admin Commands**
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
!listmilestones                         - Show all milestones with details
!addmilestone <value> <message>         - Create new milestone
!removemilestone <value>                - Remove (deactivate) a milestone
!setmilestonemessage <value> <message>  - Set/update milestone message
!setmilestonerole <value> <role_name>   - Set role for milestone (validates role exists)
!removemilestonerole <value>            - Remove role from milestone
!assignroles                            - Assign roles to all members
!markrewarded <reward_code>             - Mark reward as sent
!pendingrewards                         - List users awaiting rewards
!markrewardedbatch <codes...>           - Mark multiple rewards as sent (space-separated)```"""

        help_text_2 = """
```yaml
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
!leaderboard                            - View top members by points (everyone)

📦 Utilities
!exportdb                               - Export the database file

🎤 Voice Channel Display
!togglevoicedisplay                     - Toggle voice channel display on/off
!updatevoicedisplay                     - Manually update voice channel display
!setvoiceinterval <seconds>             - Set update interval (min 60s)

🎯 Campaign Management
!createcampaign <channel> <name> <multiplier> <start_date> <end_date>
!listcampaigns                          - Show all campaigns
!editcampaign <channel> <field> <value> - Edit campaign settings
!deletecampaign <channel>               - Delete campaign
!campaignstatus                         - Show active campaigns```"""

        await ctx.send(help_text_1)
        await ctx.send(help_text_2)

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

    @commands.command()
    @commands.check(lambda ctx: dao.is_admin(str(ctx.author.id)))
    async def assignroles(self, ctx):
        """Assign roles to all members based on their current levels."""
        await ctx.send("🔄 Starting bulk role assignment... This may take a while.")

        try:
            if not hasattr(self.bot, "role_manager"):
                await ctx.send("❌ Role manager not initialized.")
                return

            summary = await self.bot.role_manager.assign_roles_for_all_members(
                ctx.guild
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

            await ctx.send(embed=embed)

        except Exception as e:
            await ctx.send(f"❌ Error during role assignment: {str(e)}")

    @commands.command()
    @commands.check(lambda ctx: dao.is_admin(str(ctx.author.id)))
    async def markrewardedbatch(self, ctx, codes: str = None):
        """Mark multiple rewards as sent. Usage: !markrewardedbatch code1 code2 code3"""
        if not codes:
            await ctx.send("Usage: !markrewardedbatch <code1 code2 ...>")
            return
        code_list = [c.strip() for c in codes.split() if c.strip()]
        if not code_list:
            await ctx.send("No valid codes provided.")
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
        await ctx.send(msg)

    @commands.command()
    @commands.check(lambda ctx: dao.is_admin(str(ctx.author.id)))
    async def createcampaign(
        self, ctx, channel_mention: str = None, *, campaign_info: str = None
    ):
        """Create a campaign channel. Usage: !createcampaign #channel "Campaign Name" 2.0 2024-12-01 2024-12-31"""
        if not channel_mention or not campaign_info:
            await ctx.send(
                'Usage: !createcampaign #channel "Campaign Name" 2.0 2024-12-01 2024-12-31'
            )
            return

        try:
            # Extract channel ID from mention
            channel_id = channel_mention.strip("<#>")

            # Parse campaign info
            parts = campaign_info.split()
            if len(parts) < 4:
                await ctx.send(
                    '❌ Invalid format. Use: "Campaign Name" 2.0 2024-12-01 2024-12-31'
                )
                return

            # Find the multiplier (should be a number)
            multiplier = None
            campaign_name = ""
            dates = []

            for part in parts:
                if part.replace(".", "").isdigit() and multiplier is None:
                    multiplier = float(part)
                elif len(part.split("-")) == 3:  # Date format
                    dates.append(part)
                else:
                    campaign_name += part + " "

            campaign_name = campaign_name.strip()

            if not multiplier or len(dates) != 2:
                await ctx.send(
                    '❌ Invalid format. Use: "Campaign Name" 2.0 2024-12-01 2024-12-31'
                )
                return

            start_date, end_date = dates[0], dates[1]

            # Validate dates
            from datetime import datetime

            try:
                datetime.strptime(start_date, "%Y-%m-%d")
                datetime.strptime(end_date, "%Y-%m-%d")
            except ValueError:
                await ctx.send("❌ Invalid date format. Use YYYY-MM-DD")
                return

            # Create campaign
            dao.add_campaign_channel(
                channel_id, campaign_name, multiplier, start_date, end_date
            )

            await ctx.send(
                f"✅ Campaign created!\n**Channel:** <#{channel_id}>\n**Name:** {campaign_name}\n**Multiplier:** {multiplier}x\n**Period:** {start_date} to {end_date}"
            )

        except Exception as e:
            await ctx.send(f"❌ Error creating campaign: {e}")

    @commands.command()
    @commands.check(lambda ctx: dao.is_admin(str(ctx.author.id)))
    async def listcampaigns(self, ctx):
        """List all campaigns."""
        campaigns = dao.get_all_campaigns()

        if not campaigns:
            await ctx.send("📋 No campaigns found.")
            return

        embed = discord.Embed(
            title="📋 All Campaigns",
            description="List of all campaigns (active and inactive)",
            color=discord.Color.blue(),
        )

        for channel_id, name, multiplier, start_date, end_date, status in campaigns:
            status_emoji = "🟢" if status == "active" else "🔴"
            embed.add_field(
                name=f"{status_emoji} {name}",
                value=f"**Channel:** <#{channel_id}>\n**Multiplier:** {multiplier}x\n**Period:** {start_date} to {end_date}\n**Status:** {status}",
                inline=False,
            )

        await ctx.send(embed=embed)

    @commands.command()
    @commands.check(lambda ctx: dao.is_admin(str(ctx.author.id)))
    async def campaignstatus(self, ctx):
        """Show active campaigns."""
        campaigns = dao.get_active_campaigns()

        if not campaigns:
            await ctx.send("🎯 No active campaigns.")
            return

        embed = discord.Embed(
            title="🎯 Active Campaigns",
            description="Currently active campaigns with multipliers",
            color=discord.Color.green(),
        )

        for channel_id, name, multiplier, start_date, end_date in campaigns:
            embed.add_field(
                name=f"🎯 {name}",
                value=f"**Channel:** <#{channel_id}>\n**Multiplier:** {multiplier}x\n**Period:** {start_date} to {end_date}",
                inline=False,
            )

        await ctx.send(embed=embed)

    @commands.command()
    @commands.check(lambda ctx: dao.is_admin(str(ctx.author.id)))
    async def deletecampaign(self, ctx, channel_mention: str = None):
        """Delete a campaign. Usage: !deletecampaign #channel"""
        if not channel_mention:
            await ctx.send("Usage: !deletecampaign #channel")
            return

        try:
            channel_id = channel_mention.strip("<#>")
            dao.delete_campaign_channel(channel_id)
            await ctx.send(f"✅ Campaign deleted for <#{channel_id}>")
        except Exception as e:
            await ctx.send(f"❌ Error deleting campaign: {e}")


async def setup(bot):
    await bot.add_cog(AdminCommands(bot))
