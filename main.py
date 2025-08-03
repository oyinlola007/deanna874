import re
import os
import discord
import random
import string
import logging
from discord.ext.commands import check
from discord.ext.commands import CheckFailure
from discord.ext import commands, tasks
from dotenv import load_dotenv

load_dotenv()

from src.core.database import Database
import src.utils.utils as utils
import src.core.config as config
import src.core.setup_db as setup_db


# Setup DB if missing
# if not os.path.exists(config.DATABASE_NAME):
#     os.makedirs(os.path.dirname(config.DATABASE_NAME), exist_ok=True)
#     setup_db.setup()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

setup_db.setup(logger)

# Setup bot intents
intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.members = True
intents.message_content = True
intents.reactions = True
intents.invites = True

bot = commands.Bot(command_prefix="!", intents=intents)
dao = Database()
invites = {}

URL_REGEX = re.compile(r"https?://\S+")


@bot.event
async def on_ready():
    logger.info(f"✅ {bot.user} is ready!")
    logger.info(f"📊 Connected to {len(bot.guilds)} guild(s)")

    # Run database migration
    try:
        from src.core.migration_manager import run_migrations

        logger.info("🔄 Running database migrations...")
        success = run_migrations()
        if success:
            logger.info("✅ Database migrations completed successfully!")
        else:
            logger.error("❌ Database migrations failed!")
    except Exception as e:
        logger.error(f"❌ Error during migration: {e}")

    # Load Cogs
    extensions = [
        # "src.commands.admin",
        # "src.commands.points",
        # "src.commands.milestones",
        # "src.commands.tracking",
        "src.commands.slash_points",
        "src.commands.slash_config",
        "src.commands.slash_milestones",
        "src.commands.slash_roles",
        "src.commands.slash_rewards",
        "src.commands.slash_channels",
        "src.commands.slash_admin_management",
        "src.commands.slash_exclusion",
        "src.commands.slash_leaderboard",
        "src.commands.slash_database",
        "src.commands.slash_voice_display",
        "src.commands.slash_campaigns",
        "src.commands.slash_help",
        "src.commands.slash_dashboard",
        "src.core.role_manager",
        "src.core.voice_channel_display",
    ]

    for ext in extensions:
        try:
            if ext in bot.extensions:
                await bot.reload_extension(ext)
                logger.info(f"🔁 Reloaded extension: {ext}")
            else:
                await bot.load_extension(ext)
                logger.info(f"✅ Loaded extension: {ext}")
        except Exception as e:
            logger.error(f"❌ Failed to (re)load {ext}: {e}")

    # Sync slash commands with Discord
    try:
        logger.info("🔄 Syncing slash commands...")
        await bot.tree.sync()
        logger.info("✅ Slash commands synced successfully!")
    except Exception as e:
        logger.error(f"❌ Failed to sync slash commands: {e}")

    # Start invite cache update
    if not update_invite_cache.is_running():
        update_invite_cache.start()

    # Auto-assign roles for all guilds after everything is loaded
    auto_assign_roles = dao.get_config("auto_assign_roles_on_startup")
    if auto_assign_roles != "false":  # Default to true unless explicitly set to false
        logger.info("🔄 Starting automatic role assignment for all guilds...")
        for guild in bot.guilds:
            try:
                if hasattr(bot, "role_manager"):
                    summary = await bot.role_manager.assign_roles_for_all_members(guild)
                    logger.info(
                        f"📊 Role assignment for {guild.name}: {summary['total_checked']} members checked, {summary['roles_added']} roles added, {summary['roles_removed']} roles removed"
                    )
                else:
                    logger.warning(f"Role manager not available for {guild.name}")
            except Exception as e:
                logger.error(f"❌ Error assigning roles for {guild.name}: {e}")
    else:
        logger.info("⏭️ Skipping automatic role assignment (disabled in config)")

    logger.info("✅ Bot startup complete!")


def is_admin():
    async def predicate(ctx):
        return dao.is_admin(str(ctx.author.id))

    return check(predicate)


