#!/bin/bash

# Get the directory of this script
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

echo "Starting the News Analyzer API..."
echo "Server will be available at: http://localhost:8000"
echo "API docs will be available at: http://localhost:8000/docs"
echo ""

# Check if .env file exists
if [ ! -f "$DIR/.env" ]; then
    echo "⚠️ Warning: .env file not found!"
    echo "Please create a .env file with your API keys. See .env.example for reference."
    echo ""
else
    echo "✅ Found .env file"
fi

# Activate virtual environment if exists
if [ -d "$DIR/venv" ]; then
    source "$DIR/venv/bin/activate"
    echo "✅ Virtual environment activated."
else
    echo "⚠️ No virtual environment found at $DIR/venv"
    echo "It's recommended to create one for dependency isolation."
    echo ""
fi

# Check if python-dotenv is installed
if ! pip show python-dotenv > /dev/null 2>&1; then
    echo "⚠️ python-dotenv is not installed. Installing..."
    pip install python-dotenv
fi

# Check if aiohttp is installed
if ! pip show aiohttp > /dev/null 2>&1; then
    echo "⚠️ aiohttp is not installed. Installing..."
    pip install aiohttp
fi

# Load environment variables from .env file
if [ -f "$DIR/.env" ]; then
    export $(grep -v '^#' "$DIR/.env" | xargs)
    echo "✅ Loaded environment variables from .env file"
fi

# Set environment variables
export USE_MOCK_APIS=${USE_MOCK_APIS:-"false"}
export DB_FILE=${DB_FILE:-"articles_db.json"}

if [ "$USE_MOCK_APIS" = "false" ]; then
    echo "🔄 Using REAL APIs"
    
    # Check for API keys
    if [ -z "$OPENAI_API_KEY" ]; then
        echo "⚠️ OPENAI_API_KEY not set in environment or .env file"
    else
        echo "✅ Found OpenAI API key"
    fi
    
    if [ -z "$SEARCH_API_KEY" ]; then
        echo "⚠️ SEARCH_API_KEY not set in environment or .env file"
    else
        echo "✅ Found Search API key"
    fi
    
    if [ -z "$SEARCH_ENGINE_CX" ]; then
        echo "⚠️ SEARCH_ENGINE_CX not set in environment or .env file"
    else
        echo "✅ Found Search Engine CX"
    fi
else
    echo "🔄 Using MOCK APIs for development"
fi

echo ""
echo "Starting server..."
echo ""

# Run the FastAPI application
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000 