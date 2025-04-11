/**
 * Background script for the News Analyzer extension
 * Handles URL capture and backend communication
 */

// API endpoint for processing articles
const API_URL = 'http://localhost:8000/process';

// Track the last processed URL to avoid duplicate processing
let lastProcessedUrl: string | null = null;

// Track articles currently being processed
const pendingArticles = new Map<string, number>();

// Listen for tab updates to detect when a user navigates to a news article
chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
  // Only process when the page is fully loaded and has a URL
  if (changeInfo.status === 'complete' && tab.url) {
    // Check if the URL belongs to a news site
    if (isNewsSite(tab.url) && tab.url !== lastProcessedUrl) {
      console.log('Detected news article:', tab.url);
      
      // Get tab information (title and URL)
      chrome.tabs.get(tabId, (tab) => {
        if (tab.url && tab.title) {
          processArticle(tab.url, tab.title);
          lastProcessedUrl = tab.url;
        }
      });
    }
  }
});

// Process a news article - send it to the backend for analysis
async function processArticle(url: string, title: string): Promise<void> {
  try {
    console.log('Processing article:', url);
    
    // Get article content
    let canonicalUrl = url;
    let source = extractSource(url);
    
    try {
      // Try to get more accurate URL and content from the page
      const tabId = await getCurrentTabId();
      if (tabId) {
        const response = await chrome.tabs.sendMessage(tabId, { action: 'getPageContent' });
        if (response) {
          if (response.canonicalUrl) {
            canonicalUrl = response.canonicalUrl;
            console.log('Using canonical URL:', canonicalUrl);
          }
          if (response.source) {
            source = response.source;
            console.log('Using source from page:', source);
          }
        }
      }
    } catch (error) {
      console.warn('Could not get page information:', error);
    }
    
    // Check if we already have cached results in storage
    const cachedResults = await getCachedResults(canonicalUrl);
    if (cachedResults) {
      console.log('Using cached results for:', canonicalUrl);
      
      // Update badge to indicate we have cached results
      chrome.action.setBadgeText({ text: '✓' });
      chrome.action.setBadgeBackgroundColor({ color: '#4CAF50' });
      
      return;
    }
    
    // Check if this URL is already pending
    if (pendingArticles.has(canonicalUrl)) {
      const timestamp = pendingArticles.get(canonicalUrl);
      const now = Date.now();
      // If it's been less than 60 seconds, don't resubmit
      if (timestamp && now - timestamp < 60000) {
        console.log('Article already being processed:', canonicalUrl);
        
        // Update badge to indicate processing
        chrome.action.setBadgeText({ text: '...' });
        chrome.action.setBadgeBackgroundColor({ color: '#FFA000' });
        
        return;
      }
    }
    
    // Set badge to indicate processing
    chrome.action.setBadgeText({ text: '...' });
    chrome.action.setBadgeBackgroundColor({ color: '#FFA000' });
    
    // Mark this URL as pending
    pendingArticles.set(canonicalUrl, Date.now());
    
    // Send the article URL to the backend
    const response = await fetch(API_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        url: canonicalUrl,
        title: title,
        source: source
      }),
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error! Status: ${response.status}`);
    }
    
    const data = await response.json();
    
    // Save the results in local storage
    if (data.results) {
      await saveResults(canonicalUrl, data.results);
      
      // Update badge to indicate success
      chrome.action.setBadgeText({ text: '✓' });
      chrome.action.setBadgeBackgroundColor({ color: '#4CAF50' });
      
      // Remove from pending list
      pendingArticles.delete(canonicalUrl);
    } else if (data.cached) {
      // Already processed, just update badge
      chrome.action.setBadgeText({ text: '✓' });
      chrome.action.setBadgeBackgroundColor({ color: '#4CAF50' });
      
      // Remove from pending list
      pendingArticles.delete(canonicalUrl);
    } else {
      // Processing started but not complete, keep in pending list
      console.log('Article processing started for:', canonicalUrl);
    }
    
    console.log('Article processing response:', data);
  } catch (error) {
    console.error('Error processing article:', error);
    
    // Update badge to indicate error
    chrome.action.setBadgeText({ text: '!' });
    chrome.action.setBadgeBackgroundColor({ color: '#F44336' });
  }
}

// Check if a URL is from a news site
function isNewsSite(url: string): boolean {
  // List of common news domains
  const newsDomains = [
    'bbc.com', 'bbc.co.uk', 'cnn.com', 'nytimes.com', 'washingtonpost.com',
    'theguardian.com', 'reuters.com', 'apnews.com', 'aljazeera.com',
    'economist.com', 'bloomberg.com', 'wsj.com', 'ft.com', 'foxnews.com',
    'nbcnews.com', 'abcnews.go.com', 'cbsnews.com', 'npr.org', 'politico.com',
    'thehill.com', 'time.com', 'newsweek.com', 'usatoday.com', 'latimes.com',
    'chicagotribune.com', 'nypost.com', 'thedailybeast.com', 'huffpost.com',
    'vox.com', 'slate.com', 'salon.com', 'motherjones.com', 'breitbart.com',
    'dailymail.co.uk', 'telegraph.co.uk', 'independent.co.uk', 'news.sky.com',
    'news.yahoo.com', 'news.google.com'
  ];
  
  try {
    const hostname = new URL(url).hostname;
    return newsDomains.some(domain => hostname.includes(domain));
  } catch (e) {
    return false;
  }
}

// Extract the source name from the URL
function extractSource(url: string): string | null {
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
    return null;
  }
}

// Save processing results to local storage
async function saveResults(url: string, results: any): Promise<void> {
  return new Promise((resolve) => {
    chrome.storage.local.get('processedArticles', (data) => {
      const processedArticles = data.processedArticles || {};
      
      // Add the new results
      processedArticles[url] = {
        results: results,
        timestamp: Date.now()
      };
      
      // Save back to storage
      chrome.storage.local.set({ processedArticles }, () => {
        resolve();
      });
    });
  });
}

// Get cached results from local storage
async function getCachedResults(url: string): Promise<any | null> {
  return new Promise((resolve) => {
    chrome.storage.local.get('processedArticles', (data) => {
      const processedArticles = data.processedArticles || {};
      
      if (processedArticles[url]) {
        // Check if the cache is fresh (less than 24 hours old)
        const cacheTime = processedArticles[url].timestamp;
        const now = Date.now();
        const maxAge = 24 * 60 * 60 * 1000; // 24 hours in milliseconds
        
        if (now - cacheTime < maxAge) {
          resolve(processedArticles[url].results);
          return;
        }
      }
      
      resolve(null);
    });
  });
}

// Listen for messages from the popup or content script
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  console.log('Background script received message:', message);
  
  // Handle content script loaded notification
  if (message.action === 'contentScriptLoaded') {
    console.log('Content script loaded in tab with URL:', message.url);
    // If it's a news site, we could pre-fetch results
    if (isNewsSite(message.url)) {
      console.log('News site detected in tab, will track for analysis');
    }
    return false;
  }
  
  // Handle content script ping
  if (message.action === 'contentScriptPing') {
    // Just acknowledge the ping
    return false;
  }
  
  if (message.action === 'getResults') {
    console.log('Handling getResults action');
    
    // Get the current tab URL
    chrome.tabs.query({ active: true, currentWindow: true }, async (tabs) => {
      if (tabs.length > 0 && tabs[0].url) {
        const url = tabs[0].url;
        console.log('Popup requested results for URL:', url);
        
        try {
          // Check for cached results
          const results = await getCachedResults(url);
          
          if (results) {
            console.log('Found cached results for:', url);
            sendResponse({ results });
          } else {
            // Try with normalized URL (without query parameters)
            console.log('No results for exact URL, trying to normalize URL...');
            const normalizedUrl = normalizeUrl(url);
            console.log('Normalized URL:', normalizedUrl);
            
            if (normalizedUrl !== url) {
              const normalizedResults = await getCachedResults(normalizedUrl);
              if (normalizedResults) {
                console.log('Found cached results for normalized URL:', normalizedUrl);
                sendResponse({ results: normalizedResults });
                return;
              }
            }
            
            // No results found, check if URL is from a news site
            if (isNewsSite(url)) {
              console.log('No cached results found for news site:', url);
              // Try to automatically process if it's a news site
              try {
                // Get more info from the page for processing
                const tabId = tabs[0].id;
                const title = tabs[0].title || '';
                
                if (tabId) {
                  console.log('Requesting page content from tab:', tabId);
                  
                  try {
                    const contentResponse = await chrome.tabs.sendMessage(tabId, { 
                      action: 'getPageContent' 
                    });
                    
                    console.log('Content response received:', contentResponse);
                    
                    if (contentResponse) {
                      // We got content from the page, initiate processing right away
                      const processingStarted = await initiateProcessing(
                        contentResponse.canonicalUrl || url,
                        contentResponse.title || title,
                        contentResponse.source || extractSource(url)
                      );
                      
                      if (processingStarted) {
                        sendResponse({ 
                          error: 'Article processing initiated. Please wait a moment and try again.' 
                        });
                        return;
                      }
                    }
                  } catch (contentError) {
                    console.error('Error getting page content:', contentError);
                    // Continue with basic URL processing if content script fails
                  }
                }
                
                // If content script fails or returns no data, use basic URL info
                const processingStarted = await initiateProcessing(
                  url, 
                  title,
                  extractSource(url)
                );
                
                if (processingStarted) {
                  sendResponse({ 
                    error: 'Article processing initiated. Please wait a moment and try again.' 
                  });
                  return;
                }
              } catch (processingError) {
                console.error('Error initiating processing:', processingError);
              }
            }
            
            console.log('No cached results found for URL:', url);
            sendResponse({ error: 'No results available for this article' });
          }
        } catch (error: unknown) {
          console.error('Error retrieving results:', error);
          const errorMessage = error instanceof Error ? error.message : 'Unknown error';
          sendResponse({ error: 'Error retrieving results: ' + errorMessage });
        }
      } else {
        console.log('No active tab found for getResults request');
        sendResponse({ error: 'No active tab found' });
      }
    });
    
    // Return true to indicate we'll respond asynchronously
    return true;
  }
});

// Normalize URL by removing query parameters and fragments
function normalizeUrl(url: string): string {
  try {
    const urlObj = new URL(url);
    // Return only the origin and pathname parts
    return urlObj.origin + urlObj.pathname;
  } catch (e) {
    console.error('Error normalizing URL:', e);
    return url;
  }
}

// Get the current tab ID
async function getCurrentTabId(): Promise<number | null> {
  return new Promise((resolve) => {
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
      if (tabs.length > 0 && tabs[0].id !== undefined) {
        resolve(tabs[0].id);
      } else {
        resolve(null);
      }
    });
  });
}

// Initiate article processing with the backend
async function initiateProcessing(url: string, title: string, source: string | null): Promise<boolean> {
  try {
    console.log('Initiating processing for:', url);
    
    // Mark this URL as pending
    pendingArticles.set(url, Date.now());
    
    // Update badge to indicate processing
    chrome.action.setBadgeText({ text: '...' });
    chrome.action.setBadgeBackgroundColor({ color: '#FFA000' });
    
    // Send the article URL to the backend
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
    
    if (!response.ok) {
      throw new Error(`HTTP error! Status: ${response.status}`);
    }
    
    const data = await response.json();
    console.log('Processing initiation response:', data);
    
    // If results are immediately available, save them
    if (data.results) {
      await saveResults(url, data.results);
      pendingArticles.delete(url);
      
      // Update badge to indicate success
      chrome.action.setBadgeText({ text: '✓' });
      chrome.action.setBadgeBackgroundColor({ color: '#4CAF50' });
    }
    
    return true;
  } catch (error) {
    console.error('Error initiating processing:', error);
    pendingArticles.delete(url);
    return false;
  }
} 