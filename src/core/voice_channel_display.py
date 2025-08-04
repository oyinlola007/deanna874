import discord
from discord.ext import commands, tasks
from src.core.database import Database
import logging

logger = logging.getLogger(__name__)
dao = Database()


class VoiceChannelDisplay(commands.Cog):
    """Manages automated voice channel display of top 3 users."""

    def __init__(self, bot):
        self.bot = bot
        self.channel_names = ["🥇 1st Place", "🥈 2nd Place", "🥉 3rd Place"]
        self.update_interval = 60  # 1 minute
        self.update_voice_channel.start()

    def cog_unload(self):
        """Clean up when cog is unloaded."""
        self.update_voice_channel.cancel()

    async def get_or_create_display_channels(self, guild: discord.Guild) -> list:
        """Get or create the voice channels for displaying top users."""
        channels = []
        guild_id = str(guild.id)
        category_name = "═════Top Members═════"

        # Try to get existing channels from database
        saved_channel_ids = dao.get_voice_channel_display(guild_id)

        if saved_channel_ids:
            # Use saved channels if they exist
            for channel_id in saved_channel_ids:
                channel = guild.get_channel(int(channel_id))
                if channel:
                    channels.append(channel)

            # If we found all 3 channels, return them
            if len(channels) == 3:
                return channels

        # Get or create the category
        category = discord.utils.get(guild.categories, name=category_name)
        if not category:
            try:
                # Force category to the very top by using position 0
                category = await guild.create_category(
                    name=category_name,
                    position=0,
                    reason="Automated top users display category",
                )
                logger.info(f"Created category '{category_name}' in {guild.name}")
            except discord.Forbidden:
                logger.error(
                    f"Bot doesn't have permission to create categories in {guild.name}"
                )
                return []
            except Exception as e:
                logger.error(
                    f"Error creating category '{category_name}' in {guild.name}: {e}"
                )
                return []
        else:
            # If category exists but is not at the top, move it to position 0
            try:
                if category.position != 0:
                    await category.edit(
                        position=0, reason="Moving top users category to top"
                    )
                    logger.info(
                        f"Moved category '{category_name}' to top in {guild.name}"
                    )
            except discord.Forbidden:
                logger.warning(
                    f"Bot doesn't have permission to move category in {guild.name}"
                )
            except Exception as e:
                logger.warning(
                    f"Error moving category '{category_name}' in {guild.name}: {e}"
                )

        # If we don't have all channels, create new ones
        channels = []
        for channel_name in self.channel_names:
            # Look for existing channel with this name in the category
            existing_channel = discord.utils.get(
                category.voice_channels, name=channel_name
            )

            if existing_channel:
                channels.append(existing_channel)
                continue

            # Create new channel if it doesn't exist
            try:
                # Create locked voice channel (no permissions for @everyone)
                overwrites = {
                    guild.default_role: discord.PermissionOverwrite(
                        connect=False, view_channel=True
                    )
                }

                new_channel = await guild.create_voice_channel(
                    name=channel_name,
                    category=category,
                    overwrites=overwrites,
                    reason="Automated top users display channel",
                )

                logger.info(
                    f"Created locked voice channel '{channel_name}' in {guild.name}"
                )
                channels.append(new_channel)

            except discord.Forbidden:
                logger.error(
                    f"Bot doesn't have permission to create voice channels in {guild.name}"
                )
                return []
            except Exception as e:
                logger.error(
                    f"Error creating voice channel '{channel_name}' in {guild.name}: {e}"
                )
                return []

        # Save the channel IDs to database
        if channels:
            channel_ids = [str(channel.id) for channel in channels]
            dao.save_voice_channel_display(guild_id, channel_ids)

        return channels

    def get_top_users_display(self) -> list:
        """Get the top 3 users formatted for display with points."""
        try:
            # Get top 3 users from leaderboard
            top_users = dao.get_leaderboard(3)

            if not top_users:
                return ["🥇 1st Place", "🥈 2nd Place", "🥉 3rd Place"]

            # Format the display strings for each position
            displays = []
            medals = ["🥇", "🥈", "🥉"]

            for i, (discord_id, points) in enumerate(top_users):
                # Get user object to get display name
                user = self.bot.get_user(int(discord_id))
                username = user.display_name if user else f"User{discord_id}"

                # Format: medal + username + points
                display = f"{medals[i]} {username} ({points:,} XP)"

                # Discord channel names have a 100 character limit
                if len(display) > 100:
                    # If too long, try without the thousands separator
                    display = f"{medals[i]} {username} ({points} XP)"

                    # If still too long, truncate username
                    if len(display) > 100:
                        max_username_length = 100 - len(
                            f"{medals[i]} ... ({points} XP)"
                        )
                        truncated_username = username[:max_username_length]
                        display = f"{medals[i]} {truncated_username} ({points} XP)"

                displays.append(display)

            # Fill remaining slots if less than 3 users
            while len(displays) < 3:
                displays.append(f"{self.channel_names[len(displays)]}")

            return displays

        except Exception as e:
            logger.error(f"Error getting top users display: {e}")
            return ["🥇 1st Place", "🥈 2nd Place", "🥉 3rd Place"]

    async def update_channel_name(self, guild: discord.Guild):
        """Update the voice channel names with current top 3 users."""
        try:
            # Check if voice channel display is enabled
            if dao.get_config("voice_channel_display_enabled") != "true":
                return

            # Get or create the display channels
            channels = await self.get_or_create_display_channels(guild)
            if not channels:
                return

            # Get new display names
            new_names = self.get_top_users_display()

            # Update each channel
            for i, channel in enumerate(channels):
                if i < len(new_names):
                    new_name = new_names[i]

                    # Only update if the name has changed
                    if channel.name != new_name:
                        try:
                            await channel.edit(name=new_name, reason="Top users update")
                            logger.info(
                                f"Updated voice channel name in {guild.name}: {new_name}"
                            )
                        except discord.Forbidden:
                            logger.error(
                                f"Bot doesn't have permission to edit voice channel in {guild.name}"
                            )
                        except Exception as e:
                            logger.error(
                                f"Error updating voice channel name in {guild.name}: {e}"
                            )

        except Exception as e:
            logger.error(f"Error in update_channel_name for {guild.name}: {e}")

    @tasks.loop(seconds=60)  # Update every 1 minute
    async def update_voice_channel(self):
        """Periodically update voice channel names for all guilds."""
        try:
            for guild in self.bot.guilds:
                await self.update_channel_name(guild)
        except Exception as e:
            logger.error(f"Error in update_voice_channel task: {e}")

    @update_voice_channel.before_loop
    async def before_update_voice_channel(self):
        """Wait until bot is ready before starting the task."""
        await self.bot.wait_until_ready()

    @commands.command()
    @commands.check(lambda ctx: dao.is_admin(str(ctx.author.id)))
    async def togglevoicedisplay(self, ctx):
        """Toggle voice channel display on/off."""
        current_setting = dao.get_config("voice_channel_display_enabled")
        new_setting = "false" if current_setting == "true" else "true"

        dao.update_config("voice_channel_display_enabled", new_setting)

        status = "enabled" if new_setting == "true" else "disabled"
        await ctx.send(f"✅ Voice channel display {status}.")

    @commands.command()
    @commands.check(lambda ctx: dao.is_admin(str(ctx.author.id)))
    async def updatevoicedisplay(self, ctx):
        """Manually update the voice channel display."""
        await self.update_channel_name(ctx.guild)
        await ctx.send("✅ Voice channel display updated with points.")

    @commands.command()
    @commands.check(lambda ctx: dao.is_admin(str(ctx.author.id)))
    async def setvoiceinterval(self, ctx, seconds: str = None):
        """Set the update interval for voice channel display (in seconds)."""
        if not seconds or not seconds.isdigit():
            await ctx.send("Usage: !setvoiceinterval <seconds>")
            return

        seconds = int(seconds)
        if seconds < 60:  # Minimum 1 minute
            await ctx.send("❌ Update interval must be at least 60 seconds.")
            return

        # Update the interval
        self.update_interval = seconds
        dao.update_config("voice_channel_update_interval", str(seconds))

        # Restart the task with new interval
        self.update_voice_channel.cancel()
        self.update_voice_channel.change_interval(seconds=seconds)
        self.update_voice_channel.start()

        await ctx.send(f"✅ Voice channel update interval set to {seconds} seconds.")


async def setup(bot):
    await bot.add_cog(VoiceChannelDisplay(bot))
    logger.info("Voice channel display manager initialized")
