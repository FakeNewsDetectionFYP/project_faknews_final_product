# 🧠 Multi-Agent News Processing Web Extension

A browser extension that processes news articles using a LangGraph-powered multi-agent system.

## 📌 Project Overview

This project is a **browser extension** that collects the **URL of the currently viewed news article** and sends it to a **backend powered by LangGraph**, where a **multi-agent system** processes the article. The results are stored in a **persistent database** and retrieved when the same article is revisited.

### Key Features

- ✅ Browser extension captures news article URLs
- ✅ LangGraph backend with specialized agents for processing
- ✅ Mock API system for development without real API keys
- ✅ Persistent storage of analyzed articles
- ✅ Multiple analysis types: fake news detection, credibility, sentiment, summary

---

## 🛠️ Setup Instructions

### Backend Setup

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Configure API settings (see [API Configuration](#api-configuration) below)

5. Run the backend service:
   ```bash
   ./run_dev.sh
   ```

6. The API will be available at `http://localhost:8000`
   API docs will be available at `http://localhost:8000/docs`

### Using Docker

Alternatively, you can use Docker to run the backend:

```bash
cd backend
docker build -t news-processor-api .
docker run -p 8000:8000 -v $(pwd)/data:/data news-processor-api
```

### Browser Extension Setup

1. Navigate to the extension directory:
   ```bash
   cd extension
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Build the extension:
   ```bash
   npm run build
   ```

4. Load the extension in Chrome:
   - Go to `chrome://extensions/`
   - Enable "Developer mode"
   - Click "Load unpacked"
   - Select the `extension/dist` directory

---

## 💡 Development and Testing

### API Configuration

The system can operate in two modes:

#### 1. Mock API Mode (for development/testing)

This mode uses pre-defined mock data and doesn't require API keys:

1. Create or edit `.env` file in the backend directory:
   ```
   USE_MOCK_APIS=true
   DB_FILE=articles_db.json
   ```

2. Run the backend with mock APIs:
   ```bash
   cd backend
   ./run_dev.sh
   ```

3. The terminal will confirm: `🔄 Using MOCK APIs for development`

#### 2. Real API Mode (for production use)

This mode uses actual OpenAI and Google Search APIs to analyze articles:

1. Create or edit `.env` file in the backend directory with your API keys:
   ```
   USE_MOCK_APIS=false
   OPENAI_API_KEY=your_openai_api_key
   SEARCH_API_KEY=your_google_search_api_key
   SEARCH_ENGINE_CX=your_search_engine_cx
   DB_FILE=articles_db.json
   ```

2. Run the backend with real APIs:
   ```bash
   cd backend
   ./run_dev.sh
   ```

3. The terminal will confirm: `🔄 Using REAL APIs`

**Important**: When using real APIs, ensure your `.env` file is properly formatted with no line breaks in the API keys, and that all the required keys have valid values.

### Testing the Extension

The extension includes a dedicated test page to verify API connectivity:

1. With the backend running, open the extension popup
2. Click on the "API Test Tools" link in the popup header
3. Use the test buttons to verify:
   - URL extraction
   - Backend connectivity
   - API response handling

### Backend Architecture

The backend is built with FastAPI and uses LangGraph for orchestrating the multi-agent system:

- **Head Node**: Decides which agents to call
- **FakeNewsAgent**: Verifies factual claims in the article
- **CredibilityAgent**: Evaluates source reputation and content reliability
- **SentimentAgent**: Analyzes emotional tone and bias
- **SummaryAgent**: Generates a concise summary
- **ValidatorAgent**: Validates agent outputs

### Extension Architecture

The browser extension is built with Manifest V3 and consists of:

- **Background Script**: Captures the current tab's URL
- **Popup UI**: Displays processing results
- **Content Script**: Communicates with the backend

---

## 📊 Testing

Run backend tests:

```bash
cd backend
pytest
```

Run extension tests:

```bash
cd extension
npm test
```

### Manual Testing Flow

1. Start the backend server with `./run_dev.sh`
2. Load the extension in Chrome
3. Navigate to a news article
4. Click the extension icon
5. Verify that the article is processed and results are displayed
6. Check the "Fact Check" tab to confirm claims are extracted from the current article (not mock data)

### Troubleshooting

- If the fact-check claims show astronomy-themed examples, you're seeing mock data. Check that:
  - `USE_MOCK_APIS=false` is set in `.env`
  - Your API keys are valid and properly formatted
  - The backend server was restarted after configuration changes

- If no API calls are being made when opening the popup:
  - Check browser console for errors
  - Verify the backend server is running (http://localhost:8000)
  - Try the API Test Tools to debug communications

---

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details. 