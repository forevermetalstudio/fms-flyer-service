FROM python:3.11-slim

# Install system dependencies for Chromium
RUN apt-get update && apt-get install -y \
    chromium \
    chromium-driver \
    nodejs \
    npm \
    fonts-liberation \
    fonts-dejavu-core \
    libglib2.0-0 \
    libnss3 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Node dependencies (puppeteer)
COPY package.json ./
RUN npm install

# Install Python dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Set environment variables
ENV PUPPETEER_EXECUTABLE_PATH=/usr/bin/chromium
ENV PORT=10000

EXPOSE 10000

CMD ["gunicorn", "--bind", "0.0.0.0:10000", "--timeout", "120", "--workers", "1", "app:app"]
