FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for building Python packages
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    wget \
    gnupg

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright system dependencies FIRST (critical for containers)
# This installs all required shared libraries for Chromium in production
RUN playwright install-deps chromium

# Then install Playwright browser binaries
RUN playwright install chromium

# Clean up apt cache to reduce image size
RUN rm -rf /var/lib/apt/lists/*

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Run the application
CMD ["python", "api_server.py"]
