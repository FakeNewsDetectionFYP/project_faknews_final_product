# News Analysis Backend

This backend system provides news article analysis capabilities including fake news detection, credibility scoring, sentiment analysis, and article summarization.

## Setup Instructions

1. **Install dependencies**:

```bash
# Run the dependency installation script
./reinstall_deps.sh

# Or manually install dependencies
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

2. **Environment variables**:

Make sure your `.env` file is set up with the following variables:

```
# Set to "false" to use real APIs instead of mock implementations
USE_MOCK_APIS=false

# OpenAI API Key
OPENAI_API_KEY=your_openai_api_key

# Google Search API Key and Custom Search Engine ID
SEARCH_API_KEY=your_google_search_api_key
SEARCH_ENGINE_CX=your_custom_search_engine_id
```

3. **Start the server**:

```bash
# Start the server with hot reload
python3 -m uvicorn main:app --reload

# If you have issues with uvicorn module not being found
source venv/bin/activate && python -m uvicorn main:app --reload
```

## Changes Made

1. Removed LangGraph dependencies to simplify the application
2. Enhanced the sequential processing approach to be more robust
3. Fixed Google Search API implementation to use direct Google Custom Search instead of SearchAPI.io
4. Added better error handling and fallback mechanisms
5. Improved logging to help diagnose issues

## Troubleshooting

### Python Command Not Found

If you see an error like `command not found: python`, use `python3` instead:

```bash
python3 -m uvicorn main:app --reload
```

### Google Search API Issues

If you see 401 Unauthorized errors with Google Search:

1. Verify your Google Custom Search API key in the `.env` file
2. Make sure your Custom Search Engine ID (CX) is correct
3. Ensure you've enabled the Custom Search API in Google Cloud Console:
   - Go to https://console.cloud.google.com/
   - Navigate to APIs & Services > Dashboard
   - Click "+ ENABLE APIS AND SERVICES" 
   - Search for "Custom Search API" and enable it
4. Check your API quota and billing status in Google Cloud Console

### OpenAI API Issues

If you experience OpenAI API errors:

1. Verify your OpenAI API key in the `.env` file
2. Check that your account has sufficient credits/billing
3. Ensure you're using a correct and active API key

### Using Mock APIs for Development

For development purposes, you can use mock APIs by setting:

```
USE_MOCK_APIS=true
```

in your `.env` file. This will generate mock responses instead of calling the real APIs.

## API Documentation

See `API_DOCS.md` for detailed API endpoints and usage. 