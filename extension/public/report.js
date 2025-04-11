// Report.js - Handles detailed visualization of article analysis

document.addEventListener('DOMContentLoaded', async function() {
  try {
    // Set up back button functionality
    const backButton = document.getElementById('back-button');
    if (backButton) {
      backButton.addEventListener('click', function() {
        // Close this tab and go back to the popup
        window.close();
      });
    }
    
    // Get the URL parameter containing the article URL
    const urlParams = new URLSearchParams(window.location.search);
    const articleUrl = urlParams.get('url');
    
    if (!articleUrl) {
      showError('No article URL provided');
      return;
    }
    
    // Get the analysis results from chrome storage
    await loadResults(articleUrl);
    
  } catch (error) {
    console.error('Error loading report:', error);
    showError(`Failed to load report: ${error.message}`);
  }
});

// Load analysis results from chrome storage
async function loadResults(url) {
  return new Promise((resolve) => {
    console.log('Attempting to load results for URL:', url);
    
    chrome.storage.local.get('processedArticles', (data) => {
      console.log('Storage data received:', data);
      const processedArticles = data.processedArticles || {};
      
      if (processedArticles[url] && processedArticles[url].results) {
        console.log('Found results for URL:', url);
        const results = processedArticles[url].results;
        
        // Log found data for debugging
        console.log('Article title:', results.article_title);
        console.log('Article source:', results.article_source);
        console.log('Summary available:', !!results.summary_result);
        console.log('Credibility available:', !!results.credibility_result);
        console.log('Sentiment available:', !!results.sentiment_result);
        
        // Try to display results even if some parts are missing
        try {
          displayResults(results, url);
          resolve(results);
        } catch (error) {
          console.error('Error displaying results:', error);
          showError(`Error displaying results: ${error.message}`);
          resolve(null);
        }
      } else {
        // Check if we can find the URL with different normalization
        console.log('No direct match found, checking for similar URLs...');
        
        // Try to find a match by ignoring query parameters or fragments
        const normalizedUrl = normalizeUrl(url);
        console.log('Normalized URL:', normalizedUrl);
        
        const matchingUrls = Object.keys(processedArticles).filter(storedUrl => {
          return normalizeUrl(storedUrl) === normalizedUrl;
        });
        
        if (matchingUrls.length > 0) {
          console.log('Found matching URL:', matchingUrls[0]);
          const results = processedArticles[matchingUrls[0]].results;
          displayResults(results, url);
          resolve(results);
          return;
        }
        
        console.error('No analysis results found for:', url);
        showError('No analysis results found for this article. Please analyze the article first from the extension popup.');
        resolve(null);
      }
    });
  });
}

// Simple URL normalizer to help with matching
function normalizeUrl(url) {
  try {
    const urlObj = new URL(url);
    return urlObj.origin + urlObj.pathname;
  } catch (e) {
    console.error('Error normalizing URL:', e);
    return url;
  }
}

// Display all the analysis results
function displayResults(results, url) {
  console.log('Displaying results:', results);
  
  // Set article info
  document.getElementById('article-title').textContent = results.article_title || 'Unknown Article';
  document.getElementById('article-source').textContent = `Source: ${results.article_source || 'Unknown Source'}`;
  
  const articleLink = document.getElementById('article-url');
  articleLink.href = url;
  
  // Check for summary data in different possible locations
  const summaryElement = document.getElementById('article-summary');
  const summarySection = document.getElementById('summary-section');
  
  if (summaryElement && summarySection) {
    // Check all possible places where summary might be stored
    if (results.summary_result && typeof results.summary_result === 'string') {
      console.log('Found summary_result:', results.summary_result.substring(0, 50) + '...');
      summaryElement.textContent = results.summary_result;
    } else if (results.summary && typeof results.summary === 'string') {
      console.log('Found summary:', results.summary.substring(0, 50) + '...');
      summaryElement.textContent = results.summary;
    } else if (results.summary_agent_result && typeof results.summary_agent_result === 'string') {
      console.log('Found summary_agent_result:', results.summary_agent_result.substring(0, 50) + '...');
      summaryElement.textContent = results.summary_agent_result;
    } else {
      // If we check the full results object for any property that might contain the summary
      const possibleSummaryKey = Object.keys(results).find(key => 
        (key.includes('summary') && typeof results[key] === 'string' && results[key].length > 50)
      );
      
      if (possibleSummaryKey) {
        console.log('Found potential summary in:', possibleSummaryKey);
        summaryElement.textContent = results[possibleSummaryKey];
      } else {
        console.log('No summary found in any expected location');
        summaryElement.textContent = 'No summary available for this article.';
      }
    }
  }
  
  // Display credibility results
  displayCredibilityResults(results.credibility_result);
  
  // Display sentiment results
  displaySentimentResults(results.sentiment_result);
}

