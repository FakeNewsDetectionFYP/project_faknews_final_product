#!/bin/bash

# Setup script for News Analyzer project
# This script sets up both the backend and frontend

echo "Setting up News Analyzer project..."

# Check for Python and Node.js
if ! command -v python3 &> /dev/null; then
    echo "Python 3 is required but not installed. Please install Python 3 and try again."
    exit 1
fi

if ! command -v node &> /dev/null; then
    echo "Node.js is required but not installed. Please install Node.js and try again."
    exit 1
fi

# Setup backend
echo "Setting up backend..."
cd backend

# Create Python virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt

# Create empty database file
touch articles_db.json

# Return to root directory
cd ..

# Setup frontend extension
echo "Setting up frontend extension..."
cd extension

# Install npm dependencies
npm install

# Build the extension
npm run build

# Return to root directory
cd ..

echo "Setup complete!"
echo ""
echo "To run the backend server:"
echo "  cd backend"
echo "  ./run_dev.sh"
echo ""
echo "To load the extension in Chrome:"
echo "  1. Go to chrome://extensions/"
echo "  2. Enable 'Developer mode'"
echo "  3. Click 'Load unpacked'"
echo "  4. Select the 'extension/dist' directory"
echo ""
echo "Alternatively, use Docker Compose to run both services:"
echo "  docker-compose up" 