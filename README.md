# Discord Gamification Bot

A comprehensive Discord bot that transforms communities into engaging, competitive environments through advanced gamification features, automated role management, and professional image-based dashboards.

---

## ✨ Features

### 🎯 Core Gamification
- **Points System**: Track engagement through messages, reactions, images, invites, and URL sharing
- **Level Progression**: Automatic level calculation based on points with role assignments
- **Streak Tracking**: Daily activity streaks with longest streak records
- **Milestone Rewards**: Configurable milestones with automatic notifications and reward codes
- **Campaign Multipliers**: Temporary bonus point multipliers for specific channels

### 📊 Professional Dashboards
- **Personal Dashboard** (`/ttp-dashboard`): Comprehensive user profile with Neumorphism design
- **Quick Stats** (`/ttp-mystats`): Snapshot view with header section only
- **Leaderboard** (`/ttp-leaderboard`): Professional image-based top 10 leaderboard with medals
- **Dynamic Server Names**: Leaderboards display actual server names
- **User Highlighting**: Current user highlighted in leaderboards
- **Avatar Integration**: Discord avatars with fallback to default icons

### 🏆 Advanced Leaderboard System
- **Professional Design**: Image-based leaderboards with modern styling
- **Medal System**: Gold, silver, bronze medals for top 3 positions
- **Comprehensive Data**: Position, user info, messages, reactions, images, invites, total XP
- **Exclusion Management**: Admin control over who appears on leaderboards
- **Real-time Updates**: Live leaderboard generation

### 🎮 Engagement Tracking
- **Message Tracking**: Points for messages in tracked channels
- **Reaction Rewards**: Points for reactions (one per message per user)
- **Image Sharing**: Bonus points for image uploads
- **Invite Rewards**: Points for successful server invites
- **URL Sharing**: Points for sharing links
- **Daily Limits**: Configurable daily point limits per user

### 👥 Role Management
- **Auto Role Assignment**: Automatic role assignment based on levels
- **Level-based Roles**: Configurable roles at specific point milestones
- **Permission Management**: Proper Discord permission handling
- **Role Hierarchy**: Support for role-based channel access

### 🎯 Campaign System
- **Bonus Multipliers**: Temporary point multipliers for specific channels
- **Campaign Management**: Create, list, and delete campaigns
- **Time-based Campaigns**: Start and end dates for campaigns
- **Multiplier Tracking**: Automatic application of bonus points

### 📺 Voice Channel Integration
- **Top 3 Display**: Voice channel names show top 3 users
- **Real-time Updates**: Automatic channel name updates
- **User Information**: Display usernames and points in channel names

### 🛠️ Admin Management
- **Comprehensive Admin Commands**: Full control over bot configuration
- **Points Management**: Reset, set, add, remove points for users
- **Milestone Management**: Create, edit, and manage milestones
- **Channel Tracking**: Control which channels are tracked
- **Database Export**: Export data for analysis
- **Configuration Management**: Flexible bot configuration

---

## 🚀 Quick Start

### Prerequisites
- Python 3.8+ or Docker
- Discord Bot Token
- Discord Server with appropriate permissions

### ⚙️ Setup Without Docker

