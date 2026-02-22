#!/bin/bash

echo "========================================"
echo "SecurePixel - Starting..."
echo "========================================"

# Wait for database
echo "Waiting for database connection..."
max_tries=30
count=0
while ! mysqladmin ping -h"$DB_HOST" -P"$DB_PORT" --silent; do
    count=$((count+1))
    if [ $count -gt $max_tries ]; then
        echo "❌ Database connection timeout!"
        echo "Please check if MySQL container is running properly."
        exit 1
    fi
    echo "   Still waiting... ($count/$max_tries)"
    sleep 2
done

echo "✅ Database connected successfully!"

# Create shared directory
mkdir -p /home/appuser/shared
echo "✅ Shared directory ready at /home/appuser/shared"

# Show environment info
echo "========================================"
echo "Environment:"
echo "   DB Host: $DB_HOST"
echo "   DB Port: $DB_PORT"
echo "   DB Name: $DB_NAME"
echo "   Display: $DISPLAY"
echo "========================================"

# Run application
echo "🚀 Launching PKI Steganography Suite..."
cd /app
python stegno_gui.py

echo "Application closed."
