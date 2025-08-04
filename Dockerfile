# Use Python 3.11 slim base
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install dependencies
RUN apt-get update && apt-get install -y \
    git \
    sqlite3 \
    wget \
    curl \
    xvfb \
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
    libxdamage1 \
    libxfixes3 \
    libxcursor1 \
    libxi6 \
    libxtst6 \
    libdrm2 \
    libxkbcommon0 \
    libatspi2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Clone your GitHub repo
RUN git clone https://github.com/oyinlola007/deanna874.git .

# Install Python requirements
RUN pip install --upgrade pip && pip install -r requirements.txt

# Install Playwright and browsers in the correct order
RUN python -m playwright install-deps
RUN python -m playwright install --force chromium

# Set environment variables for Playwright  
ENV PLAYWRIGHT_BROWSERS_PATH=/root/.cache/ms-playwright

# Verify Playwright installation and browser availability
RUN python -c "from playwright.sync_api import sync_playwright; p = sync_playwright().start(); browser = p.chromium.launch(headless=True); print('Playwright and Chromium working correctly'); browser.close(); p.stop()"

# Ensure data folder exists for DB
RUN mkdir -p data

# Run the bot
CMD ["python", "main.py"]
