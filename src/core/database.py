import sqlite3
from datetime import datetime
from typing import Optional, List, Tuple, Dict
import src.core.config as config

DB_PATH = config.DATABASE_NAME


class Database:
    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path

    def _connect(self):
        return sqlite3.connect(self.db_path)

    def get_config(self, key: str) -> Optional[str]:
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute("SELECT value FROM config WHERE key = ?", (key,))
            result = cur.fetchone()
            return result[0] if result else None

    def set_config(self, key: str, value: str):
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute(
                "INSERT OR REPLACE INTO config (key, value) VALUES (?, ?)", (key, value)
            )
            conn.commit()

    def add_points_to_member(self, discord_id: str, points: int):
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO members (discord_id, total_points, level, current_streak, longest_streak, last_activity_date)
                VALUES (?, ?, 0, 0, 0, date('now', '-1 day'))
                ON CONFLICT(discord_id) DO UPDATE SET total_points = total_points + ?
                """,
                (discord_id, points, points),
            )
            conn.commit()

    def log_engagement(
        self,
        discord_id: str,
        activity_type: str,
        activity_object_id: Optional[str],
        channel_id: Optional[str],
        point_value: int = 0,
    ):
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO engagement_log (discord_id, activity_type, activity_object_id, channel_id, point_value)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    discord_id,
                    activity_type,
                    activity_object_id,
                    channel_id,
                    point_value,
                ),
            )
            conn.commit()

    def has_user_reacted_to_message(self, discord_id: str, message_id: str) -> bool:
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT 1 FROM engagement_log
                WHERE discord_id = ? AND activity_type = 'reaction' AND activity_object_id = ?
            """,
                (discord_id, message_id),
            )
            return cur.fetchone() is not None

    def has_invited_before(self, inviter_id: str, invitee_id: str) -> bool:
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT 1 FROM engagement_log
                WHERE discord_id = ? AND activity_type = 'invite' AND activity_object_id = ?
                """,
                (inviter_id, f"invite_{invitee_id}"),
            )
            return cur.fetchone() is not None

    def get_next_milestone(self, discord_id: str) -> Optional[int]:
        with self._connect() as conn:
            cur = conn.cursor()
            # Fetch all active milestone values
            cur.execute(
                "SELECT value FROM milestones WHERE status = 'active' ORDER BY value ASC"
            )
            milestones = [row[0] for row in cur.fetchall()]

            # Get current points
            points = self.get_user_points(discord_id)

            # Get already recorded milestones
            cur.execute(
                "SELECT milestone FROM milestones_log WHERE discord_id = ?",
                (discord_id,),
            )
            recorded = {row[0] for row in cur.fetchall()}

            # Return the first unrecorded milestone the user qualifies for
            for milestone in milestones:
                if points >= milestone and milestone not in recorded:
                    return milestone

            return None

    def get_next_milestone_by_points(self, current_points: int) -> Optional[int]:
        """Get the next milestone based on current points (for dashboard)."""
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT value FROM milestones WHERE status = 'active' AND value > ? ORDER BY value ASC LIMIT 1",
                (current_points,),
            )
            result = cur.fetchone()
            return result[0] if result else None

    def get_leaderboard(self, limit=10) -> List[Tuple[str, int]]:
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT discord_id, total_points
                FROM members
                WHERE discord_id NOT IN (SELECT discord_id FROM excluded_leaderboard)
                ORDER BY total_points DESC
                LIMIT ?
                """,
                (limit,),
            )
            return cur.fetchall()

    def get_top_users(self, limit=10) -> List[Dict]:
        """Get top members with detailed statistics for leaderboard display."""
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT 
                    m.discord_id,
                    m.total_points,
                    COALESCE(msg_count.count, 0) as messages,
                    COALESCE(reaction_count.count, 0) as reactions,
                    COALESCE(image_count.count, 0) as images,
                    COALESCE(invite_count.count, 0) as invites
                FROM members m
                LEFT JOIN (
                    SELECT discord_id, COUNT(*) as count
                    FROM engagement_log
                    WHERE activity_type = 'message'
                    GROUP BY discord_id
                ) msg_count ON m.discord_id = msg_count.discord_id
                LEFT JOIN (
                    SELECT discord_id, COUNT(*) as count
                    FROM engagement_log
                    WHERE activity_type = 'reaction'
                    GROUP BY discord_id
                ) reaction_count ON m.discord_id = reaction_count.discord_id
                LEFT JOIN (
                    SELECT discord_id, COUNT(*) as count
                    FROM engagement_log
                    WHERE activity_type = 'image'
                    GROUP BY discord_id
                ) image_count ON m.discord_id = image_count.discord_id
                LEFT JOIN (
                    SELECT discord_id, COUNT(*) as count
                    FROM engagement_log
                    WHERE activity_type = 'invite'
                    GROUP BY discord_id
                ) invite_count ON m.discord_id = invite_count.discord_id
                WHERE m.discord_id NOT IN (SELECT discord_id FROM excluded_leaderboard)
                ORDER BY m.total_points DESC
                LIMIT ?
                """,
                (limit,),
            )

            columns = [description[0] for description in cur.description]
            return [dict(zip(columns, row)) for row in cur.fetchall()]

    def record_milestone(self, discord_id: str, milestone: int, reward_code: str):
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO milestones_log (discord_id, milestone, reached_at, user_notified, admin_notified, reward_status, reward_code)
                VALUES (?, ?, ?, 0, 0, 'pending', ?)
                """,
                (discord_id, milestone, datetime.utcnow(), reward_code),
            )
            conn.commit()

    def mark_milestone_user_notified(self, discord_id: str, milestone: int):
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                UPDATE milestones_log
                SET user_notified = 1
                WHERE discord_id = ? AND milestone = ?
                """,
                (discord_id, milestone),
            )
            conn.commit()

    def mark_milestone_admin_notified(self, discord_id: str, milestone: int):
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                UPDATE milestones_log
                SET admin_notified = 1
                WHERE discord_id = ? AND milestone = ?
                """,
                (discord_id, milestone),
            )
            conn.commit()

    def get_user_points(self, discord_id: str) -> int:
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT total_points FROM members WHERE discord_id = ?
                """,
                (discord_id,),
            )
            row = cur.fetchone()
            return row[0] if row else 0

    def get_user_level(self, discord_id: str) -> int:
        """Get user's current level (milestone value)."""
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT level FROM members WHERE discord_id = ?
                """,
                (discord_id,),
            )
            row = cur.fetchone()
            return row[0] if row else 0

    def update_user_level(self, discord_id: str, points: int):
        """Update user's level based on their points and milestone values."""
        with self._connect() as conn:
            cur = conn.cursor()

            # Get all milestone values in descending order
            cur.execute(
                "SELECT value FROM milestones WHERE status = 'active' ORDER BY value DESC"
            )
            milestones = [row[0] for row in cur.fetchall()]

            # Find the highest milestone the user qualifies for
            user_level = 0
            for milestone in milestones:
                if points >= milestone:
                    user_level = milestone
                    break

            # Update the user's level
            cur.execute(
                """
                UPDATE members SET level = ? WHERE discord_id = ?
                """,
                (user_level, discord_id),
            )
            conn.commit()

    def is_admin(self, discord_id: str) -> bool:
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT 1 FROM admin_ids WHERE discord_id = ? AND status = 'active'",
                (discord_id,),
            )
            return cur.fetchone() is not None

    def reset_user_points(self, discord_id: str):
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute(
                "UPDATE members SET total_points = 0 WHERE discord_id = ?",
                (discord_id,),
            )
            conn.commit()

    def reset_all_points(self):
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute("UPDATE members SET total_points = 0")
            cur.execute("DELETE from milestones_log")
            conn.commit()

    def set_user_points(self, discord_id: str, amount: int):
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO members (discord_id, total_points, level, current_streak, longest_streak, last_activity_date)
                VALUES (?, ?, 0, 0, 0, date('now', '-1 day'))
                ON CONFLICT(discord_id) DO UPDATE SET total_points = ?
                """,
                (discord_id, amount, amount),
            )
            conn.commit()

    def increment_user_points(self, discord_id: str, delta: int):
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute(
                """
            INSERT INTO members (discord_id, total_points, level, current_streak, longest_streak, last_activity_date)
            VALUES (?, ?, 0, 0, 0, date('now', '-1 day'))
            ON CONFLICT(discord_id) DO UPDATE SET total_points = total_points + ?
            """,
                (discord_id, delta, delta),
            )
        conn.commit()

    def user_exists(self, discord_id: str) -> bool:
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute("SELECT 1 FROM members WHERE discord_id = ?", (discord_id,))
            return cur.fetchone() is not None

    def update_config(self, key: str, value: str) -> bool:
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute("UPDATE config SET value = ? WHERE key = ?", (value, key))
            conn.commit()
            return cur.rowcount > 0  # True if updated, False if key didn't exist

    def get_all_configs(self) -> Dict[str, str]:
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute("SELECT key, value FROM config")
            return dict(cur.fetchall())

    def get_daily_points(self, discord_id: str) -> int:
        """Get the total points earned by a user in the last 24 hours."""
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT COALESCE(SUM(point_value), 0)
                FROM engagement_log
                WHERE discord_id = ?
                AND timestamp >= datetime('now', '-1 day')
                """,
                (discord_id,),
            )
            return cur.fetchone()[0]

    def can_earn_points(self, discord_id: str, points_to_add: int) -> bool:
        """Check if a user can earn more points today."""
        daily_limit = int(
            self.get_config("daily_points_limit") or config.DEFAULT_DAILY_POINTS_LIMIT
        )
        current_daily_points = self.get_daily_points(discord_id)
        return (current_daily_points + points_to_add) <= daily_limit

    def get_active_milestones(
        self,
    ) -> List[Tuple[int, Optional[str], Optional[str], bool, Optional[str]]]:
        with self._connect() as conn:
            cur = conn.cursor()
            try:
                cur.execute(
                    "SELECT value, message, role_name, is_level_based, reward FROM milestones WHERE status = 'active' ORDER BY value ASC"
                )
                return cur.fetchall()
            except sqlite3.OperationalError:
                # New columns don't exist yet, fall back to old format
                cur.execute(
                    "SELECT value, message FROM milestones WHERE status = 'active' ORDER BY value ASC"
                )
                # Convert to new format with None values for missing columns
                old_results = cur.fetchall()
                return [
                    (value, message, None, True, None) for value, message in old_results
                ]

    def track_channel(self, channel_id: str):
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO tracked_channels (channel_id, status)
                VALUES (?, 'active')
                ON CONFLICT(channel_id) DO UPDATE SET status = 'active'
                """,
                (channel_id,),
            )
            conn.commit()

    def untrack_channel(self, channel_id: str):
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute(
                "UPDATE tracked_channels SET status = 'inactive' WHERE channel_id = ?",
                (channel_id,),
            )
            conn.commit()

    def get_tracked_channels(self) -> List[str]:
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT channel_id FROM tracked_channels WHERE status = 'active'"
            )
            return [row[0] for row in cur.fetchall()]

    def get_all_admin_ids(self) -> List[str]:
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute("SELECT discord_id FROM admin_ids WHERE status = 'active'")
            return [row[0] for row in cur.fetchall()]

    def add_admin(self, discord_id: str):
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO admin_ids (discord_id, status)
                VALUES (?, 'active')
                ON CONFLICT(discord_id) DO UPDATE SET status = 'active'
                """,
                (discord_id,),
            )
            conn.commit()

    def remove_admin(self, discord_id: str):
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute(
                "UPDATE admin_ids SET status = 'inactive' WHERE discord_id = ?",
                (discord_id,),
            )
            conn.commit()

    def is_tracked_channel(self, channel_id: str) -> bool:
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT 1 FROM tracked_channels WHERE channel_id = ? AND status = 'active'",
                (channel_id,),
            )
            return cur.fetchone() is not None

    def mark_reward_given(self, reward_code: str):
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute(
                "UPDATE milestones_log SET reward_status = 'sent' WHERE reward_code = ?",
                (reward_code,),
            )
            conn.commit()
            return cur.rowcount > 0

    def get_unrewarded_milestones(self) -> List[Tuple[str, int, str]]:
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT discord_id, milestone, reward_code 
                FROM milestones_log 
                WHERE reward_status = 'pending' 
                ORDER BY reached_at ASC
                """
            )
            return cur.fetchall()

    def get_milestone_message(self, milestone: int) -> Optional[str]:
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT message FROM milestones WHERE value = ? AND status = 'active'",
                (milestone,),
            )
            result = cur.fetchone()
            return result[0] if result else None

    def get_milestone_details(self, milestone: int) -> Optional[Dict]:
        with self._connect() as conn:
            cur = conn.cursor()
            try:
                cur.execute(
                    "SELECT value, message, role_name, is_level_based, reward FROM milestones WHERE value = ? AND status = 'active'",
                    (milestone,),
                )
                result = cur.fetchone()
                if result:
                    return {
                        "value": result[0],
                        "message": result[1],
                        "role_name": result[2],
                        "is_level_based": result[3],
                        "reward": result[4],
                    }
                return None
            except sqlite3.OperationalError:
                # Fall back to old format if reward column doesn't exist
                cur.execute(
                    "SELECT value, message, role_name, is_level_based FROM milestones WHERE value = ? AND status = 'active'",
                    (milestone,),
                )
                result = cur.fetchone()
                if result:
                    return {
                        "value": result[0],
                        "message": result[1],
                        "role_name": result[2],
                        "is_level_based": result[3],
                        "reward": None,
                    }
                return None

    def update_milestone_message(self, milestone: int, message: str) -> bool:
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute(
                "UPDATE milestones SET message = ? WHERE value = ?",
                (message, milestone),
            )
            conn.commit()
            return cur.rowcount > 0

    def add_milestone(
        self,
        value: int,
        message: Optional[str],
        role_name: Optional[str] = None,
        is_level_based: bool = True,
        reward: Optional[str] = None,
    ) -> bool:
        with self._connect() as conn:
            cur = conn.cursor()
            try:
                cur.execute(
                    """
                    INSERT OR REPLACE INTO milestones (value, status, message, role_name, is_level_based, reward) 
                    VALUES (?, 'active', ?, ?, ?, ?)
                    """,
                    (value, message, role_name, is_level_based, reward),
                )
                conn.commit()
                return True
            except sqlite3.OperationalError:
                # Fall back to old format if reward column doesn't exist
                cur.execute(
                    """
                    INSERT OR REPLACE INTO milestones (value, status, message, role_name, is_level_based) 
                    VALUES (?, 'active', ?, ?, ?)
                    """,
                    (value, message, role_name, is_level_based),
                )
                conn.commit()
                return True

    def update_milestone_status(self, value: int, status: str) -> bool:
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute(
                "UPDATE milestones SET status = ? WHERE value = ?",
                (status, value),
            )
            conn.commit()
            return cur.rowcount > 0

    def update_milestone_role(self, value: int, role_name: str) -> bool:
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute(
                "UPDATE milestones SET role_name = ? WHERE value = ?",
                (role_name, value),
            )
            conn.commit()
            return cur.rowcount > 0

    def update_milestone_reward(self, value: int, reward: str) -> bool:
        with self._connect() as conn:
            cur = conn.cursor()
            try:
                cur.execute(
                    "UPDATE milestones SET reward = ? WHERE value = ?",
                    (reward, value),
                )
                conn.commit()
                return cur.rowcount > 0
            except sqlite3.OperationalError:
                # Reward column doesn't exist yet
                return False

    def get_milestone_role(self, milestone: int) -> Optional[str]:
        """Get the role name for a specific milestone."""
        with self._connect() as conn:
            cur = conn.cursor()
            try:
                cur.execute(
                    "SELECT role_name FROM milestones WHERE value = ? AND status = 'active'",
                    (milestone,),
                )
                row = cur.fetchone()
                return row[0] if row and row[0] else None
            except sqlite3.OperationalError:
                # role_name column doesn't exist yet (migration not complete)
                return None

    def get_user_current_role_milestone(self, discord_id: str) -> Optional[int]:
        """Get the milestone value for the user's current role (if any)."""
        with self._connect() as conn:
            cur = conn.cursor()
            try:
                cur.execute(
                    """
                    SELECT m.value 
                    FROM milestones m 
                    WHERE m.role_name IS NOT NULL 
                    AND m.value <= (SELECT level FROM members WHERE discord_id = ?)
                    AND m.status = 'active'
                    ORDER BY m.value DESC 
                    LIMIT 1
                    """,
                    (discord_id,),
                )
                row = cur.fetchone()
                return row[0] if row else None
            except sqlite3.OperationalError:
                # role_name column doesn't exist yet (migration not complete)
                return None

    def get_user_milestone_role_name(self, discord_id: str) -> Optional[str]:
        """Get the user's current milestone role name, if any."""
        current_points = self.get_user_points(discord_id)

        try:
            with self._connect() as conn:
                cur = conn.cursor()
                cur.execute(
                    """
                    SELECT role_name 
                    FROM milestones 
                    WHERE status = 'active' 
                    AND role_name IS NOT NULL 
                    AND value <= ? 
                    ORDER BY value DESC 
                    LIMIT 1
                    """,
                    (current_points,),
                )
                row = cur.fetchone()
                return row[0] if row else None
        except sqlite3.OperationalError:
            return None

    def get_all_role_milestones(self) -> List[Tuple[int, str]]:
        """Get all milestones that have roles assigned."""
        with self._connect() as conn:
            cur = conn.cursor()
            try:
                cur.execute(
                    "SELECT value, role_name FROM milestones WHERE role_name IS NOT NULL AND status = 'active' ORDER BY value ASC"
                )
                return cur.fetchall()
            except sqlite3.OperationalError:
                # role_name column doesn't exist yet (migration not complete)
                return []

    def add_excluded_leaderboard_user(self, discord_id: str) -> bool:
        with self._connect() as conn:
            cur = conn.cursor()
            try:
                cur.execute(
                    "INSERT INTO excluded_leaderboard (discord_id) VALUES (?)",
                    (discord_id,),
                )
                conn.commit()
                return True
            except sqlite3.IntegrityError:
                return False  # already excluded

    def remove_excluded_leaderboard_user(self, discord_id: str) -> bool:
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute(
                "DELETE FROM excluded_leaderboard WHERE discord_id = ?",
                (discord_id,),
            )
            conn.commit()
            return cur.rowcount > 0

    def get_excluded_leaderboard_users(self) -> List[str]:
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute("SELECT discord_id FROM excluded_leaderboard")
            return [row[0] for row in cur.fetchall()]

    # Streak tracking functions
    def get_current_streak(self, discord_id: str) -> int:
        """Get user's current streak."""
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT current_streak FROM members WHERE discord_id = ?",
                (discord_id,),
            )
            row = cur.fetchone()
            return row[0] if row else 0

    def get_longest_streak(self, discord_id: str) -> int:
        """Get user's longest streak."""
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT longest_streak FROM members WHERE discord_id = ?",
                (discord_id,),
            )
            row = cur.fetchone()
            return row[0] if row else 0

    def update_streak(self, discord_id: str, activity_date: str = None):
        """
        Update user's streak based on activity.
        If activity_date is provided, use it; otherwise use current date.
        """
        if not activity_date:
            from datetime import date

            activity_date = date.today().isoformat()

        with self._connect() as conn:
            cur = conn.cursor()

            # Get user's last activity date and current streak
            cur.execute(
                "SELECT last_activity_date, current_streak, longest_streak FROM members WHERE discord_id = ?",
                (discord_id,),
            )
            row = cur.fetchone()

            if not row:
                # User doesn't exist, create them with streak 1
                cur.execute(
                    """
                    INSERT INTO members (discord_id, last_activity_date, current_streak, longest_streak)
                    VALUES (?, ?, 1, 1)
                    """,
                    (discord_id, activity_date),
                )
            else:
                last_activity_date, current_streak, longest_streak = row

                if last_activity_date == activity_date:
                    # User already active today, no change needed
                    return

                # Check if this is consecutive activity
                from datetime import datetime, timedelta

                try:
                    last_date = datetime.strptime(last_activity_date, "%Y-%m-%d").date()
                    current_date = datetime.strptime(activity_date, "%Y-%m-%d").date()

                    if current_date - last_date == timedelta(days=1):
                        # Consecutive day, increment streak
                        new_streak = current_streak + 1
                        new_longest = max(longest_streak, new_streak)
                    else:
                        # Non-consecutive day, reset streak
                        new_streak = 1
                        new_longest = longest_streak

                except (ValueError, TypeError):
                    # Invalid date format, treat as new streak
                    new_streak = 1
                    new_longest = max(longest_streak, 1)

                # Update streak and last activity
                cur.execute(
                    """
                    UPDATE members 
                    SET current_streak = ?, longest_streak = ?, last_activity_date = ?
                    WHERE discord_id = ?
                    """,
                    (new_streak, new_longest, activity_date, discord_id),
                )

            conn.commit()

    def get_streak(self, discord_id: str) -> int:
        """Get user's current streak (alias for get_current_streak for compatibility)."""
        return self.get_current_streak(discord_id)

    # Voice channel display functions
    def save_voice_channel_display(self, guild_id: str, channel_ids: list):
        """Save voice channel display channel IDs for a guild."""
        with self._connect() as conn:
            cur = conn.cursor()
            # Delete existing entries for this guild
            cur.execute(
                "DELETE FROM voice_channel_display WHERE guild_id = ?", (guild_id,)
            )

            # Insert new channel IDs
            for i, channel_id in enumerate(channel_ids):
                cur.execute(
                    "INSERT INTO voice_channel_display (guild_id, channel_id, position) VALUES (?, ?, ?)",
                    (guild_id, channel_id, i),
                )
            conn.commit()

    def get_voice_channel_display(self, guild_id: str) -> list:
        """Get voice channel display channel IDs for a guild."""
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT channel_id FROM voice_channel_display WHERE guild_id = ? ORDER BY position ASC",
                (guild_id,),
            )
            return [row[0] for row in cur.fetchall()]

    def delete_voice_channel_display(self, guild_id: str):
        """Delete voice channel display entries for a guild."""
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute(
                "DELETE FROM voice_channel_display WHERE guild_id = ?", (guild_id,)
            )
            conn.commit()

    # Campaign channel functions
    def add_campaign_channel(
        self,
        channel_id: str,
        campaign_name: str,
        multiplier: float,
        start_date: str,
        end_date: str,
    ):
        """Add a campaign channel with multiplier."""
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT OR REPLACE INTO campaign_channels 
                (channel_id, campaign_name, multiplier, start_date, end_date, status)
                VALUES (?, ?, ?, ?, ?, 'active')
                """,
                (channel_id, campaign_name, multiplier, start_date, end_date),
            )

            # Automatically add to tracked channels
            cur.execute(
                """
                INSERT OR IGNORE INTO tracked_channels (channel_id, status)
                VALUES (?, 'active')
                """,
                (channel_id,),
            )
            conn.commit()

    def get_campaign_multiplier(self, channel_id: str) -> float:
        """Get the campaign multiplier for a channel if it's an active campaign."""
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT multiplier FROM campaign_channels 
                WHERE channel_id = ? AND status = 'active'
                AND date('now') BETWEEN start_date AND end_date
                """,
                (channel_id,),
            )
            row = cur.fetchone()
            return row[0] if row else 1.0

    def get_active_campaigns(self) -> list:
        """Get all active campaigns."""
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT channel_id, campaign_name, multiplier, start_date, end_date 
                FROM campaign_channels 
                WHERE status = 'active' AND date('now') BETWEEN start_date AND end_date
                ORDER BY start_date ASC
                """
            )
            return cur.fetchall()

    def get_all_campaigns(self) -> list:
        """Get all campaigns (active and inactive)."""
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT channel_id, campaign_name, multiplier, start_date, end_date, status
                FROM campaign_channels 
                ORDER BY start_date DESC
                """
            )
            return cur.fetchall()

    def update_campaign_status(self, channel_id: str, status: str):
        """Update campaign status (active/inactive)."""
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute(
                "UPDATE campaign_channels SET status = ? WHERE channel_id = ?",
                (status, channel_id),
            )
            conn.commit()

    def delete_campaign_channel(self, channel_id: str) -> bool:
        """Delete a campaign channel."""
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute(
                "DELETE FROM campaign_channels WHERE channel_id = ?", (channel_id,)
            )
            conn.commit()
            return cur.rowcount > 0

    def is_campaign_channel(self, channel_id: str) -> bool:
        """Check if a channel is a campaign channel."""
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT 1 FROM campaign_channels WHERE channel_id = ? AND status = 'active'",
                (channel_id,),
            )
            return cur.fetchone() is not None

    def get_member_info(self, discord_id: str) -> Optional[Dict]:
        """Get member information including all fields."""
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT discord_id, total_points, level, current_streak, longest_streak, last_activity_date
                FROM members 
                WHERE discord_id = ?
                """,
                (discord_id,),
            )
            result = cur.fetchone()
            if result:
                return {
                    "discord_id": result[0],
                    "total_points": result[1],
                    "level": result[2],
                    "current_streak": result[3],
                    "longest_streak": result[4],
                    "last_activity_date": result[5],
                }
            return None

    def add_member(self, discord_id: str, points: int = 0):
        """Add a new member to the database."""
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO members (discord_id, total_points, level, current_streak, longest_streak, last_activity_date)
                VALUES (?, ?, 1, 0, 0, date('now', '-1 day'))
                """,
                (discord_id, points),
            )
            conn.commit()

    def get_user_rank(self, discord_id: str) -> int:
        """Get user's rank in the leaderboard."""
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT COUNT(*) + 1
                FROM members m1
                WHERE m1.total_points > (
                    SELECT COALESCE(m2.total_points, 0)
                    FROM members m2
                    WHERE m2.discord_id = ?
                )
                """,
                (discord_id,),
            )
            result = cur.fetchone()
            return result[0] if result else 1

    def get_total_members_count(self) -> int:
        """Get total number of members in the database."""
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM members")
            result = cur.fetchone()
            return result[0] if result else 0

    def get_previous_milestone(self, discord_id: str) -> Optional[int]:
        """Get the previous milestone for a user."""
        with self._connect() as conn:
            cur = conn.cursor()
            # Get user's current points
            cur.execute(
                "SELECT total_points FROM members WHERE discord_id = ?",
                (discord_id,),
            )
            result = cur.fetchone()
            if not result:
                return None

            current_points = result[0]

            # Get the highest milestone that's less than current points
            cur.execute(
                """
                SELECT value FROM milestones 
                WHERE value <= ? AND status = 'active'
                ORDER BY value DESC 
                LIMIT 1
                """,
                (current_points,),
            )
            result = cur.fetchone()
            return result[0] if result else 0
