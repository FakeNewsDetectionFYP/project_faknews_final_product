# News Processing API Documentation

## Introduction

This API provides endpoints for processing news articles with a multi-agent system powered by LangGraph. It analyzes articles for credibility, fake news detection, sentiment, and provides summaries.

## Base URL

For local development:
```
http://localhost:8000
```

## Authentication

The API currently doesn't require authentication for development purposes. In a production environment, authentication should be implemented.

## Endpoints

### 1. Health Check

**GET /** 

Returns a simple message indicating the API is running.

**Response Example:**
```json
{
  "message": "News Processing API is running"
}
```

### 2. Process Article

**POST /process**

Processes a news article by URL. If the article has already been processed, returns cached results. Otherwise, queues processing in the background.

**Request Body:**
```json
{
  "url": "https://example.com/news-article",
  "title": "Optional Article Title",
  "source": "Optional Source Name"
}
```

**Parameters:**
- `url` (string, required): The URL of the news article to process
- `title` (string, optional): The title of the article if known
- `source` (string, optional): The source/publisher of the article if known

**Response Examples:**

New article being processed:
```json
{
  "message": "Article processing started",
  "article_id": "20230329121530",
  "cached": false
}
```

Article already processed:
```json
{
  "message": "Article already processed",
  "article_id": "20230329121530",
  "cached": true,
  "results": {
    "article_title": "Example News Article",
    "article_url": "https://example.com/news-article",
    "article_source": "Example News",
    "summary_result": "This is a summary of the article...",
    "fake_news_result": {
      "claims_analyzed": 5,
      "claims_verified": 4,
      "verification_score": 0.8,
      "verified_claims": ["Claim 1", "Claim 2", "Claim 3", "Claim 4"],
      "unverified_claims": ["Claim 5"]
    },
    "credibility_result": {
      "source_reputation": 0.75,
      "title_content_alignment": 0.9,
      "overall_credibility": 0.82,
      "evaluation": "This article appears to be from a credible source..."
    },
    "sentiment_result": {
      "polarity": -0.2,
      "subjectivity": 0.6,
      "emotional_tone": "slightly negative",
      "bias_assessment": "moderate bias detected",
      "justification": "The article uses language that suggests..."
    },
    "agents_called": ["fake_news", "credibility", "sentiment", "summary"],
    "processed_at": "2023-03-29T12:15:30"
  }
}
```

### 3. Get Article by ID

**GET /articles/{article_id}**

Retrieves the processed results for a specific article by ID.

**Parameters:**
- `article_id` (path, required): The ID of the processed article

**Response Example:**
```json
{
  "id": "20230329121530",
  "url": "https://example.com/news-article",
  "title": "Example News Article",
  "source": "Example News",
  "processed_at": "2023-03-29T12:15:30",
  "analysis_results": {
    "article_title": "Example News Article",
    "article_url": "https://example.com/news-article",
    "article_source": "Example News",
    "summary_result": "This is a summary of the article...",
    "fake_news_result": { /* ... */ },
    "credibility_result": { /* ... */ },
    "sentiment_result": { /* ... */ },
    "agents_called": ["fake_news", "credibility", "sentiment", "summary"]
  }
}
```

### 4. List Articles

**GET /articles**

Lists all processed articles.

**Response Example:**
```json
[
  {
    "id": "20230329121530",
    "url": "https://example.com/news-article",
    "title": "Example News Article",
    "source": "Example News",
    "processed_at": "2023-03-29T12:15:30",
    "analysis_results": { /* ... */ }
  },
  {
    "id": "20230329121545",
    "url": "https://example.com/another-article",
    "title": "Another News Article",
    "source": "Example News",
    "processed_at": "2023-03-29T12:15:45",
    "analysis_results": { /* ... */ }
  }
]
```

## Error Handling

The API returns appropriate HTTP status codes:

- `200 OK`: Request successful
- `404 Not Found`: Resource not found
- `400 Bad Request`: Invalid request parameters
- `500 Internal Server Error`: Server-side error

Error responses include a descriptive message:

```json
{
  "detail": "Article not found"
}
```

## Development Mode

The API includes mock implementations of OpenAI and search APIs for development. To use real APIs, set the environment variable `USE_MOCK_APIS=false` and provide your API keys. 