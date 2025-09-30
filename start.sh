#!/bin/bash
set -e
echo "Starting deployment..."

# Find Python executable
PYTHON_CMD="python3"
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
else
    echo "Python not found!"
    exit 1
fi

echo "Using Python: $PYTHON_CMD"

# Go to backend directory
cd backend
echo "Current directory: $(pwd)"
echo "Python version: $($PYTHON_CMD --version)"

# Install dependencies
echo "Installing dependencies..."
$PYTHON_CMD -m pip install --upgrade pip
$PYTHON_CMD -m pip install -r requirements.txt

# Start the application
echo "Starting uvicorn..."
$PYTHON_CMD -m uvicorn main:app --host 0.0.0.0 --port $PORT