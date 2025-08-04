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


class SlashLeaderboardCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.dao = Database()

        # Setup paths and environment
        self._setup_leaderboard_environment()

    def _setup_leaderboard_environment(self):
        """Initialize leaderboard generation environment."""
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
        name="ttp-leaderboard", description="Generate the top 10 traders leaderboard"
    )
    async def leaderboard(self, interaction: discord.Interaction):
        """Generate a leaderboard image showing top 10 users."""
        await interaction.response.defer(ephemeral=False)

        try:
            user_id = str(interaction.user.id)

            # Check if guild is available
            if not interaction.guild:
                await interaction.followup.send(
                    "❌ This command can only be used in a server.",
                    ephemeral=False,
                )
                return

            # Generate fresh leaderboard data
            leaderboard_data = await self._get_leaderboard_data(interaction)

            # Generate image and upload
            image_path = await self._generate_leaderboard_async(
                leaderboard_data, user_id
            )

            # Send the image and delete local file
            await self._send_and_cleanup(interaction, image_path)

        except Exception as e:
            logger.error(f"Error generating leaderboard for {interaction.user.id}: {e}")
            await interaction.followup.send(
                "❌ Sorry, there was an error generating the leaderboard. Please try again later.",
                ephemeral=False,
            )

    async def _send_and_cleanup(
        self, interaction: discord.Interaction, image_path: str
    ):
        """Send leaderboard image and delete local file."""
        try:
            # Send the image
            file = discord.File(image_path, filename="leaderboard.png")
            await interaction.followup.send(file=file, ephemeral=False)
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

    async def _get_leaderboard_data(self, interaction: discord.Interaction) -> Dict:
        """Get data needed for leaderboard generation."""
        user_id = str(interaction.user.id)

        # Get top 10 users from database
        top_users = self.dao.get_top_users(limit=10)

        # Get current user's data to mark them in the leaderboard
        current_user_data = None

        # Format leaderboard data
        leaderboard = []
        for user in top_users:
            # Get user's Discord member object for avatar and role
            member = None
            if interaction.guild:
                try:
                    member = interaction.guild.get_member(int(user["discord_id"]))
                except (ValueError, AttributeError) as e:
                    logger.warning(f"Error getting member {user['discord_id']}: {e}")
                    member = None

            user_data = {
                "user_id": user["discord_id"],
                "username": (
                    member.display_name if member else f"User{user['discord_id']}"
                ),
                "avatar_url": member.avatar.url if member and member.avatar else None,
                "messages": user.get("messages", 0),
                "reactions": user.get("reactions", 0),
                "images": user.get("images", 0),
                "invites": user.get("invites", 0),
                "total_xp": user.get("total_points", 0),
                "is_current_user": user["discord_id"] == user_id,
            }

            leaderboard.append(user_data)

            # Store current user's data
            if user["discord_id"] == user_id:
                current_user_data = user_data

        return {
            "leaderboard": leaderboard,
            "current_user": current_user_data,
            "server_name": (
                interaction.guild.name if interaction.guild else "Discord Server"
            ),
            "timestamp": self._get_current_timestamp(),
        }

    def _get_current_timestamp(self) -> str:
        """Get current timestamp for display."""
        from datetime import datetime

        return datetime.now().strftime("%B %d, %Y at %I:%M %p")

    async def _generate_leaderboard_async(
        self, leaderboard_data: Dict, user_id: str
    ) -> str:
        """Generate leaderboard image asynchronously with cropped output."""
        try:
            # Generate unique filename with timestamp
            filename = f"leaderboard_{user_id}_{int(time.time())}.png"
            output_path = self.output_dir / filename

            # Render template with embedded CSS
            template = self.env.get_template("leaderboard_standalone.html")
            template_data = {
                **leaderboard_data,
                "css_content": self.css_content,  # Embed CSS directly in HTML
            }
            html_content = template.render(**template_data)

            # Generate cropped image (only the leaderboard table, not full page)
            await self._render_leaderboard_to_image(html_content, output_path)

            return str(output_path)

        except Exception as e:
            logger.error(f"Error generating leaderboard image: {e}")
            raise

    async def _render_leaderboard_to_image(self, html_content: str, output_path: Path):
        """Render leaderboard HTML content to cropped image using Playwright.

        This function captures only the leaderboard container instead of
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

                # Crop to just the leaderboard container element
                element = await page.query_selector(".leaderboard-container")
                if element:
                    # Screenshot only the leaderboard (no empty space)
                    await element.screenshot(path=str(output_path), type="png")
                else:
                    # Fallback to full page if element not found
                    logger.warning(
                        "Leaderboard container not found, falling back to full page screenshot"
                    )
                    await page.screenshot(
                        path=str(output_path), full_page=True, type="png"
                    )

                await browser.close()
        except Exception as e:
            logger.error(f"Playwright browser error: {e}")
            raise

        finally:
            # Clean up temporary HTML file
            if os.path.exists(temp_html_path):
                os.unlink(temp_html_path)


async def setup(bot):
    await bot.add_cog(SlashLeaderboardCommands(bot))
