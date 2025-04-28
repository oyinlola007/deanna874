import sqlite3
import cogs.config as config


# Create tables
def setup():
    # Connect to SQLite database (will create it if it doesn't exist)
    conn = sqlite3.connect(config.DATABASE_NAME)
    cursor = conn.cursor()

    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS members (
        discord_id TEXT PRIMARY KEY,
        total_points INTEGER DEFAULT 0
    );
    """
    )

    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS config (
        key TEXT PRIMARY KEY,
        value TEXT NOT NULL
    );
    """
    )

    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS admin_ids (
        discord_id TEXT PRIMARY KEY,
        status TEXT DEFAULT 'active'
    );
    """
    )

    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS tracked_channels (
        channel_id TEXT PRIMARY KEY,
        status TEXT DEFAULT 'active'
    );
    """
    )

    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS milestones (
        value INTEGER PRIMARY KEY,
        status TEXT DEFAULT 'active',
        message TEXT
    );
    """
    )

    # Renamed to avoid conflict with milestones config table
    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS milestones_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        discord_id TEXT NOT NULL,
        milestone INTEGER NOT NULL,
        reached_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        user_notified INTEGER DEFAULT 0,
        admin_notified INTEGER DEFAULT 0,
        reward_status TEXT DEFAULT 'pending',
        reward_code TEXT,
        FOREIGN KEY(discord_id) REFERENCES members(discord_id)
    );
    """
    )

    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS engagement_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        discord_id TEXT NOT NULL,
        activity_type TEXT NOT NULL,
        activity_object_id TEXT,
        channel_id TEXT,
        point_value INTEGER DEFAULT 0,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(discord_id) REFERENCES members(discord_id)
    );
    """
    )

    # Insert initial config values
    default_config = {
        "points_per_message": "1",
        "points_per_invite": "1000",
        "points_per_reaction": "5",
        "points_per_share": "50",
        "points_per_image": "10",
        "notification_channel_id": "YOUR_CHANNEL_ID",
    }

    for key, value in default_config.items():
        cursor.execute(
            "INSERT OR IGNORE INTO config (key, value) VALUES (?, ?)", (key, value)
        )

    milestones = [
        (1000, "active", "🎉 Congrats! You've reached 1,000 points!"),
        (5000, "active", "🚀 You're on fire! You've hit 5,000 points!"),
        (10000, "active", "🏆 Incredible! You've reached 10,000 points!"),
    ]

    for value, status, message in milestones:
        cursor.execute(
            "INSERT OR IGNORE INTO milestones (value, status, message) VALUES (?, ?, ?)",
            (value, status, message),
        )

    # Example admin ID (replace with real admin Discord IDs)
    admin_ids = ["1301517023846858784"]
    for admin in admin_ids:
        cursor.execute(
            "INSERT OR IGNORE INTO admin_ids (discord_id, status) VALUES (?, 'active')",
            (admin,),
        )

    # Finalize
    conn.commit()
    conn.close()

    print(
        "✅ Database initialized successfully with config, milestones, admins, and tracked channels."
    )
