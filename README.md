# Discord Engagement Bot

A custom Discord bot to track and reward community engagement via messages, reactions, shares, and invites.

---

## ✨ Features

- Points system for various activities (messages, invites, reactions, shares)
- Milestone-based rewards with automatic notifications
- Admin-only commands for managing users, config, and rewards
- SQLite-based persistence
- Easy setup with Docker or Python

---

## ⚙️ Setup Without Docker (Manual Method)

1. Clone the repo:
```bash
git clone https://github.com/oyinlola007/deanna874.git
cd deanna874
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file in the project root:
```
BOT_TOKEN=your-discord-bot-token-here
```

4. ⚠️ **Set up your admin ID:**

Open `setup_db.py` and replace the example admin with your actual Discord user ID:
```python
# Example admin ID (replace with real admin Discord IDs)
admin_ids = ["your-discord-user-id"]
```

5. Run the bot:
```bash
python main.py
```

---

## 🐳 Setup Using Docker (Recommended)

This method is ideal for clean, isolated deployments.

### 📁 Required files

To run this project with Docker, you only need:
- `Dockerfile`
- `docker-compose.yml`
- `.env` file

```bash
curl -O https://raw.githubusercontent.com/oyinlola007/deanna874/main/Dockerfile
curl -O https://raw.githubusercontent.com/oyinlola007/deanna874/main/docker-compose.yml
```

---

### 🔧 1. Clone the Repository First

The Dockerfile clones the GitHub repo — you **must update it to your fork if you're not using the original**.

Open the Dockerfile and update this line:
```dockerfile
RUN git clone https://github.com/oyinlola007/deanna874.git .
```
If you've forked or renamed it, replace with your own repo URL.

---

### 👮‍♂️ 2. Add Your Admin User

Edit `setup_db.py` inside the repo (before building Docker) and replace the example admin with your own:
```python
admin_ids = ["your-discord-user-id"]
```

---

### 📄 3. Create a `.env` file (same directory as the Docker files)

```env
BOT_TOKEN=your-discord-bot-token-here
```

---

### ▶️ 4. Build and Run the Bot

```bash
docker-compose up --build
```

To run in the background:

```bash
docker-compose up --build -d
```

---

### 🔁 5. If You Update the Codebase (e.g., on GitHub)

To pull changes and refresh your container:
```bash
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

This ensures you always run the latest version of the bot.

---

### 💾 Database Persistence

The bot stores its SQLite database in a `data/` folder. This is automatically mounted via volume in Docker, so your points and engagement history survive restarts.

---

## 📜 License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.