async def check_and_notify_milestone(discord_id: str):
    milestone = dao.get_next_milestone(discord_id)
    if milestone:
        reward_code = "".join(
            random.choices(string.ascii_uppercase + string.digits, k=5)
        )
        dao.record_milestone(discord_id, milestone, reward_code)

        # Update user's level to the milestone value
        dao.update_user_level(discord_id, milestone)

        # Try to notify the user via DM
        user = await bot.fetch_user(int(discord_id))
        try:
            msg = (
                dao.get_milestone_message(milestone)
                or f"🎉 Congrats! You've reached a milestone of {milestone} points!"
            )
            await user.send(msg)
            logger.info(
                f"[MILESTONE] {user} reached {milestone} points and was notified."
            )
            dao.mark_milestone_user_notified(discord_id, milestone)
        except discord.Forbidden:
            logger.info(f"[DM ERROR] Couldn't DM {user} - DMs disabled")
        except Exception as e:
            logger.info(f"[DM ERROR] Couldn't DM {user}: {e}")

        # Try to notify admins
        try:
            channel_id = dao.get_config("notification_channel_id")
            if channel_id:
                admin_channel = bot.get_channel(int(channel_id))
                if admin_channel:
                    # Get milestone details for role information
                    milestone_details = dao.get_milestone_details(milestone)
                    role_info = ""
                    if milestone_details and milestone_details.get("role_name"):
                        role_info = f"\nRole: {milestone_details['role_name']}"

                    await admin_channel.send(
                        f"📢 **Milestone Reached**\nUser: <@{discord_id}>\nMilestone: {milestone}{role_info}\nReward Code: `{reward_code}`"
                    )
                    dao.mark_milestone_admin_notified(discord_id, milestone)
                else:
                    logger.warning(
                        f"[ADMIN CHANNEL ERROR] Admin channel {channel_id} not found or inaccessible"
                    )
            else:
                logger.warning("[ADMIN CHANNEL ERROR] No admin channel configured")
        except Exception as e:
            logger.warning(f"[ADMIN CHANNEL ERROR] {e}")

            # Fallback: Try to DM the first admin (but don't crash if it fails)
            try:
                admin_ids = dao.get_all_admin_ids()
                if admin_ids:
                    admin_user = await bot.fetch_user(int(admin_ids[0]))
                    await admin_user.send(
                        f"⚠️ **Milestone Reached but No Admin Channel Configured**\n\n"
                        f"User: <@{discord_id}>\nMilestone: {milestone}\nReward Code: `{reward_code}`\n\n"
                        f"Please set a proper admin notification channel using:\n"
                        f"`!setconfig notification_channel_id <channel_id>`"
                    )
            except discord.Forbidden:
                logger.warning(f"[ADMIN DM ERROR] Couldn't DM admin - DMs disabled")
            except Exception as e:
                logger.warning(f"[ADMIN DM ERROR] Couldn't DM admin: {e}")


# 1. Track messages
@bot.event
async def on_message(message):
    if message.author.bot:
        return

    if dao.is_tracked_channel(str(message.channel.id)):
        user_id = str(message.author.id)
        channel_id = str(message.channel.id)
        message_id = str(message.id)

        logged = False  # flag to prevent double logging

        # 1. Track image
        if message.attachments:
            for attachment in message.attachments:
                if attachment.content_type and attachment.content_type.startswith(
                    "image/"
                ):
                    image_points = int(dao.get_config("points_per_image") or 10)

                    # Apply campaign multiplier if channel is a campaign channel
                    campaign_multiplier = dao.get_campaign_multiplier(channel_id)
                    if campaign_multiplier > 1.0:
                        image_points = int(image_points * campaign_multiplier)
                        logger.info(
                            f"[CAMPAIGN] {message.author} earned {image_points} points (base: {int(image_points/campaign_multiplier)}, multiplier: {campaign_multiplier}x)"
                        )

                    if dao.can_earn_points(user_id, image_points):
                        dao.add_points_to_member(user_id, image_points)
                        dao.log_engagement(
                            user_id, "image", message_id, channel_id, image_points
                        )
                        logged = True
                    break  # log once per message

        # 2. Track shared URL
        elif URL_REGEX.search(message.content):
            share_points = int(dao.get_config("points_per_share") or 50)

            # Apply campaign multiplier if channel is a campaign channel
            campaign_multiplier = dao.get_campaign_multiplier(channel_id)
            if campaign_multiplier > 1.0:
                share_points = int(share_points * campaign_multiplier)
                logger.info(
                    f"[CAMPAIGN] {message.author} earned {share_points} points (base: {int(share_points/campaign_multiplier)}, multiplier: {campaign_multiplier}x)"
                )

            if dao.can_earn_points(user_id, share_points):
                dao.add_points_to_member(user_id, share_points)
                dao.log_engagement(
                    user_id, "share", message_id, channel_id, share_points
                )
                logged = True

        # 3. Fallback to regular message if no image or URL
        if not logged:
            message_points = int(dao.get_config("points_per_message") or 5)

            # Apply campaign multiplier if channel is a campaign channel
            campaign_multiplier = dao.get_campaign_multiplier(channel_id)
            if campaign_multiplier > 1.0:
                message_points = int(message_points * campaign_multiplier)
                logger.info(
                    f"[CAMPAIGN] {message.author} earned {message_points} points (base: {int(message_points/campaign_multiplier)}, multiplier: {campaign_multiplier}x)"
                )

            if dao.can_earn_points(user_id, message_points):
                dao.add_points_to_member(user_id, message_points)
                dao.log_engagement(
                    user_id, "message", message_id, channel_id, message_points
                )

        # Update user's level based on new points
        current_points = dao.get_user_points(user_id)
        dao.update_user_level(user_id, current_points)

        # Update streak tracking
        dao.update_streak(user_id)

        # Check for milestone
        await check_and_notify_milestone(user_id)

        # Check for role assignment/downgrading
        if hasattr(bot, "role_manager"):
            await bot.role_manager.check_and_assign_roles(user_id, message.guild)

        # Update voice channel display
        if hasattr(bot, "voice_channel_display"):
            await bot.voice_channel_display.update_channel_name(message.guild)

    await bot.process_commands(message)


