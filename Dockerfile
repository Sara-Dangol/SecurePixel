# Use Python 3.9 slim image
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies for Windows compatibility
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    lsb-release \
    x11-apps \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libx11-6 \
    mariadb-client \
    xauth \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ /app/

# Copy startup script
COPY start.sh /start.sh
RUN chmod +x /start.sh && sed -i 's/\r$//g' /start.sh

# Create a non-root user to run the application
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app /start.sh

# Create shared directory
RUN mkdir -p /home/appuser/shared && \
    chown -R appuser:appuser /home/appuser/shared

# Switch to non-root user
USER appuser

# Set display for GUI (will be overridden by docker-compose)
ENV DISPLAY=:0
ENV PYTHONUNBUFFERED=1

# Default command
CMD ["/start.sh"]
