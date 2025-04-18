# Discord Engagement Bot

A custom Discord bot to track and reward community engagement via messages, reactions, shares, and invites.

## Features
- Points system for various activities
- Milestone rewards with notifications
- Admin commands to manage config, points, and users

## Setup

1. Clone the repo:
```bash
git clone https://github.com/oyinlola007/deanna874.git
cd deanna874
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file:
```
BOT_TOKEN=your-bot-token-here
```

---

### ⚠️ IMPORTANT: Add an Admin
Open `setup_db.py` and **add at least one Discord user ID as an admin** before initializing the database.

Look for the section:
```python
# Example admin ID (replace with real admin Discord IDs)
admin_ids = ["588443056529866818"]
```
Replace the value in the list with your own Discord user ID to ensure you have access to admin-only commands.

---

### 4. Run the bot
```bash
python main.py
```

## License
This project is licensed under the MIT License. See [LICENSE](LICENSE) for more information.