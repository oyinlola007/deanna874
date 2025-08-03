import discord
from discord.ext import commands
from src.core.database import Database
import logging
from typing import List, Optional

logger = logging.getLogger(__name__)
dao = Database()


class RoleManager:
    """Handles automatic role assignment based on user levels."""

    def __init__(self, bot):
        self.bot = bot

    async def _remove_all_level_roles(
        self, member: discord.Member, guild: discord.Guild
    ) -> List[discord.Role]:
        """Remove all level-based roles from a member. Returns list of removed roles."""
        removed_roles = []
        all_role_milestones = dao.get_all_role_milestones()

        logger.info(f"Checking for level roles to remove from {member.display_name}")
        logger.info(f"Available role milestones: {all_role_milestones}")
        logger.info(f"User's current roles: {[r.name for r in member.roles]}")

        for milestone, role_name in all_role_milestones:
            if role_name:
                role = discord.utils.get(guild.roles, name=role_name)
                logger.info(
                    f"Looking for role '{role_name}' - found: {role is not None}"
                )
                if role and role in member.roles:
                    removed_roles.append(role)
                    logger.info(f"Will remove role: {role.name}")

        if removed_roles:
            try:
                await member.remove_roles(
                    *removed_roles, reason="Level-based role cleanup"
                )
                logger.info(
                    f"Removed roles {[r.name for r in removed_roles]} from {member.display_name}"
                )
            except discord.Forbidden:
                logger.error(
                    f"Bot doesn't have permission to remove roles from {member.display_name}"
                )
            except Exception as e:
                logger.error(f"Error removing roles from {member.display_name}: {e}")
        else:
            logger.info(f"No level roles to remove from {member.display_name}")

        return removed_roles

    async def _get_target_role_for_level(
        self, current_level: int, guild: discord.Guild
    ) -> Optional[discord.Role]:
        """Get the role that should be assigned for the current level."""
        # Get all role milestones in descending order to find highest qualifying
        all_role_milestones = dao.get_all_role_milestones()
        all_role_milestones.sort(
            key=lambda x: x[0], reverse=True
        )  # Sort by milestone value descending

        for milestone, role_name in all_role_milestones:
            if role_name and current_level >= milestone:
                return discord.utils.get(guild.roles, name=role_name)

        return None

    async def _assign_highest_qualifying_role(
        self, member: discord.Member, guild: discord.Guild, current_level: int
    ) -> List[discord.Role]:
        """Assign the highest qualifying role based on current level. Returns list of added roles."""
        added_roles = []

        target_role = await self._get_target_role_for_level(current_level, guild)
        if target_role and target_role not in member.roles:
            added_roles.append(target_role)
            try:
                await member.add_roles(
                    target_role, reason="Level-based role assignment"
                )
                logger.info(f"Added role {target_role.name} to {member.display_name}")
            except discord.Forbidden:
                logger.error(
                    f"Bot doesn't have permission to add roles to {member.display_name}"
                )
            except Exception as e:
                logger.error(f"Error adding roles to {member.display_name}: {e}")

        return added_roles

    async def check_and_assign_roles(
        self, discord_id: str, guild: discord.Guild
    ) -> bool:
        """
        Check if user's level has changed and assign/remove roles accordingly.
        Returns True if roles were changed, False otherwise.
        """
        try:
            # Get user's current level
            current_level = dao.get_user_level(discord_id)
            logger.info(f"Checking roles for user {discord_id}, level: {current_level}")

            if current_level == 0:
                logger.info(f"User {discord_id} has level 0, removing all level roles")
                # Even with level 0, we should remove any existing level roles
                member = guild.get_member(int(discord_id))
                if member:
                    removed_roles = await self._remove_all_level_roles(member, guild)
                    return len(removed_roles) > 0
                return False

            # Get the member object
            member = guild.get_member(int(discord_id))
            if not member:
                logger.warning(f"Member {discord_id} not found in guild {guild.id}")
                return False

            # Get the target role for current level
            target_role = await self._get_target_role_for_level(current_level, guild)

            # Get all level-based roles the user currently has
            all_role_milestones = dao.get_all_role_milestones()
            current_level_roles = []
            for milestone, role_name in all_role_milestones:
                if role_name:
                    role = discord.utils.get(guild.roles, name=role_name)
                    if role and role in member.roles:
                        current_level_roles.append(role)

            # Check if changes are needed
            roles_to_remove = []
            roles_to_add = []

            # Remove roles that shouldn't be there
            for role in current_level_roles:
                if role != target_role:
                    roles_to_remove.append(role)

            # Add target role if user doesn't have it
            if target_role and target_role not in member.roles:
                roles_to_add.append(target_role)

            # Apply changes only if needed
            if roles_to_remove or roles_to_add:
                try:
                    if roles_to_remove:
                        await member.remove_roles(
                            *roles_to_remove, reason="Level-based role cleanup"
                        )
                        logger.info(
                            f"Removed roles {[r.name for r in roles_to_remove]} from {member.display_name}"
                        )

                    if roles_to_add:
                        await member.add_roles(
                            *roles_to_add, reason="Level-based role assignment"
                        )
                        logger.info(
                            f"Added roles {[r.name for r in roles_to_add]} to {member.display_name}"
                        )

                    return True

                except discord.Forbidden:
                    logger.error(
                        f"Bot doesn't have permission to manage roles for {member.display_name}"
                    )
                    return False
                except Exception as e:
                    logger.error(f"Error managing roles for {member.display_name}: {e}")
                    return False

            return False

        except Exception as e:
            logger.error(f"Error in check_and_assign_roles for {discord_id}: {e}")
            return False

    async def assign_roles_for_all_members(self, guild: discord.Guild) -> dict:
        """
        Check and assign roles for all members in the guild.
        Returns a summary of changes made.
        """
        summary = {
            "total_checked": 0,
            "roles_added": 0,
            "roles_removed": 0,
            "errors": 0,
        }

        try:
            # Get all members from database (including those with level 0 who might have roles to remove)
            with dao._connect() as conn:
                cur = conn.cursor()
                cur.execute("SELECT discord_id FROM members")
                member_ids = [row[0] for row in cur.fetchall()]

            logger.info(
                f"Starting bulk role assignment for {guild.name} - {len(member_ids)} members to check"
            )

            for discord_id in member_ids:
                summary["total_checked"] += 1
                try:
                    member = guild.get_member(int(discord_id))
                    if member:
                        current_level = dao.get_user_level(discord_id)
                        logger.info(
                            f"Processing member {member.display_name} (ID: {discord_id}) - Level: {current_level}"
                        )

                        # Handle level 0 users - remove all level roles
                        if current_level == 0:
                            removed_roles = await self._remove_all_level_roles(
                                member, guild
                            )
                            added_roles = []
                        else:
                            # Use the same modular approach as individual role assignment
                            removed_roles = await self._remove_all_level_roles(
                                member, guild
                            )
                            added_roles = await self._assign_highest_qualifying_role(
                                member, guild, current_level
                            )

                        summary["roles_removed"] += len(removed_roles)
                        summary["roles_added"] += len(added_roles)

                        if removed_roles or added_roles:
                            logger.info(
                                f"Member {member.display_name}: Removed {len(removed_roles)} roles, Added {len(added_roles)} roles"
                            )

                except Exception as e:
                    logger.error(f"Error processing member {discord_id}: {e}")
                    summary["errors"] += 1

            return summary

        except Exception as e:
            logger.error(f"Error in bulk role assignment: {e}")
            summary["errors"] += 1
            return summary


async def setup(bot):
    """Add the role manager to the bot."""
    bot.role_manager = RoleManager(bot)
    logger.info("Role manager initialized")
