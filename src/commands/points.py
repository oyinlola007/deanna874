from discord.ext import commands
from src.core.database import Database

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

        if not dao.user_exists(user_id):
            await ctx.send(f"❌ User with ID {user_id} does not exist.")
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

        if not dao.user_exists(user_id):
            await ctx.send(f"❌ User with ID {user_id} does not exist.")
            return

        amount = int(amount)
        if amount < 1 or amount > 1_000_000_000:
            await ctx.send("❌ Amount must be between 1 and 1,000,000,000.")
            return

        dao.set_user_points(user_id, int(amount))

        # Update user's level and check for role changes
        dao.update_user_level(user_id, int(amount))

        # Check for role assignment/downgrading
        if hasattr(self.bot, "role_manager"):
            await self.bot.role_manager.check_and_assign_roles(user_id, ctx.guild)

        # Update voice channel display
        if hasattr(self.bot, "voice_channel_display"):
            await self.bot.voice_channel_display.update_channel_name(ctx.guild)

        await ctx.send(f"✅ Set points for user ID {user_id} to {amount}.")

    @commands.command()
    @commands.check(lambda ctx: dao.is_admin(str(ctx.author.id)))
    async def addpoints(self, ctx, user_id: str = None, amount: str = None):
        if not user_id or not amount or not user_id.isdigit() or not amount.isdigit():
            await ctx.send("Usage: !addpoints <user_id> <amount>")
            return

        if not dao.user_exists(user_id):
            await ctx.send(f"❌ User with ID {user_id} does not exist.")
            return

        amount = int(amount)
        if amount < 1 or amount > 1_000_000_000:
            await ctx.send("❌ Amount must be between 1 and 1,000,000,000.")
            return

        dao.increment_user_points(user_id, int(amount))

        # Update user's level and check for role changes
        current_points = dao.get_user_points(user_id)
        dao.update_user_level(user_id, current_points)

        # Check for milestone and role assignment
        if hasattr(self.bot, "role_manager"):
            await self.bot.role_manager.check_and_assign_roles(user_id, ctx.guild)

        # Update voice channel display
        if hasattr(self.bot, "voice_channel_display"):
            await self.bot.voice_channel_display.update_channel_name(ctx.guild)

        await ctx.send(f"✅ Added {amount} points to user ID {user_id}.")

    @commands.command()
    @commands.check(lambda ctx: dao.is_admin(str(ctx.author.id)))
    async def removepoints(self, ctx, user_id: str = None, amount: str = None):
        if not user_id or not amount or not user_id.isdigit() or not amount.isdigit():
            await ctx.send("Usage: !removepoints <user_id> <amount>")
            return

        if not dao.user_exists(user_id):
            await ctx.send(f"❌ User with ID {user_id} does not exist.")
            return

        amount = int(amount)
        if amount < 1 or amount > 1_000_000_000:
            await ctx.send("❌ Amount must be between 1 and 1,000,000,000.")
            return

        dao.increment_user_points(user_id, -int(amount))

        # Update user's level and check for role changes
        current_points = dao.get_user_points(user_id)
        dao.update_user_level(user_id, current_points)

        # Check for role assignment/downgrading
        if hasattr(self.bot, "role_manager"):
            await self.bot.role_manager.check_and_assign_roles(user_id, ctx.guild)

        # Update voice channel display
        if hasattr(self.bot, "voice_channel_display"):
            await self.bot.voice_channel_display.update_channel_name(ctx.guild)

        await ctx.send(f"✅ Removed {amount} points from user ID {user_id}.")


async def setup(bot):
    await bot.add_cog(PointsCommands(bot))
