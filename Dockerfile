# Use Microsoft's official Playwright Python Docker image with latest stable version
FROM mcr.microsoft.com/playwright/python:v1.54.0-noble

# Set working directory
WORKDIR /app

# Install additional dependencies needed for the bot
RUN apt-get update && apt-get install -y \
    git \
    sqlite3 \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Clone your GitHub repo
RUN git clone https://github.com/oyinlola007/deanna874.git .

# Install Python requirements
RUN pip install --upgrade pip && pip install -r requirements.txt

# Ensure data folder exists for DB
RUN mkdir -p data

# Run the bot
CMD ["python", "main.py"]
