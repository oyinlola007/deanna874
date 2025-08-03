import discord
from discord import app_commands
from discord.ext import commands
import asyncio
import logging
import os
import tempfile
import time
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from jinja2 import Environment, FileSystemLoader
from playwright.async_api import async_playwright
from src.core.database import Database

logger = logging.getLogger(__name__)


class DashboardCommands(commands.Cog):
    """Commands for generating user dashboards."""

    def __init__(self, bot):
        self.bot = bot
        self.dao = Database()

        # Setup paths and environment
        self._setup_dashboard_environment()

    def _setup_dashboard_environment(self):
        """Initialize dashboard generation environment."""
        self.template_dir = Path("src/dashboard/templates")
        self.static_dir = Path("src/dashboard/static")
        self.output_dir = Path("src/dashboard/output")
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Jinja2 environment
        self.env = Environment(
            loader=FileSystemLoader(str(self.template_dir)), autoescape=True
        )

        # Load CSS once
        self._load_css()

    def _load_css(self):
        """Load and cache CSS content."""
        css_path = self.static_dir / "css" / "neumorphism.css"
        try:
            with open(css_path, "r", encoding="utf-8") as f:
                self.css_content = f.read()
        except FileNotFoundError:
            logger.error(f"CSS file not found: {css_path}")
            self.css_content = "/* CSS not found */"

    @app_commands.command(
        name="ttp-dashboard", description="Generate your personal dashboard"
    )
    async def dashboard(self, interaction: discord.Interaction):
        """Generate a personal dashboard for the user."""
        await interaction.response.defer(ephemeral=True)

        try:
            user_id = str(interaction.user.id)

            # Generate fresh dashboard data
            user_data = await self._get_user_dashboard_data(interaction)

            # Generate image and upload
            image_path = await self._generate_dashboard_async(user_data, user_id)

            # Send the image and delete local file
            await self._send_and_cleanup(interaction, image_path)

        except Exception as e:
            logger.error(f"Error generating dashboard for {interaction.user.id}: {e}")
            await interaction.followup.send(
                "❌ Sorry, there was an error generating your dashboard. Please try again later.",
                ephemeral=True,
            )

    @app_commands.command(
        name="ttp-mystats", description="Generate your quick stats snapshot"
    )
    async def mystats(self, interaction: discord.Interaction):
        """Generate a quick stats snapshot for the user."""
        await interaction.response.defer(ephemeral=True)

        try:
            user_id = str(interaction.user.id)

            # Generate fresh mystats data
            user_data = await self._get_user_mystats_data(interaction)

            # Generate image and upload
            image_path = await self._generate_mystats_async(user_data, user_id)

            # Send the image and delete local file
            await self._send_and_cleanup(interaction, image_path)

        except Exception as e:
            logger.error(f"Error generating mystats for {interaction.user.id}: {e}")
            await interaction.followup.send(
                "❌ Sorry, there was an error generating your stats. Please try again later.",
                ephemeral=True,
            )

    async def _send_and_cleanup(
        self, interaction: discord.Interaction, image_path: str
    ):
        """Send dashboard image and delete local file."""
        try:
            # Send the image
            file = discord.File(image_path, filename="dashboard.png")
            await interaction.followup.send(file=file, ephemeral=True)
        finally:
            # Always delete the local file
            self._delete_local_file(image_path)

    def _delete_local_file(self, file_path: str):
        """Delete local file safely."""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.debug(f"Deleted local file: {file_path}")
        except Exception as e:
            logger.error(f"Error deleting file {file_path}: {e}")

    async def _get_user_dashboard_data(self, interaction: discord.Interaction) -> Dict:
        """Get all data needed for dashboard generation."""
        user_id = str(interaction.user.id)

        # Get or create user
        user_info = self._get_or_create_user(interaction)

        # Get user stats
        stats = self._get_user_stats(user_id)

        # Add streak data
        stats["streak"] = self.dao.get_current_streak(user_id)

        # Add total users count
        stats["total_users"] = self.dao.get_total_members_count()

        # Get server info
        server_info = self._get_server_info(interaction)

        # Get leaderboard
        leaderboard = self._get_formatted_leaderboard(interaction)

        # Calculate progress
        progress = self._calculate_progress(user_info)

        # Get activity data for chart
        activity_data = self._get_activity_data(stats)

        return {
            "user": user_info,
            "stats": stats,
            "server": server_info,
            "leaderboard": leaderboard,
            "progress": progress,
            "activity_data": activity_data,
            "timestamp": self._get_current_timestamp(),
        }

    def _get_or_create_user(self, interaction: discord.Interaction) -> Dict:
        """Get user info or create if doesn't exist."""
        user_id = str(interaction.user.id)
        user_info = self.dao.get_member_info(user_id)

        if not user_info:
            # Create new user
            self.dao.add_member(user_id)
            user_info = self.dao.get_member_info(user_id)

        # Add Discord user info
        user_info["name"] = interaction.user.display_name
        user_info["avatar_url"] = (
            str(interaction.user.avatar.url) if interaction.user.avatar else None
        )
        user_info["role"] = self._get_user_role_name(interaction.user)
        user_info["join_date"] = self._format_join_date(interaction.user.joined_at)
        user_info["rank"] = self.dao.get_user_rank(user_id)

        # Calculate current level (sequential number)
        current_points = user_info.get("total_points", 0)
        user_info["level"] = self._calculate_current_level(current_points)

        return user_info

    def _get_user_info(self, interaction: discord.Interaction) -> Dict:
        """Get user information."""
        user_id = str(interaction.user.id)
        user_info = self.dao.get_member_info(user_id)

        if not user_info:
            return {
                "discord_id": user_id,
                "total_points": 0,
                "level": 1,
                "current_streak": 0,
                "longest_streak": 0,
                "name": interaction.user.display_name,
                "avatar_url": (
                    str(interaction.user.avatar.url)
                    if interaction.user.avatar
                    else None
                ),
                "role": self._get_user_role_name(interaction.user),
                "join_date": self._format_join_date(interaction.user.joined_at),
                "rank": 0,
            }

        # Add Discord user info
        user_info["name"] = interaction.user.display_name
        user_info["avatar_url"] = (
            str(interaction.user.avatar.url) if interaction.user.avatar else None
        )
        user_info["role"] = self._get_user_role_name(interaction.user)
        user_info["join_date"] = self._format_join_date(interaction.user.joined_at)
        user_info["rank"] = self.dao.get_user_rank(user_id)

        return user_info

    def _get_server_info(self, interaction: discord.Interaction) -> Dict:
        """Get server information."""
        return {
            "name": interaction.guild.name,
            "icon_url": (
                str(interaction.guild.icon.url) if interaction.guild.icon else None
            ),
        }

    def _get_formatted_leaderboard(
        self, interaction: discord.Interaction
    ) -> List[Tuple]:
        """Get formatted leaderboard data."""
        raw_leaderboard = self.dao.get_leaderboard(limit=3)
        leaderboard = []
        current_user_id = str(interaction.user.id)

        for rank, (discord_id, points) in enumerate(raw_leaderboard, 1):
            user = interaction.guild.get_member(int(discord_id))
            name = user.display_name if user else f"User#{discord_id[-4:]}"
            leaderboard.append((rank, name, points))

        return leaderboard

    def _calculate_progress(self, user_info: Dict) -> Dict:
        """Calculate user progress data."""
        current_points = user_info.get("total_points", 0)

        # Get next milestone by points (for dashboard display)
        next_milestone = self.dao.get_next_milestone_by_points(current_points)

        # Calculate current level (sequential number)
        current_level = self._calculate_current_level(current_points)

        # Check if user is at max level
        if next_milestone is None:
            # User is at max level
            return {
                "level_percentage": 100,
                "daily_percentage": min(
                    100, (user_info.get("daily_points", 0) / 100) * 100
                ),
                "next_level_points": None,  # No next level
                "daily_limit": 100,
                "next_reward": None,  # No next reward
                "current_level": current_level,
            }

        next_level_points = next_milestone

        # Calculate level percentage
        prev_milestone = self._get_previous_milestone_by_points(current_points)
        prev_points = prev_milestone if prev_milestone else 0
        level_percentage = min(
            100,
            max(
                0,
                ((current_points - prev_points) / (next_level_points - prev_points))
                * 100,
            ),
        )

        # Get next reward info only if not at max level
        next_reward = (
            self._get_next_reward_info(current_points) if next_milestone else None
        )

        return {
            "level_percentage": level_percentage,
            "daily_percentage": min(
                100, (user_info.get("daily_points", 0) / 100) * 100
            ),
            "next_level_points": next_level_points,
            "daily_limit": 100,
            "next_reward": next_reward,
            "current_level": current_level,
        }

    def _calculate_current_level(self, current_points: int) -> int:
        """Calculate current level as sequential number."""
        try:
            with self.dao._connect() as conn:
                cur = conn.cursor()
                cur.execute(
                    "SELECT COUNT(*) FROM milestones WHERE status = 'active' AND value <= ?",
                    (current_points,),
                )
                return cur.fetchone()[0]
        except:
            return 1

    def _get_previous_milestone_by_points(self, current_points: int) -> Optional[int]:
        """Get the previous milestone based on current points."""
        try:
            with self.dao._connect() as conn:
                cur = conn.cursor()
                cur.execute(
                    "SELECT value FROM milestones WHERE status = 'active' AND value <= ? ORDER BY value DESC LIMIT 1",
                    (current_points,),
                )
                result = cur.fetchone()
                return result[0] if result else 0
        except:
            return 0

    def _get_activity_data(self, stats: Dict) -> Dict:
        """Get weekly activity data."""
        return {
            "messages": stats.get("weekly_messages", [0] * 7),
            "reactions": stats.get("weekly_reactions", [0] * 7),
            "attachments": stats.get("weekly_attachments", [0] * 7),
            "invites": stats.get("weekly_invites", [0] * 7),
        }

    def _get_user_stats(self, user_id: str) -> Dict:
        """Get comprehensive user statistics from engagement_log."""
        try:
            with self.dao._connect() as conn:
                cur = conn.cursor()

                # Activity counts
                cur.execute(
                    """
                    SELECT activity_type, COUNT(*) as count
                    FROM engagement_log 
                    WHERE discord_id = ?
                    GROUP BY activity_type
                """,
                    (user_id,),
                )
                activity_counts = dict(cur.fetchall())

                # Daily points
                cur.execute(
                    """
                    SELECT COALESCE(SUM(point_value), 0) as daily_points
                    FROM engagement_log 
                    WHERE discord_id = ? 
                    AND timestamp >= datetime('now', '-1 day')
                """,
                    (user_id,),
                )
                daily_points = cur.fetchone()[0]

                # Weekly data
                weekly_messages = self._get_weekly_activity(cur, user_id, "message")
                weekly_reactions = self._get_weekly_activity(cur, user_id, "reaction")
                weekly_attachments = self._get_weekly_activity(cur, user_id, "image")
                weekly_invites = self._get_weekly_activity(cur, user_id, "invite")

                return {
                    "messages": activity_counts.get("message", 0),
                    "reactions": activity_counts.get("reaction", 0),
                    "attachments": activity_counts.get(
                        "image", 0
                    ),  # Changed from 'attachment' to 'image'
                    "referrals": activity_counts.get("invite", 0),
                    "referral_points": activity_counts.get("invite", 0)
                    * int(self.dao.get_config("points_per_invite") or 200),
                    "daily_points": daily_points,
                    "weekly_messages": weekly_messages,
                    "weekly_reactions": weekly_reactions,
                    "weekly_attachments": weekly_attachments,
                    "weekly_invites": weekly_invites,
                }

        except Exception as e:
            logger.error(f"Error getting user stats: {e}")
            return self._get_default_stats()

    def _get_weekly_activity(self, cur, user_id: str, activity_type: str) -> List[int]:
        """Get weekly activity data for a specific type."""
        weekly_data = []
        # Get last 7 days, with today as the last day
        for i in range(6, -1, -1):  # 6, 5, 4, 3, 2, 1, 0 (today is 0)
            cur.execute(
                """
                SELECT COUNT(*) 
                FROM engagement_log 
                WHERE discord_id = ? 
                AND activity_type = ?
                AND timestamp >= datetime('now', '-{} days', 'start of day')
                AND timestamp < datetime('now', '-{} days', 'start of day', '+1 day')
            """.format(
                    i, i
                ),
                (user_id, activity_type),
            )
            weekly_data.append(cur.fetchone()[0])
        return weekly_data

    def _get_default_stats(self) -> Dict:
        """Get default stats when database query fails."""
        return {
            "messages": 0,
            "reactions": 0,
            "attachments": 0,
            "referrals": 0,
            "referral_points": 0,
            "daily_points": 0,
            "weekly_messages": [0] * 7,
            "weekly_reactions": [0] * 7,
            "weekly_attachments": [0] * 7,
            "weekly_invites": [0] * 7,
        }

    def _get_user_role_name(self, user: discord.Member) -> Optional[str]:
        """Get the user's milestone role name, if any."""
        user_id = str(user.id)

        # Get user's milestone role name from DAO
        milestone_role = self.dao.get_user_milestone_role_name(user_id)

        # Check if user actually has this role in Discord
        if milestone_role != "Active Trader":
            role = discord.utils.get(user.roles, name=milestone_role)
            if role:
                return milestone_role

        # No milestone role found or user doesn't have the role
        return None

    def _format_join_date(self, joined_at) -> str:
        """Format the user's join date."""
        return joined_at.strftime("%b %d, %Y") if joined_at else "Unknown"

    def _get_next_reward_info(self, current_points: int) -> str:
        """Get information about the next reward."""
        try:
            with self.dao._connect() as conn:
                cur = conn.cursor()
                cur.execute(
                    """
                    SELECT value, reward 
                    FROM milestones 
                    WHERE value > ? AND status = 'active'
                    ORDER BY value ASC 
                    LIMIT 1
                """,
                    (current_points,),
                )

                result = cur.fetchone()
                return (
                    f"Next: {result[1]}"
                    if result and result[1]
                    else "Next: Keep trading!"
                )
        except:
            return "Next: Keep trading!"

    def _get_current_timestamp(self) -> str:
        """Get current timestamp in the required format."""
        from datetime import datetime

        return datetime.now().strftime("%B %d, %Y at %I:%M %p")

    async def _generate_dashboard_async(self, user_data: Dict, user_id: str) -> str:
        """Generate dashboard image asynchronously."""
        try:
            # Generate filename and render template
            filename = f"dashboard_{user_id}_{int(time.time())}.png"
            output_path = self.output_dir / filename

            template = self.env.get_template("dashboard.html")
            html_content = template.render(**user_data)

            # Create complete HTML with embedded CSS
            complete_html = self._create_complete_html(html_content)

            # Generate image
            await self._render_html_to_image(complete_html, output_path)

            return str(output_path)

        except Exception as e:
            logger.error(f"Error generating dashboard image: {e}")
            raise

    def _create_complete_html(self, html_content: str) -> str:
        """Create complete HTML document with embedded CSS."""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>TTP Trading Dashboard</title>
            <style>
            {self.css_content}
            </style>
        </head>
        <body>
            {html_content}
        </body>
        </html>
        """

    async def _render_html_to_image(self, html_content: str, output_path: Path):
        """Render HTML content to image using Playwright."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".html", delete=False, encoding="utf-8"
        ) as f:
            f.write(html_content)
            temp_html_path = f.name

        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(
                    headless=True, args=["--no-sandbox", "--disable-dev-shm-usage"]
                )
                page = await browser.new_page()

                await page.goto(f"file://{temp_html_path}")
                await page.wait_for_load_state("networkidle")

                # Full page screenshot for dashboard
                await page.screenshot(path=str(output_path), full_page=True, type="png")

                await browser.close()

        finally:
            # Clean up temporary HTML file
            if os.path.exists(temp_html_path):
                os.unlink(temp_html_path)

    async def _render_mystats_to_image(self, html_content: str, output_path: Path):
        """Render mystats HTML content to cropped image using Playwright.

        This function captures only the stats card (.header-section) instead of
        the full page to eliminate empty space around the content.
        """
        # Create temporary HTML file for Playwright
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".html", delete=False, encoding="utf-8"
        ) as f:
            f.write(html_content)
            temp_html_path = f.name

        try:
            async with async_playwright() as p:
                # Launch headless browser
                browser = await p.chromium.launch(
                    headless=True, args=["--no-sandbox", "--disable-dev-shm-usage"]
                )
                page = await browser.new_page()

                # Load the HTML content
                await page.goto(f"file://{temp_html_path}")
                await page.wait_for_load_state("networkidle")

                # Crop to just the stats card element
                element = await page.query_selector(".header-section")
                if element:
                    # Screenshot only the stats card (no empty space)
                    await element.screenshot(path=str(output_path), type="png")
                else:
                    # Fallback to full page if element not found
                    logger.warning(
                        "Header section not found, falling back to full page screenshot"
                    )
                    await page.screenshot(
                        path=str(output_path), full_page=True, type="png"
                    )

                await browser.close()

        finally:
            # Clean up temporary HTML file
            if os.path.exists(temp_html_path):
                os.unlink(temp_html_path)

    async def _get_user_mystats_data(self, interaction: discord.Interaction) -> Dict:
        """Get data needed for mystats generation (header section only)."""
        user_id = str(interaction.user.id)

        # Get or create user
        user_info = self._get_or_create_user(interaction)

        # Get server info
        server_info = self._get_server_info(interaction)

        # Calculate progress
        progress = self._calculate_progress(user_info)

        return {
            "user": user_info,
            "server": server_info,
            "progress": progress,
            "timestamp": self._get_current_timestamp(),
        }

    async def _generate_mystats_async(self, user_data: Dict, user_id: str) -> str:
        """Generate mystats image asynchronously with cropped output."""
        try:
            # Generate unique filename with timestamp
            filename = f"mystats_{user_id}_{int(time.time())}.png"
            output_path = self.output_dir / filename

            # Render template with embedded CSS
            template = self.env.get_template("mystats_standalone.html")
            template_data = {
                **user_data,
                "css_content": self.css_content,  # Embed CSS directly in HTML
            }
            html_content = template.render(**template_data)

            # Generate cropped image (only the stats card, not full page)
            await self._render_mystats_to_image(html_content, output_path)

            return str(output_path)

        except Exception as e:
            logger.error(f"Error generating mystats image: {e}")
            raise


async def setup(bot):
    await bot.add_cog(DashboardCommands(bot))
