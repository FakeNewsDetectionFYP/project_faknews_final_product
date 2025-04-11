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

4. Run the backend service:
   ```bash
   uvicorn main:app --reload
   ```

5. The API will be available at `http://localhost:8000`

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

## 💡 Development

### Mock APIs

During development, mock APIs are used by default. This allows for testing without real API keys.

To use real APIs:
1. Create a `.env` file in the backend directory
2. Add your API keys:
   ```
   USE_MOCK_APIS=false
   OPENAI_API_KEY=your_openai_key
   SEARCH_API_KEY=your_search_api_key
   ```

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

---

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details. 