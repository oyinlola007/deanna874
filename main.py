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

from cogs.dao import Database
import cogs.utils as utils
import cogs.config as config
import cogs.setup_db as setup_db


# Setup DB if missing
if not os.path.exists(config.DATABASE_NAME):
    os.makedirs(os.path.dirname(config.DATABASE_NAME), exist_ok=True)
    setup_db.setup()


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
    logger.info(f"{bot.user} has connected.")
    if not update_invite_cache.is_running():
        update_invite_cache.start()

    # Load Cogs
    extensions = [
        "cogs.commands.admin",
        "cogs.commands.points",
        "cogs.commands.milestones",
        "cogs.commands.tracking",
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
        except Exception as e:
            logger.info(f"[DM ERROR] Couldn't DM {user}: {e}")

        try:
            channel_id = dao.get_config("notification_channel_id")
            if channel_id:
                admin_channel = bot.get_channel(int(channel_id))
                if admin_channel:
                    await admin_channel.send(
                        f"📢 **Milestone Reached**\nUser: <@{discord_id}>\nMilestone: {milestone}\nReward Code: `{reward_code}`"
                    )
                    dao.mark_milestone_admin_notified(discord_id, milestone)
                else:
                    raise ValueError("Admin channel not found or inaccessible.")
            else:
                raise ValueError("No admin channel configured.")
        except Exception as e:
            logger.info(f"[ADMIN CHANNEL ERROR] {e}")

            # Fallback: DM the first admin
            admin_ids = dao.get_all_admin_ids()
            if admin_ids:
                admin_user = await bot.fetch_user(int(admin_ids[0]))
                await admin_user.send(
                    f"⚠️ **Milestone Reached but No Admin Channel Configured**\n\n"
                    f"User: <@{discord_id}>\nMilestone: {milestone}\nReward Code: `{reward_code}`\n\n"
                    f"Please set a proper admin notification channel using:\n"
                    f"`!setconfig notification_channel_id <channel_id>`"
                )


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
                    dao.add_points_to_member(user_id, image_points)
                    dao.log_engagement(
                        user_id, "image", message_id, channel_id, image_points
                    )
                    logged = True
                    break  # log once per message

        # 2. Track shared URL
        elif URL_REGEX.search(message.content):
            share_points = int(dao.get_config("points_per_share") or 50)
            dao.add_points_to_member(user_id, share_points)
            dao.log_engagement(user_id, "share", message_id, channel_id, share_points)
            logged = True

        # 3. Fallback to regular message if no image or URL
        if not logged:
            message_points = int(dao.get_config("points_per_message") or 5)
            dao.add_points_to_member(user_id, message_points)
            dao.log_engagement(
                user_id, "message", message_id, channel_id, message_points
            )

        await check_and_notify_milestone(user_id)

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
            dao.add_points_to_member(user_id, POINT_VALUE)
            dao.log_engagement(user_id, "reaction", message_id, channel_id, POINT_VALUE)
            logger.info(f"[INFO] Reaction logged and points awarded to {user.name}")

            await check_and_notify_milestone(user_id)


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
                    dao.add_points_to_member(inviter_id, POINT_VALUE)
                    dao.log_engagement(
                        inviter_id, "invite", invite_key, "N/A", POINT_VALUE
                    )
                    logger.info(
                        f"[INFO] {inviter} earned {POINT_VALUE} points for inviting {member}"
                    )

                    await check_and_notify_milestone(inviter_id)
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
