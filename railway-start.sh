#!/bin/bash
set -e

echo "=== Railway Deployment Script ==="
echo "Current directory: $(pwd)"
echo "Python version check..."

# Try different Python commands
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
    echo "Using python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
    echo "Using python"
else
    echo "Error: No Python found!"
    exit 1
fi

echo "Python version: $($PYTHON_CMD --version)"

# Go to backend directory
echo "Changing to backend directory..."
cd backend

# List files to debug
echo "Files in backend directory:"
ls -la

# Start the application
echo "Starting uvicorn server..."
exec $PYTHON_CMD -m uvicorn main:app --host 0.0.0.0 --port $PORT