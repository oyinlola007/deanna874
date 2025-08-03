#!/usr/bin/env python3
"""
Database Migration Manager
Handles versioned migrations to ensure they only run once
"""

import sqlite3
import os
import shutil
from datetime import datetime
from typing import List, Tuple, Callable
import src.core.config as config


class MigrationManager:
    """Manages database migrations with versioning."""

    def __init__(self, db_path: str = config.DATABASE_NAME):
        self.db_path = db_path
        self.migrations: List[Tuple[str, str, Callable]] = []
        self._register_migrations()

    def _register_migrations(self):
        """Register all available migrations."""
        # Migration 2.0 - Add level-based features
        self.migrations.append(
            ("2.0", "Add level-based features and role management", self._migrate_to_v2)
        )
        # Add future migrations here
        # self.migrations.append(("3.0", "Future migration description", self._migrate_to_v3))

    def get_current_version(self) -> str:
        """Get the current database version."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT value FROM config WHERE key = 'database_version'"
                )
                result = cursor.fetchone()
                return result[0] if result else "1.0"
        except Exception:
            return "1.0"

    def set_version(self, version: str):
        """Set the database version."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT OR REPLACE INTO config (key, value) VALUES (?, ?)",
                ("database_version", version),
            )
            conn.commit()

    def backup_database(self) -> str:
        """Create a backup of the current database."""
        if os.path.exists(self.db_path):
            backup_name = (
                f"{self.db_path}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            )
            shutil.copy2(self.db_path, backup_name)
            print(f"✅ Database backed up to: {backup_name}")
            return backup_name
        return None

    def _migrate_to_v2(self) -> bool:
        """Migration to version 2.0 - Add level-based features."""
        print("🔄 Running migration to version 2.0...")

        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # 1. Add columns to existing tables
                print("1️⃣ Adding columns to existing tables...")

                # Add columns to members table
                self._add_column_if_not_exists(
                    cursor, "members", "level", "INTEGER DEFAULT 1"
                )
                self._add_column_if_not_exists(
                    cursor, "members", "current_streak", "INTEGER DEFAULT 0"
                )
                self._add_column_if_not_exists(
                    cursor, "members", "longest_streak", "INTEGER DEFAULT 0"
                )
                self._add_column_if_not_exists(
                    cursor, "members", "last_activity_date", "DATE"
                )

                # Add columns to milestones table
                self._add_column_if_not_exists(
                    cursor, "milestones", "role_name", "TEXT"
                )
                self._add_column_if_not_exists(
                    cursor, "milestones", "is_level_based", "BOOLEAN DEFAULT 0"
                )
                self._add_column_if_not_exists(cursor, "milestones", "reward", "TEXT")

                # Add column to engagement_log table
                self._add_column_if_not_exists(
                    cursor,
                    "engagement_log",
                    "campaign_multiplier",
                    "DECIMAL(3,2) DEFAULT 1.0",
                )

                # 2. Create new tables
                print("2️⃣ Creating new tables...")

                # Create campaign_channels table
                self._create_table_if_not_exists(
                    cursor,
                    "campaign_channels",
                    """
                    CREATE TABLE campaign_channels (
                        channel_id TEXT PRIMARY KEY,
                        multiplier DECIMAL(3,2) DEFAULT 1.0,
                        campaign_name TEXT,
                        start_date DATETIME,
                        end_date DATETIME,
                        status TEXT DEFAULT 'active'
                    )
                """,
                )

                # Create voice_channel_display table
                self._create_table_if_not_exists(
                    cursor,
                    "voice_channel_display",
                    """
                    CREATE TABLE voice_channel_display (
                        guild_id TEXT,
                        channel_id TEXT,
                        position INTEGER,
                        PRIMARY KEY (guild_id, position)
                    )
                """,
                )

                # 3. Create indexes
                print("3️⃣ Creating performance indexes...")
                self._create_index_if_not_exists(
                    cursor, "idx_members_level", "members(level)"
                )
                self._create_index_if_not_exists(
                    cursor, "idx_members_streak", "members(current_streak)"
                )
                self._create_index_if_not_exists(
                    cursor,
                    "idx_engagement_campaign",
                    "engagement_log(campaign_multiplier)",
                )
                self._create_index_if_not_exists(
                    cursor, "idx_milestones_level", "milestones(is_level_based, value)"
                )

                # 4. Insert default data
                print("4️⃣ Inserting default data...")

                # Add new config values
                new_configs = {
                    "level_roles_enabled": "true",
                    "voice_channel_display_enabled": "true",
                    "campaign_system_enabled": "true",
                    "default_level_multiplier": "1.0",
                    "streak_bonus_enabled": "true",
                    "dashboard_enabled": "true",
                    "mystats_enabled": "true",
                    "auto_assign_roles_on_startup": "true",
                }

                for key, value in new_configs.items():
                    cursor.execute(
                        "INSERT OR IGNORE INTO config (key, value) VALUES (?, ?)",
                        (key, value),
                    )

                # Add level-based milestones with rewards
                level_milestones = [
                    (
                        1000,
                        "active",
                        '😊 Congrats! You\'ve reached 1,000 points and unlocked the special "Pit Novice" role!',
                        "Pit Novice",
                        1,
                        'Beginner Trader Badge - Unlock a special Discord role "Pit Novice"',
                    ),
                    (
                        5000,
                        "active",
                        "💥 You're on fire! You've hit 5,000 points and receive a 5% discount! (prime challenges excluding 5K)",
                        None,
                        1,
                        "5% discount (prime challenges excluding 5K)",
                    ),
                    (
                        10000,
                        "active",
                        "(US participants will receive Futures accounts)\n🤯 Incredible! You've reached 10,000 points!",
                        None,
                        1,
                        "10 10K CFD accounts\n(US participants will receive Futures accounts)",
                    ),
                    (
                        15000,
                        "active",
                        "🎉 Well done! You've hit 15,000 points and earned a 15% discount!",
                        None,
                        1,
                        "15% discount",
                    ),
                    (
                        25000,
                        "active",
                        "💼 Big moves! 25,000 points unlocked a 20% discount + a 20% Eshop voucher!",
                        None,
                        1,
                        "20% discount + 20% Eshop voucher\nNote: some regions might be eligible for discounts etc",
                    ),
                    (
                        40000,
                        "active",
                        "🙌 You've crushed it! At 40,000 points, you've earned a TTP hoodie and a 30% voucher!",
                        None,
                        1,
                        "Hoodie + 30% voucher",
                    ),
                    (
                        50000,
                        "active",
                        '👑 Legendary! 50,000 points reached — you\'ve earned a free 50,000 CFD account and the coveted "TTP Superfan" role!',
                        "TTP Superfan",
                        1,
                        'Free account + special Discord role "TTP Superfan"',
                    ),
                ]

                for (
                    value,
                    status,
                    message,
                    role_name,
                    is_level_based,
                    reward,
                ) in level_milestones:
                    cursor.execute(
                        """
                        INSERT OR REPLACE INTO milestones (value, status, message, role_name, is_level_based, reward) 
                        VALUES (?, ?, ?, ?, ?, ?)
                    """,
                        (value, status, message, role_name, is_level_based, reward),
                    )

                # 5. Update existing members with default values
                print("5️⃣ Updating existing members...")

                cursor.execute(
                    """
                    UPDATE members 
                    SET level = CASE 
                        WHEN total_points >= 50000 THEN 50000
                        WHEN total_points >= 40000 THEN 40000
                        WHEN total_points >= 25000 THEN 25000
                        WHEN total_points >= 15000 THEN 15000
                        WHEN total_points >= 10000 THEN 10000
                        WHEN total_points >= 5000 THEN 5000
                        WHEN total_points >= 1000 THEN 1000
                        ELSE 0
                    END,
                    last_activity_date = date('now', '-1 day')
                    WHERE level IS NULL OR level = 1
                """
                )

                updated_count = cursor.rowcount
                print(f"   ✅ Updated {updated_count} existing members with levels")

                conn.commit()
                print("✅ Migration to version 2.0 completed successfully!")
                return True

        except Exception as e:
            print(f"❌ Migration to version 2.0 failed: {e}")
            return False

    def _add_column_if_not_exists(
        self, cursor, table: str, column: str, definition: str
    ):
        """Add a column to a table if it doesn't exist."""
        cursor.execute(f"PRAGMA table_info({table})")
        columns = [col[1] for col in cursor.fetchall()]
        if column not in columns:
            cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")
            print(f"   ✅ Added '{column}' column to {table} table")

    def _create_table_if_not_exists(self, cursor, table: str, create_sql: str):
        """Create a table if it doesn't exist."""
        cursor.execute(
            f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'"
        )
        if not cursor.fetchone():
            cursor.execute(create_sql)
            print(f"   ✅ Created '{table}' table")

    def _create_index_if_not_exists(
        self, cursor, index_name: str, index_definition: str
    ):
        """Create an index if it doesn't exist."""
        cursor.execute(
            f"SELECT name FROM sqlite_master WHERE type='index' AND name='{index_name}'"
        )
        if not cursor.fetchone():
            cursor.execute(f"CREATE INDEX {index_name} ON {index_definition}")
            print(f"   ✅ Created index {index_name}")

    def run_migrations(self) -> bool:
        """Run all pending migrations."""
        current_version = self.get_current_version()
        print(f"📊 Current database version: {current_version}")

        # Get all migrations that need to run
        pending_migrations = [
            (version, description, func)
            for version, description, func in self.migrations
            if self._version_greater(version, current_version)
        ]

        if not pending_migrations:
            print("✅ Database is up to date - no migrations needed.")
            return True

        # Create backup before running migrations
        backup_path = self.backup_database()

        try:
            for version, description, migration_func in pending_migrations:
                print(f"\n🔄 Running migration to version {version}: {description}")

                if not migration_func():
                    print(f"❌ Migration to version {version} failed!")
                    return False

                # Update version after successful migration
                self.set_version(version)
                print(f"✅ Successfully migrated to version {version}")

            print(f"\n✅ All migrations completed successfully!")
            print(f"📁 Database backup saved at: {backup_path}")
            return True

        except Exception as e:
            print(f"❌ Migration failed: {e}")
            return False

    def _version_greater(self, version1: str, version2: str) -> bool:
        """Compare version strings."""
        v1_parts = [int(x) for x in version1.split(".")]
        v2_parts = [int(x) for x in version2.split(".")]

        # Pad with zeros if needed
        max_len = max(len(v1_parts), len(v2_parts))
        v1_parts.extend([0] * (max_len - len(v1_parts)))
        v2_parts.extend([0] * (max_len - len(v2_parts)))

        return v1_parts > v2_parts


def run_migrations():
    """Run all pending migrations."""
    manager = MigrationManager()
    return manager.run_migrations()


if __name__ == "__main__":
    print("🚀 Database Migration Manager")
    print("=" * 50)

    success = run_migrations()
    exit(0 if success else 1)
