from discord.ext import commands
import discord
from src.core.database import Database

dao = Database()


class TrackingCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.check(lambda ctx: dao.is_admin(str(ctx.author.id)))
    async def trackchannel(self, ctx, channel_id: str = None):
        if not channel_id:
            await ctx.send("Usage: !trackchannel <channel_id>")
            return
        dao.track_channel(channel_id)
        await ctx.send(f"📡 Now tracking channel ID: {channel_id}")

    @commands.command()
    @commands.check(lambda ctx: dao.is_admin(str(ctx.author.id)))
    async def untrackchannel(self, ctx, channel_id: str = None):
        if not channel_id:
            await ctx.send("Usage: !untrackchannel <channel_id>")
            return
        dao.untrack_channel(channel_id)
        await ctx.send(f"📴 Stopped tracking channel ID: {channel_id}")

    @commands.command()
    @commands.check(lambda ctx: dao.is_admin(str(ctx.author.id)))
    async def listtrackedchannels(self, ctx):
        channels = dao.get_tracked_channels()
        if not channels:
            await ctx.send("No tracked channels.")
            return
        await ctx.send("📺 **Tracked Channels:**\n" + "\n".join(channels))


async def setup(bot):
    await bot.add_cog(TrackingCommands(bot))
