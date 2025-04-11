#!/bin/bash

echo "Reinstalling core dependencies..."

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
    echo "Activated virtual environment"
else
    echo "Creating new virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
fi

# Install dependencies from requirements.txt
echo "Installing dependencies from requirements.txt..."
pip install -r requirements.txt

# Set USE_MOCK_APIS to false in .env
if [ -f ".env" ]; then
    echo "Updating .env file to use real APIs..."
    # Check API keys in .env
    if grep -q "OPENAI_API_KEY=" .env && grep -q "SEARCH_API_KEY=" .env && grep -q "SEARCH_ENGINE_CX=" .env; then
        echo "API keys found in .env file"
        
        # Use sed to replace the USE_MOCK_APIS line
        if [[ "$OSTYPE" == "darwin"* ]]; then
            # macOS requires a different sed syntax
            sed -i '' 's/USE_MOCK_APIS=true/USE_MOCK_APIS=false/g' .env
        else
            # Linux sed syntax
            sed -i 's/USE_MOCK_APIS=true/USE_MOCK_APIS=false/g' .env
        fi
    else
        echo "WARNING: Some API keys may be missing in .env file"
        echo "Please ensure you have set up:"
        echo "  - OPENAI_API_KEY"
        echo "  - SEARCH_API_KEY (Google API Key)"
        echo "  - SEARCH_ENGINE_CX (Google Custom Search Engine ID)"
    fi
else
    echo "WARNING: No .env file found. Creating one..."
    echo "USE_MOCK_APIS=true" > .env
    echo "OPENAI_API_KEY=" >> .env
    echo "SEARCH_API_KEY=" >> .env
    echo "SEARCH_ENGINE_CX=" >> .env
    echo "DB_FILE=articles_db.json" >> .env
    echo "Please edit .env and add your API keys"
fi

# Verify python imports
echo "Checking for critical modules..."
python3 -c "import json; import aiohttp; import bs4; print('All critical modules available')" || echo "WARNING: Some modules may be missing"

echo "Dependencies installed successfully!"
echo "Run 'python3 -m uvicorn main:app --reload' to start the service" 