// Display credibility analysis results
function displayCredibilityResults(credibility) {
  if (!credibility) {
    hideSection('credibility-section');
    return;
  }
  
  console.log('Displaying credibility data:', credibility);
  
  // Get score elements
  const overallScoreElement = document.getElementById('overall-credibility-score');
  const overallScoreValue = overallScoreElement.querySelector('.score-value');
  
  // Source reputation
  const sourceReputationScore = document.getElementById('source-reputation-score');
  const sourceReputationReasoning = document.getElementById('source-reputation-reasoning');
  
  // Title-content alignment
  const titleContentScore = document.getElementById('title-content-score');
  const titleContentReasoning = document.getElementById('title-content-reasoning');
  
  // Misleading title
  const misleadingTitlesScore = document.getElementById('misleading-titles-score');
  const misleadingTitlesReasoning = document.getElementById('misleading-titles-reasoning');
  
  // Overall conclusion
  const overallConclusion = document.getElementById('overall-conclusion');
  
  // Set values
  
  // Overall score
  let overallScore = 0;
  if (typeof credibility.overall_credibility === 'number') {
    // Convert from 0-1 scale to 0-100
    overallScore = Math.round(credibility.overall_credibility * 100);
  } else if (typeof credibility.averageScore === 'number') {
    overallScore = Math.round(credibility.averageScore);
  }
  
  overallScoreValue.textContent = overallScore;
  setScoreColor(overallScoreElement, overallScore);
  
  // Source reputation
  if (typeof credibility.source_reputation === 'number') {
    // Convert from 0-1 scale to 0-100
    const score = Math.round(credibility.source_reputation * 100);
    sourceReputationScore.textContent = score;
    setScoreColor(sourceReputationScore, score);
  } else if (typeof credibility.sourceReputationScore === 'number') {
    sourceReputationScore.textContent = Math.round(credibility.sourceReputationScore);
    setScoreColor(sourceReputationScore, credibility.sourceReputationScore);
  }
  
  // Set source reputation reasoning with detailed explanation
  if (credibility.sourceReputationReasoning) {
    sourceReputationReasoning.textContent = credibility.sourceReputationReasoning;
  } else {
    sourceReputationReasoning.textContent = "No detailed reasoning available.";
  }
  
  // Title content
  if (typeof credibility.title_content_alignment === 'number') {
    // Convert from 0-1 scale to 0-100
    const score = Math.round(credibility.title_content_alignment * 100);
    titleContentScore.textContent = score;
    setScoreColor(titleContentScore, score);
  } else if (typeof credibility.titleContentScore === 'number') {
    titleContentScore.textContent = Math.round(credibility.titleContentScore);
    setScoreColor(titleContentScore, credibility.titleContentScore);
  }
  
  // Set title content reasoning with detailed explanation
  if (credibility.titleContentReasoning) {
    titleContentReasoning.textContent = credibility.titleContentReasoning;
  } else {
    titleContentReasoning.textContent = "No detailed reasoning available.";
  }
  
  // Misleading titles
  if (typeof credibility.misleadingTitlesScore === 'number') {
    misleadingTitlesScore.textContent = Math.round(credibility.misleadingTitlesScore);
    setScoreColor(misleadingTitlesScore, credibility.misleadingTitlesScore);
  }
  
  // Set misleading titles reasoning with detailed explanation
  if (credibility.misleadingTitlesReasoning) {
    misleadingTitlesReasoning.textContent = credibility.misleadingTitlesReasoning;
  } else {
    misleadingTitlesReasoning.textContent = "No detailed reasoning available.";
  }
  
  // Overall conclusion
  if (credibility.evaluation) {
    overallConclusion.textContent = credibility.evaluation;
  } else if (credibility.overallConclusion) {
    overallConclusion.textContent = credibility.overallConclusion;
  } else {
    overallConclusion.textContent = "No overall conclusion available.";
  }
  
  // Create the radar chart for credibility scores
  createCredibilityChart(credibility);
}

