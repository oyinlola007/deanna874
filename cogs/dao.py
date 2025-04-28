import sqlite3
from datetime import datetime
from typing import Optional, List, Tuple, Dict
import cogs.config as config

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
                INSERT INTO members (discord_id, total_points)
                VALUES (?, ?)
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

    def get_leaderboard(self, limit=10) -> List[Tuple[str, int]]:
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT discord_id, total_points
                FROM members
                ORDER BY total_points DESC
                LIMIT ?
                """,
                (limit,),
            )
            return cur.fetchall()

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
            conn.commit()

    def set_user_points(self, discord_id: str, amount: int):
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO members (discord_id, total_points)
                VALUES (?, ?)
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
            INSERT INTO members (discord_id, total_points)
            VALUES (?, ?)
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
            return {key: value for key, value in cur.fetchall()}

    def get_active_milestones(self) -> List[int]:
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT value FROM milestones WHERE status = 'active' ORDER BY value ASC"
            )
            return [row[0] for row in cur.fetchall()]

    def get_active_milestones(self) -> List[Tuple[int, Optional[str]]]:
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT value, message FROM milestones WHERE status = 'active' ORDER BY value ASC"
            )
            return cur.fetchall()

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
            """
            )
            return cur.fetchall()

    def get_milestone_message(self, milestone: int) -> Optional[str]:
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute("SELECT message FROM milestones WHERE value = ?", (milestone,))
            row = cur.fetchone()
            return row[0] if row else None

    def update_milestone_message(self, milestone: int, message: str) -> bool:
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute(
                "UPDATE milestones SET message = ? WHERE value = ?",
                (message, milestone),
            )
            conn.commit()
            return cur.rowcount > 0

    def add_milestone(self, value: int, message: Optional[str]) -> bool:
        with self._connect() as conn:
            cur = conn.cursor()
            try:
                cur.execute(
                    "INSERT INTO milestones (value, status, message) VALUES (?, 'active', ?)",
                    (value, message),
                )
                conn.commit()
                return True
            except sqlite3.IntegrityError:
                return False  # milestone already exists
