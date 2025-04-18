# Use Python 3.11 slim base
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install dependencies
RUN apt-get update && apt-get install -y \
    git \
    sqlite3 \
 && rm -rf /var/lib/apt/lists/*

# Clone your GitHub repo
RUN git clone https://github.com/oyinlola007/deanna874.git .

# Install Python requirements
RUN pip install --upgrade pip && pip install -r requirements.txt

# Ensure data folder exists for DB
RUN mkdir -p data

# Run the bot
CMD ["python", "main.py"]
