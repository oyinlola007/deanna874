import discord
from discord import app_commands
from discord.ext import commands
from src.core.database import Database as dao


class SlashVoiceDisplayCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # All voice display commands have been removed as they are overkill
    # The voice channel display system runs automatically without manual controls


async def setup(bot):
    await bot.add_cog(SlashVoiceDisplayCommands(bot))
