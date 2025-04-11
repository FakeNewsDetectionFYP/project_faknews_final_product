/**
 * Content script for the News Analyzer extension
 * Runs on news article pages and communicates with the backend
 */

console.log('News Analyzer content script loaded');

// Send a message to the background script to notify that content script is loaded
chrome.runtime.sendMessage({ 
  action: 'contentScriptLoaded', 
  url: window.location.href,
  title: document.title
});

// Listen for messages from the background script or popup
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  console.log('Content script received message:', message);
  
  if (message.action === 'getPageContent') {
    console.log('Extracting page content...');
    // Extract article content and metadata from the page
    const articleData = extractArticleData();
    console.log('Extracted article data:', articleData);
    sendResponse(articleData);
  }
  
  // Return true to indicate we might respond asynchronously
  return true;
});

// Ping the background script every 5 seconds to ensure connection
setInterval(() => {
  try {
    chrome.runtime.sendMessage({ 
      action: 'contentScriptPing',
      url: window.location.href
    });
  } catch (e) {
    console.error('Failed to ping background script:', e);
  }
}, 5000);

/**
 * Extract all relevant article data from the page
 */
function extractArticleData() {
  const content = extractArticleContent();
  const canonicalUrl = getCanonicalUrl();
  const source = getArticleSource();
  
  console.log('Extracted canonical URL:', canonicalUrl);
  console.log('Extracted source:', source);
  console.log('Content extracted:', content ? 'Yes' : 'No');
  
  return {
    content: content,
    url: window.location.href,
    title: document.title,
    canonicalUrl: canonicalUrl,
    metaDescription: getMetaDescription(),
    author: getArticleAuthor(),
    publishDate: getArticleDate(),
    source: source
  };
}

/**
 * Get the canonical URL if available
 */
function getCanonicalUrl(): string | null {
  // Try canonical link tag first (most reliable)
  const canonicalLink = document.querySelector('link[rel="canonical"]');
  if (canonicalLink && canonicalLink.getAttribute('href')) {
    return canonicalLink.getAttribute('href');
  }
  
  // Try Open Graph URL (often used for social sharing)
  const ogUrlMeta = document.querySelector('meta[property="og:url"]');
  if (ogUrlMeta && ogUrlMeta.getAttribute('content')) {
    return ogUrlMeta.getAttribute('content');
  }
  
  return null;
}

/**
 * Get meta description for additional context
 */
function getMetaDescription(): string | null {
  const metaDesc = document.querySelector('meta[name="description"]');
  if (metaDesc && metaDesc.getAttribute('content')) {
    return metaDesc.getAttribute('content');
  }
  
  const ogDesc = document.querySelector('meta[property="og:description"]');
  if (ogDesc && ogDesc.getAttribute('content')) {
    return ogDesc.getAttribute('content');
  }
  
  return null;
}

/**
 * Get article author if available
 */
function getArticleAuthor(): string | null {
  // Try common author meta tags
  const metaAuthor = document.querySelector('meta[name="author"]');
  if (metaAuthor && metaAuthor.getAttribute('content')) {
    return metaAuthor.getAttribute('content');
  }
  
  // Try schema.org markup
  const schemaAuthor = document.querySelector('[itemprop="author"]');
  if (schemaAuthor) {
    return schemaAuthor.textContent?.trim() || null;
  }
  
  return null;
}

/**
 * Get article publication date if available
 */
function getArticleDate(): string | null {
  // Try common date meta tags
  const metaDate = document.querySelector('meta[property="article:published_time"]');
  if (metaDate && metaDate.getAttribute('content')) {
    return metaDate.getAttribute('content');
  }
  
  // Try schema.org markup
  const schemaDate = document.querySelector('[itemprop="datePublished"]');
  if (schemaDate) {
    return schemaDate.getAttribute('content') || schemaDate.textContent?.trim() || null;
  }
  
  return null;
}

/**
 * Get article source/publication name
 */
function getArticleSource(): string | null {
  // Try common publisher meta tags
  const siteName = document.querySelector('meta[property="og:site_name"]');
  if (siteName && siteName.getAttribute('content')) {
    return siteName.getAttribute('content');
  }
  
  // Try schema.org markup
  const schemaPublisher = document.querySelector('[itemprop="publisher"] [itemprop="name"]');
  if (schemaPublisher) {
    return schemaPublisher.textContent?.trim() || null;
  }
  
  // Fallback: Extract from domain
  try {
    const hostname = new URL(window.location.href).hostname;
    return hostname.replace('www.', '').split('.')[0];
  } catch (e) {
    return null;
  }
}

/**
 * Extract the main content of a news article from the current page
 * This is a basic implementation that will need customization for different news sites
 */
function extractArticleContent(): string | null {
  // Try different selectors commonly used for article content
  const selectors = [
    // Common article content selectors
    'article',
    '[itemprop="articleBody"]',
    '.article-body',
    '.story-body',
    '.story-content',
    '.article-content',
    '.entry-content',
    '.post-content',
    '#article-body',
    '.news-article'
  ];

  // Try each selector until we find content
  for (const selector of selectors) {
    const element = document.querySelector(selector);
    if (element && element.textContent && element.textContent.trim().length > 100) {
      return element.textContent.trim();
    }
  }

  // Fallback to looking for large text blocks
  const paragraphs = Array.from(document.querySelectorAll('p'));
  if (paragraphs.length > 3) {
    // If we have multiple paragraphs, combine them (likely an article)
    return paragraphs
      .map(p => p.textContent?.trim() || '')
      .filter(text => text.length > 30)  // Exclude short paragraphs
      .join('\n\n');
  }

  // Couldn't extract meaningful content
  return null;
} 