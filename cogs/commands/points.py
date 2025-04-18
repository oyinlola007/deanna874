from discord.ext import commands
from cogs.dao import Database

dao = Database()


class PointsCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.check(lambda ctx: dao.is_admin(str(ctx.author.id)))
    async def resetpoints(self, ctx, user_id: str = None):
        if not user_id or not user_id.isdigit():
            await ctx.send("Usage: !resetpoints <user_id>")
            return
        dao.reset_user_points(user_id)
        await ctx.send(f"✅ Points reset for user ID: {user_id}")

    @commands.command()
    @commands.check(lambda ctx: dao.is_admin(str(ctx.author.id)))
    async def resetallpoints(self, ctx):
        dao.reset_all_points()
        await ctx.send("✅ All user points have been reset.")

    @commands.command()
    @commands.check(lambda ctx: dao.is_admin(str(ctx.author.id)))
    async def setpoints(self, ctx, user_id: str = None, amount: str = None):
        if not user_id or not amount or not user_id.isdigit() or not amount.isdigit():
            await ctx.send("Usage: !setpoints <user_id> <amount>")
            return
        dao.set_user_points(user_id, int(amount))
        await ctx.send(f"✅ Set points for user ID {user_id} to {amount}.")

    @commands.command()
    @commands.check(lambda ctx: dao.is_admin(str(ctx.author.id)))
    async def addpoints(self, ctx, user_id: str = None, amount: str = None):
        if not user_id or not amount or not user_id.isdigit() or not amount.isdigit():
            await ctx.send("Usage: !addpoints <user_id> <amount>")
            return
        dao.increment_user_points(user_id, int(amount))
        await ctx.send(f"✅ Added {amount} points to user ID {user_id}.")

    @commands.command()
    @commands.check(lambda ctx: dao.is_admin(str(ctx.author.id)))
    async def removepoints(self, ctx, user_id: str = None, amount: str = None):
        if not user_id or not amount or not user_id.isdigit() or not amount.isdigit():
            await ctx.send("Usage: !removepoints <user_id> <amount>")
            return
        dao.increment_user_points(user_id, -int(amount))
        await ctx.send(f"✅ Removed {amount} points from user ID {user_id}.")


async def setup(bot):
    await bot.add_cog(PointsCommands(bot))