// Display sentiment analysis results
function displaySentimentResults(sentiment) {
  if (!sentiment) {
    hideSection('sentiment-section');
    return;
  }
  
  console.log('Displaying sentiment data:', sentiment);
  
  // Set polarity meter
  const polarityMeter = document.getElementById('polarity-meter');
  let polarityValue = 50; // neutral default
  
  if (sentiment.polarity !== undefined) {
    // Convert -1 to 1 scale to 0 to 100
    polarityValue = (sentiment.polarity + 1) * 50;
  } else if (sentiment.sentiment_score !== undefined) {
    polarityValue = sentiment.sentiment_score;
  }
  
  polarityMeter.style.width = `${polarityValue}%`;
  
  // Set subjectivity meter
  const subjectivityMeter = document.getElementById('subjectivity-meter');
  let subjectivityValue = 50; // mixed default
  
  if (sentiment.subjectivity !== undefined) {
    // Convert 0 to 1 scale to 0 to 100
    subjectivityValue = sentiment.subjectivity * 100;
  }
  
  subjectivityMeter.style.width = `${subjectivityValue}%`;
  
  // Set emotional tone
  if (sentiment.emotional_tone) {
    document.getElementById('emotional-tone').textContent = sentiment.emotional_tone;
  }
  
  // Set bias assessment
  if (sentiment.bias_assessment) {
    document.getElementById('bias-assessment').textContent = sentiment.bias_assessment;
  }
  
  // Set justification with detailed information
  const justificationElement = document.getElementById('sentiment-justification');
  if (justificationElement) {
    // Clear existing content first
    justificationElement.innerHTML = '';
    
    // Check if we have detailed justification array
    if (sentiment.detailed_justification && Array.isArray(sentiment.detailed_justification) && sentiment.detailed_justification.length > 0) {
      // Create a list from detailed justifications
      const list = document.createElement('ul');
      sentiment.detailed_justification.forEach(reason => {
        const item = document.createElement('li');
        item.textContent = reason;
        list.appendChild(item);
      });
      justificationElement.appendChild(list);
      
      // Add key phrases if available
      if (sentiment.key_phrases && Array.isArray(sentiment.key_phrases) && sentiment.key_phrases.length > 0) {
        const phrasesHeader = document.createElement('h5');
        phrasesHeader.textContent = 'Key Phrases:';
        justificationElement.appendChild(phrasesHeader);
        
        const phrasesList = document.createElement('ul');
        phrasesList.className = 'key-phrases-list';
        sentiment.key_phrases.forEach(phrase => {
          const item = document.createElement('li');
          item.textContent = `"${phrase}"`;
          phrasesList.appendChild(item);
        });
        justificationElement.appendChild(phrasesList);
      }
    } else if (sentiment.justification) {
      // Just use the main justification text
      justificationElement.textContent = sentiment.justification;
    } else {
      justificationElement.textContent = "No justification available.";
    }
  }
}

// Create radar chart for credibility scores
function createCredibilityChart(credibility) {
  const ctx = document.getElementById('credibility-chart').getContext('2d');
  
  // Prepare data
  let sourceReputation = 0;
  let titleContentAlignment = 0;
  let misleadingTitleScore = 0;
  
  // Try to get source reputation score, checking both the 0-1 scale and 0-100 scale values
  if (typeof credibility.source_reputation === 'number') {
    // Convert from 0-1 scale to 0-100
    sourceReputation = Math.round(credibility.source_reputation * 100);
  } else if (typeof credibility.sourceReputationScore === 'number') {
    sourceReputation = Math.round(credibility.sourceReputationScore);
  }
  
  // Try to get title-content alignment score, checking both scales
  if (typeof credibility.title_content_alignment === 'number') {
    // Convert from 0-1 scale to 0-100
    titleContentAlignment = Math.round(credibility.title_content_alignment * 100);
  } else if (typeof credibility.titleContentScore === 'number') {
    titleContentAlignment = Math.round(credibility.titleContentScore);
  }
  
  // Try to get misleading title score
  if (typeof credibility.misleadingTitlesScore === 'number') {
    misleadingTitleScore = Math.round(credibility.misleadingTitlesScore);
  }
  
  console.log('Chart data:', {
    sourceReputation, 
    titleContentAlignment, 
    misleadingTitleScore
  });
  
  // Create chart
  const chart = new Chart(ctx, {
    type: 'radar',
    data: {
      labels: [
        'Source Reputation',
        'Title-Content Alignment',
        'Non-Misleading Title'
      ],
      datasets: [{
        label: 'Credibility Scores',
        data: [sourceReputation, titleContentAlignment, misleadingTitleScore],
        backgroundColor: 'rgba(52, 152, 219, 0.2)',
        borderColor: 'rgba(52, 152, 219, 1)',
        borderWidth: 2,
        pointBackgroundColor: 'rgba(52, 152, 219, 1)',
        pointBorderColor: '#fff',
        pointHoverBackgroundColor: '#fff',
        pointHoverBorderColor: 'rgba(52, 152, 219, 1)'
      }]
    },
    options: {
      scales: {
        r: {
          beginAtZero: true,
          max: 100,
          ticks: {
            stepSize: 20
          }
        }
      },
      plugins: {
        tooltip: {
          callbacks: {
            label: function(context) {
              const value = context.raw;
              return `Score: ${value}/100`;
            }
          }
        }
      }
    }
  });
}

// Set score color based on value
function setScoreColor(element, score) {
  if (score >= 80) {
    element.style.backgroundColor = 'var(--success-color)';
  } else if (score >= 60) {
    element.style.backgroundColor = 'var(--warning-color)';
  } else {
    element.style.backgroundColor = 'var(--danger-color)';
  }
}

// Hide a section that doesn't have data
function hideSection(sectionId) {
  const section = document.getElementById(sectionId);
  if (section) {
    section.style.display = 'none';
  }
}

// Show error message
function showError(message) {
  const container = document.querySelector('.container');
  const errorDiv = document.createElement('div');
  errorDiv.className = 'error-message';
  errorDiv.style.padding = '20px';
  errorDiv.style.backgroundColor = '#f8d7da';
  errorDiv.style.color = '#721c24';
  errorDiv.style.borderRadius = '5px';
  errorDiv.style.marginBottom = '20px';
  errorDiv.style.textAlign = 'center';
  
  errorDiv.textContent = message;
  
  // Add at the top
  container.insertBefore(errorDiv, container.firstChild);
} 