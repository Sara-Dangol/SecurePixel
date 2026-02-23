# Dockerfile for SecurePixel Main Application
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
    # Build tools for crypto libraries
    gcc \
    g++ \
    make \
    libffi-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
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

# Set display for X11
ENV DISPLAY=:0

# Create startup script
RUN echo '#!/bin/bash\n\
echo "========================================="\n\
echo "🔐 SecurePixel - Starting..."\n\
echo "========================================="\n\
echo "Waiting for database..."\n\
sleep 10\n\
echo "✅ Database ready"\n\
echo "Launching application..."\n\
python /app/stegno_gui.py\n\
' > /home/appuser/start.sh && chmod +x /home/appuser/start.sh

# Command to run
CMD ["/home/appuser/start.sh"]
