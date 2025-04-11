/**
 * Test API Popup Script
 * Used for testing API communications between the extension and backend
 */

// API endpoint for processing articles
const API_URL = 'http://localhost:8000/process';
const API_ARTICLES_URL = 'http://localhost:8000/articles';
const API_HEALTH_URL = 'http://localhost:8000/';

document.addEventListener('DOMContentLoaded', () => {
  // Get DOM elements
  const extractUrlBtn = document.getElementById('extract-url');
  const testApiBtn = document.getElementById('test-api');
  const testApiAllBtn = document.getElementById('test-api-all');
  const showCacheBtn = document.getElementById('show-cache');
  const clearCacheBtn = document.getElementById('clear-cache');
  const customUrlInput = document.getElementById('custom-url');
  const urlResult = document.getElementById('url-result');
  const apiResult = document.getElementById('api-result');
  const cacheResult = document.getElementById('cache-result');

  // Extracted page information
  let extractedInfo = null;

  // Extract URL from the current page
  extractUrlBtn.addEventListener('click', async () => {
    urlResult.textContent = 'Extracting URL and content...';
    
    try {
      // Query for the active tab
      const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
      
      if (!tab || !tab.id) {
        throw new Error('No active tab found');
      }
      
      // Send message to content script to extract the page content
      const response = await chrome.tabs.sendMessage(tab.id, { action: 'getPageContent' });
      
      extractedInfo = response;
      
      // Format response for display
      if (response) {
        // Update the custom URL input with the canonical URL if available
        if (response.canonicalUrl) {
          customUrlInput.value = response.canonicalUrl;
        } else {
          customUrlInput.value = response.url;
        }
        
        // Show extracted data
        urlResult.innerHTML = `<strong>URL:</strong> ${response.url}\n` +
          `<strong>Canonical URL:</strong> ${response.canonicalUrl || 'Not available'}\n` +
          `<strong>Title:</strong> ${response.title || 'Not available'}\n` +
          `<strong>Content extracted:</strong> ${response.content ? 'Yes' : 'No'}\n` +
          (response.content ? `<strong>Content preview:</strong> ${truncate(response.content, 150)}` : '');
      } else {
        urlResult.textContent = 'No content extracted. Make sure you are on a news article page.';
      }
    } catch (error) {
      urlResult.textContent = `Error extracting content: ${error.message}`;
      console.error('Error extracting content:', error);
    }
  });

  // Test API with current URL
  testApiBtn.addEventListener('click', async () => {
    const url = customUrlInput.value.trim();
    
    if (!url) {
      apiResult.textContent = 'Please enter a URL or extract one from the current page first.';
      return;
    }
    
    apiResult.textContent = 'Testing API...';
    
    try {
      // Get title from extracted info or use a default
      const title = (extractedInfo && extractedInfo.title) 
        ? extractedInfo.title 
        : 'Test Article';
      
      // Get source from extracted info or derive from URL
      const source = (extractedInfo && extractedInfo.source) 
        ? extractedInfo.source 
        : extractSourceFromURL(url);
      
      // Call the process API
      const response = await fetch(API_URL, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          url: url,
          title: title,
          source: source
        }),
      });
      
      const data = await response.json();
      
      apiResult.innerHTML = `<span class="success">API Test successful!</span>\n` +
        `<strong>Status:</strong> ${response.status} ${response.statusText}\n` +
        `<strong>Response:</strong>\n${JSON.stringify(data, null, 2)}`;
    } catch (error) {
      apiResult.innerHTML = `<span class="error">API Test failed!</span>\n` +
        `<strong>Error:</strong> ${error.message}\n` +
        `<strong>Details:</strong> Make sure the backend server is running at ${API_URL}.`;
      console.error('API test error:', error);
    }
  });

  // Test all API endpoints
  testApiAllBtn.addEventListener('click', async () => {
    apiResult.textContent = 'Testing all API endpoints...';
    
    const results = {};
    
    try {
      // Test health endpoint
      try {
        const healthResponse = await fetch(API_HEALTH_URL);
        results.health = {
          status: healthResponse.status,
          data: await healthResponse.json()
        };
      } catch (error) {
        results.health = { error: error.message };
      }
      
      // Test articles endpoint
      try {
        const articlesResponse = await fetch(API_ARTICLES_URL);
        results.articles = {
          status: articlesResponse.status,
          data: await articlesResponse.json()
        };
      } catch (error) {
        results.articles = { error: error.message };
      }
      
      // Test process endpoint with a dummy URL
      try {
        const dummyURL = 'https://example.com/test-article';
        const processResponse = await fetch(API_URL, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            url: dummyURL,
            title: 'Test Article',
            source: 'Example'
          }),
        });
        results.process = {
          status: processResponse.status,
          data: await processResponse.json()
        };
      } catch (error) {
        results.process = { error: error.message };
      }
      
      // Display results
      const allSuccessful = Object.values(results).every(r => !r.error);
      
      apiResult.innerHTML = `<span class="${allSuccessful ? 'success' : 'error'}">` +
        `API Tests ${allSuccessful ? 'successful' : 'partially failed'}!</span>\n` +
        `<strong>Results:</strong>\n${JSON.stringify(results, null, 2)}`;
    } catch (error) {
      apiResult.innerHTML = `<span class="error">API Tests failed!</span>\n` +
        `<strong>Error:</strong> ${error.message}`;
      console.error('API tests error:', error);
    }
  });

  // Show cached results
  showCacheBtn.addEventListener('click', async () => {
    cacheResult.textContent = 'Loading cache...';
    
    try {
      const data = await new Promise(resolve => {
        chrome.storage.local.get('processedArticles', data => {
          resolve(data.processedArticles || {});
        });
      });
      
      if (Object.keys(data).length === 0) {
        cacheResult.textContent = 'No cached articles found.';
      } else {
        // Format for better readability
        const formattedCache = {};
        for (const [url, entry] of Object.entries(data)) {
          formattedCache[url] = {
            timestamp: new Date(entry.timestamp).toLocaleString(),
            results: entry.results
          };
        }
        
        cacheResult.textContent = JSON.stringify(formattedCache, null, 2);
      }
    } catch (error) {
      cacheResult.textContent = `Error loading cache: ${error.message}`;
      console.error('Error loading cache:', error);
    }
  });

  // Clear cached results
  clearCacheBtn.addEventListener('click', async () => {
    try {
      await new Promise(resolve => {
        chrome.storage.local.remove('processedArticles', () => {
          resolve();
        });
      });
      
      cacheResult.textContent = 'Cache cleared successfully!';
    } catch (error) {
      cacheResult.textContent = `Error clearing cache: ${error.message}`;
      console.error('Error clearing cache:', error);
    }
  });
});

// Helper function to truncate text
function truncate(text, maxLength) {
  if (!text) return '';
  return text.length > maxLength ? text.substring(0, maxLength) + '...' : text;
}

// Extract source name from URL
function extractSourceFromURL(url) {
  try {
    const hostname = new URL(url).hostname;
    
    // Remove www. and .com/.net/etc.
    const parts = hostname.split('.');
    if (parts.length >= 2) {
      if (parts[0] === 'www') {
        return parts[1];
      }
      return parts[0];
    }
    
    return hostname;
  } catch (e) {
    return 'Unknown Source';
  }
} 