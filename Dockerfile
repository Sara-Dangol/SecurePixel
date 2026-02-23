# Dockerfile for SecurePixel
FROM python:3.9-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    # Tkinter GUI support
    python3-tk \
    x11-apps \
    libx11-6 \
    libxext6 \
    libxrender1 \
    libxtst6 \
    libxi6 \
    # Database client
    default-mysql-client \
    # File utilities
    file \
    # Build tools
    gcc \
    g++ \
    make \
    libffi-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -s /bin/bash appuser && \
    mkdir -p /app /home/appuser/shared && \
    chown -R appuser:appuser /app /home/appuser

# Set working directory
WORKDIR /app

# Copy requirements first (for better caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY stegno_gui.py .

# Create necessary directories
RUN mkdir -p /home/appuser/.local/share/SecurePixel && \
    chown -R appuser:appuser /home/appuser/.local

# Switch to non-root user
USER appuser

# Set display (will be overridden by docker-compose)
ENV DISPLAY=:0

# Create a helper script
RUN echo '#!/bin/bash\n\
echo "========================================="\n\
echo "🔐 SecurePixel - Starting..."\n\
echo "========================================="\n\
echo "Waiting for database connection..."\n\
max_tries=30\n\
count=0\n\
while ! mysqladmin ping -h"$DB_HOST" -P"$DB_PORT" --silent; do\n\
    count=$((count+1))\n\
    if [ $count -gt $max_tries ]; then\n\
        echo "❌ Database connection timeout!"\n\
        echo "Starting in demo mode..."\n\
        break\n\
    fi\n\
    echo "   Still waiting... ($count/$max_tries)"\n\
    sleep 2\n\
done\n\
echo "✅ Database ready"\n\
echo "Launching application..."\n\
python /app/stegno_gui.py\n\
' > /home/appuser/start.sh && chmod +x /home/appuser/start.sh

# Command to run
CMD ["/home/appuser/start.sh"]