# 2. Track reactions
@bot.event
async def on_reaction_add(reaction, user):
    if user.bot:
        return

    user_id = str(user.id)
    message_id = str(reaction.message.id)
    channel_id = str(reaction.message.channel.id)

    if dao.is_tracked_channel(channel_id):
        if not dao.has_user_reacted_to_message(user_id, message_id):
            POINT_VALUE = int(dao.get_config("points_per_reaction") or 5)

            # Apply campaign multiplier if channel is a campaign channel
            campaign_multiplier = dao.get_campaign_multiplier(channel_id)
            if campaign_multiplier > 1.0:
                POINT_VALUE = int(POINT_VALUE * campaign_multiplier)
                logger.info(
                    f"[CAMPAIGN] {user} earned {POINT_VALUE} points for reaction (base: {int(POINT_VALUE/campaign_multiplier)}, multiplier: {campaign_multiplier}x)"
                )

            if dao.can_earn_points(user_id, POINT_VALUE):
                dao.add_points_to_member(user_id, POINT_VALUE)
                dao.log_engagement(
                    user_id, "reaction", message_id, channel_id, POINT_VALUE
                )
                logger.info(f"[INFO] Reaction logged and points awarded to {user.name}")

                # Update user's level based on new points
                current_points = dao.get_user_points(user_id)
                dao.update_user_level(user_id, current_points)

                # Update streak tracking
                dao.update_streak(user_id)

                # Check for milestone
                await check_and_notify_milestone(user_id)

                # Check for role assignment/downgrading
                if hasattr(bot, "role_manager"):
                    await bot.role_manager.check_and_assign_roles(
                        user_id, reaction.message.guild
                    )

                # Update voice channel display
                if hasattr(bot, "voice_channel_display"):
                    await bot.voice_channel_display.update_channel_name(
                        reaction.message.guild
                    )


# 3. Track invites (when new member joins)
@bot.event
async def on_member_join(member):
    try:
        guild_id = member.guild.id
        invites_before = invites.get(guild_id, [])
        invites_after = await member.guild.invites()

        for old_invite in invites_before:
            new_invite = utils.find_invite_by_code(invites_after, old_invite.code)

            if new_invite and new_invite.uses > old_invite.uses:
                inviter = old_invite.inviter
                inviter_id = str(inviter.id)
                invitee_id = str(member.id)
                invite_key = f"invite_{invitee_id}"

                # Only award points if this inviter hasn't already invited this member
                if not dao.has_invited_before(inviter_id, invitee_id):
                    POINT_VALUE = int(dao.get_config("points_per_invite") or 1000)
                    if dao.can_earn_points(inviter_id, POINT_VALUE):
                        dao.add_points_to_member(inviter_id, POINT_VALUE)
                        dao.log_engagement(
                            inviter_id, "invite", invite_key, "N/A", POINT_VALUE
                        )
                        logger.info(
                            f"[INFO] {inviter} earned {POINT_VALUE} points for inviting {member}"
                        )

                        # Update user's level based on new points
                        current_points = dao.get_user_points(inviter_id)
                        dao.update_user_level(inviter_id, current_points)

                        # Update streak tracking
                        dao.update_streak(inviter_id)

                        # Check for milestone
                        await check_and_notify_milestone(inviter_id)

                        # Check for role assignment/downgrading
                        if hasattr(bot, "role_manager"):
                            await bot.role_manager.check_and_assign_roles(
                                inviter_id, member.guild
                            )

                        # Update voice channel display
                        if hasattr(bot, "voice_channel_display"):
                            await bot.voice_channel_display.update_channel_name(
                                member.guild
                            )
                    else:
                        logger.info(
                            f"[SKIP] {inviter} has reached daily points limit — no points awarded for invite."
                        )
                else:
                    logger.info(
                        f"[SKIP] {inviter} already invited {member} before — no points awarded."
                    )

                break  # Stop after matching the invite

        invites[guild_id] = invites_after  # Refresh cache after join

    except Exception as e:
        logger.info(f"[ERROR] on_member_join: {e}")


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, CheckFailure):
        pass


@tasks.loop(seconds=30)
async def update_invite_cache():
    for guild in bot.guilds:
        try:
            invites[guild.id] = await guild.invites()
        except Exception as e:
            logger.info(f"Invite cache update failed for {guild.name}: {e}")


# Run bot
bot.run(config.BOT_TOKEN)
