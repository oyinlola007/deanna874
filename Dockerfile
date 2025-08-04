# Use Python 3.11 slim base
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install dependencies
RUN apt-get update && apt-get install -y \
    git \
    sqlite3 \
    wget \
    libnss3 \
    libatk-bridge2.0-0 \
    libgtk-3-0 \
    libxss1 \
    libasound2 \
    libgbm-dev \
    libxshmfence1 \
    libxcomposite1 \
    libxrandr2 \
    libu2f-udev \
    fonts-liberation \
    libappindicator3-1 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libjpeg-dev \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

# Clone your GitHub repo
RUN git clone https://github.com/oyinlola007/deanna874.git .

# Install Python requirements
RUN pip install --upgrade pip && pip install -r requirements.txt

# Install Playwright browsers
RUN playwright install chromium
RUN playwright install-deps

# Ensure data folder exists for DB
RUN mkdir -p data

# Run the bot
CMD ["python", "main.py"]