1. **Clone the repository:**
```bash
git clone https://github.com/oyinlola007/deanna874.git
cd deanna874
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Install Playwright browsers:**
```bash
playwright install
```

4. **Create `.env` file:**
```env
BOT_TOKEN=your-discord-bot-token-here
```

5. **Set up admin user:**
Edit `src/core/setup_db.py` and replace the example admin with your Discord user ID:
```python
admin_ids = ["your-discord-user-id"]
```

6. **Run the bot:**
```bash
python main.py
```

### 🐳 Setup Using Docker (Recommended)

1. **Clone the repository:**
```bash
git clone https://github.com/oyinlola007/deanna874.git
cd deanna874
```

2. **Update Dockerfile (if using a fork):**
Edit the Dockerfile and update the repository URL if needed:
```dockerfile
RUN git clone https://github.com/oyinlola007/deanna874.git .
```

3. **Set up admin user:**
Edit `src/core/setup_db.py` and replace with your Discord user ID:
```python
admin_ids = ["your-discord-user-id"]
```

4. **Create `.env` file:**
```env
BOT_TOKEN=your-discord-bot-token-here
```

5. **Build and run:**
```bash
docker-compose up --build
```

For background operation:
```bash
docker-compose up --build -d
```

---

## 📋 Available Commands

### 🎮 User Commands
- `/ttp-dashboard` - Generate your personal dashboard
- `/ttp-mystats` - Quick stats snapshot
- `/ttp-leaderboard` - View top 10 members leaderboard
- `/ttp-help` - Show all available commands

### 👑 Admin Commands

**Points Management:**
- `/ttp-resetpoints` - Reset a user's points
- `/ttp-resetallpoints` - Reset all users' points
- `/ttp-setpoints` - Set a user's points
- `/ttp-addpoints` - Add points to a user
- `/ttp-removepoints` - Remove points from a user
- `/ttp-setdailylimit` - Set daily point limit

**Configuration:**
- `/ttp-setconfig` - Set bot configuration
- `/ttp-viewconfig` - View current configuration

**Milestones:**
- `/ttp-listmilestones` - List all milestones
- `/ttp-addmilestone` - Add a new milestone
- `/ttp-removemilestone` - Remove a milestone
- `/ttp-setmilestonemessage` - Set milestone message
- `/ttp-setmilestonerole` - Set milestone role
- `/ttp-setmilestonereward` - Set milestone reward

**Role Management:**
- `/ttp-assignroles` - Assign roles to users

**Rewards:**
- `/ttp-markrewarded` - Mark milestone as rewarded
- `/ttp-pendingrewards` - View pending rewards
- `/ttp-markrewardedbatch` - Mark multiple rewards

**Channel Tracking:**
- `/ttp-trackchannel` - Start tracking a channel
- `/ttp-untrackchannel` - Stop tracking a channel
- `/ttp-listtrackedchannels` - List tracked channels

**Admin Management:**
- `/ttp-listadmins` - List all admins
- `/ttp-addadmin` - Add an admin
- `/ttp-removeadmin` - Remove an admin

**Leaderboard Exclusion:**
- `/ttp-excludeuser` - Exclude user from leaderboard
- `/ttp-includeuser` - Include user in leaderboard
- `/ttp-excludedusers` - List excluded users

**Campaign Management:**
- `/ttp-createcampaign` - Create a campaign
- `/ttp-listcampaigns` - List all campaigns
- `/ttp-deletecampaign` - Delete a campaign

**Database:**
- `/ttp-exportdb` - Export database

---

## 🏗️ Project Structure

```
deanna874/
├── src/
│   ├── commands/          # All bot commands
│   │   ├── slash_*.py    # Slash commands
│   │   └── *.py          # Legacy commands
│   ├── core/             # Core functionality
│   │   ├── database.py   # Database operations
│   │   ├── config.py     # Configuration
│   │   └── setup_db.py   # Database setup
│   ├── dashboard/        # Dashboard system
│   │   ├── templates/    # HTML templates
│   │   └── static/       # CSS and assets
│   └── utils/            # Utility functions
├── data/                 # Database files
├── docs/                 # Documentation
├── main.py              # Bot entry point
└── requirements.txt     # Python dependencies
```

---

## 🎨 Dashboard Features

### Personal Dashboard (`/ttp-dashboard`)
- **User Profile**: Avatar, username, role, join date
- **Progress Tracking**: Current level, points, next milestone
- **Activity Charts**: Weekly activity visualization
- **Statistics**: Messages, reactions, images, invites
- **Leaderboard**: Current rank and top users
- **Streak Information**: Current and longest streaks

### Quick Stats (`/ttp-mystats`)
- **Header Section**: Essential user information
- **Current Status**: Level, points, rank
- **Progress Bar**: Visual progress to next level
- **Compact Design**: Quick overview format

### Leaderboard (`/ttp-leaderboard`)
- **Top 10 Users**: Professional ranking display
- **Medal System**: Gold, silver, bronze for top 3
- **Comprehensive Data**: All engagement metrics
- **User Highlighting**: Current user emphasis
- **Dynamic Server Names**: Actual server names displayed

---

## 🔧 Configuration

### Bot Permissions Required
- **Send Messages**: To respond to commands
- **Attach Files**: To send dashboard images
- **Manage Roles**: For automatic role assignment
- **Manage Channels**: For voice channel name updates
- **Read Message History**: For engagement tracking
- **Add Reactions**: For reaction tracking

### Database Schema
- **members**: User data, points, levels, streaks
- **milestones**: Milestone configuration and rewards
- **engagement_log**: Activity tracking
- **config**: Bot configuration
- **admin_ids**: Admin user management
- **tracked_channels**: Channel tracking configuration
- **excluded_leaderboard**: Leaderboard exclusions
- **campaign_channels**: Campaign multiplier tracking
- **voice_channel_display**: Top 3 display configuration

---

## 🚀 Advanced Features

### Image Generation System
- **Playwright Integration**: High-quality browser rendering
- **Jinja2 Templates**: Dynamic HTML generation
- **Neumorphism Design**: Modern UI styling
- **Responsive Layout**: Works on all screen sizes
- **Professional Output**: Production-ready images

### Real-time Updates
- **Voice Channel Names**: Live top 3 user display
- **Leaderboard Updates**: Real-time ranking changes
- **Role Assignments**: Automatic role management
- **Streak Tracking**: Daily activity monitoring

### Performance Optimizations
- **Database Indexing**: Optimized queries
- **Caching**: Efficient data access
- **Rate Limiting**: Discord API compliance
- **Error Handling**: Robust error management

---

## 📊 Database Persistence

The bot uses SQLite for data storage with automatic persistence:
- **Docker Volume**: Database survives container restarts
- **Backup Support**: Easy database export functionality
- **Migration System**: Automatic schema updates
- **Data Integrity**: Proper foreign key relationships

---

## 🔄 Updates and Maintenance

### Pull Latest Changes
```bash
git pull origin main
```

### Docker Updates
```bash
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### Database Migrations
The bot automatically runs database migrations on startup to ensure schema compatibility.

---

## 📜 License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

---

## 📞 Support

For support, please open an issue on GitHub or contact the development team.

**Payment Details:** Revolut @oyinlola1
