import React, { useEffect, useState } from 'react';
import ReactDOM from 'react-dom/client';
import './popup.css';

// Types for article analysis results
interface AnalysisResults {
  article_title?: string;
  article_url?: string;
  article_source?: string;
  summary_result?: string;
  fake_news_result?: {
    claims_analyzed?: number;
    claims_verified?: number;
    verification_score?: number;
    verified_claims?: Array<{
      claim: string;
      analysis: string;
      is_verified: boolean;
    }> | string[];
    unverified_claims?: Array<{
      claim: string;
      analysis: string;
      is_verified: boolean;
    }> | string[];
    all_claims?: Array<{
      claim: string;
      analysis: string;
      is_verified: boolean;
    }>;
  };
  credibility_result?: {
    source_reputation?: number;
    title_content_alignment?: number;
    overall_credibility?: number;
    evaluation?: string;
  };
  sentiment_result?: {
    polarity?: number;
    subjectivity?: number;
    emotional_tone?: string;
    bias_assessment?: string;
    justification?: string;
  };
  agents_called?: string[];
}

const Popup: React.FC = () => {
  const [loading, setLoading] = useState<boolean>(false); // Initially not loading
  const [results, setResults] = useState<AnalysisResults | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [processing, setProcessing] = useState<boolean>(false);
  const [activeTab, setActiveTab] = useState<string>('summary');
  const [currentUrl, setCurrentUrl] = useState<string>('');
  const [numClaims, setNumClaims] = useState<number>(2); // Default to 2 claims
  const [showSettings, setShowSettings] = useState<boolean>(false);
  const [initialized, setInitialized] = useState<boolean>(false); // Track if initial setup is done

  // Function to manually trigger processing
  const triggerProcessing = async () => {
    try {
      setProcessing(true);
      setLoading(true);
      setError('Processing article... This may take a moment.');
      
      // Get the current tab
      const tabs = await chrome.tabs.query({ active: true, currentWindow: true });
      if (!tabs || !tabs[0] || !tabs[0].url) {
        throw new Error('Could not determine current page URL');
      }
      
      const url = tabs[0].url;
      setCurrentUrl(url);
      const title = tabs[0].title || '';
      
      console.log('Triggering manual processing for:', url);
      
      // Call the processing API
      const API_URL = 'http://localhost:8000/process';
      const response = await fetch(API_URL, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          url: url,
          title: title,
          source: extractSourceFromUrl(url),
          num_claims: numClaims, // Pass the user-set number of claims
        }),
      });
      
      if (!response.ok) {
        throw new Error(`API error: ${response.status}`);
      }
      
      const data = await response.json();
      console.log('Processing API response:', data);
      
      if (data.cached && data.results) {
        // We have immediate results
        setResults(data.results);
        setError(null);
        setProcessing(false);
        setLoading(false);
      } else {
        // Processing started, but we need to wait
        setError('Analysis started. Please wait a moment and try again.');
        setTimeout(() => fetchResults(), 3000); // Try again after 3 seconds
      }
      
    } catch (err) {
      console.error('Error triggering processing:', err);
      setError(`Could not process article: ${err instanceof Error ? err.message : 'Unknown error'}`);
      setProcessing(false);
      setLoading(false);
    }
  };

  // Function to extract source from URL
  const extractSourceFromUrl = (url: string): string => {
    try {
      const hostname = new URL(url).hostname;
      // Remove www. and get domain name
      return hostname.replace('www.', '').split('.')[0];
    } catch (e) {
      return 'unknown';
    }
  };

  useEffect(() => {
    console.log('Popup mounted, initializing...');
    
    // Load user settings
    chrome.storage.local.get(['numClaims'], (result) => {
      if (result.numClaims) {
        setNumClaims(result.numClaims);
      }
    });
    
    // Check if the backend is accessible at all
    fetch('http://localhost:8000/')
      .then(response => {
        console.log('Backend server connection test:', response.status);
        setInitialized(true);
      })
      .catch(error => {
        console.error('Backend server connection failed:', error);
        setError('Backend server not running. Please start your backend server.');
        setInitialized(true);
      });
    
    // Get the current URL
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
      if (tabs && tabs[0] && tabs[0].url) {
        setCurrentUrl(tabs[0].url);
      }
    });
    
    // Don't auto-fetch results anymore
  }, []);

  // Function to check connection to backend
  const checkBackendConnection = async (): Promise<boolean> => {
    try {
      const response = await fetch('http://localhost:8000/', { method: 'GET' });
      return response.ok;
    } catch (error) {
      console.error('Backend connection check failed:', error);
      return false;
    }
  };

  // Fetch results for the current tab
  const fetchResults = async () => {
    try {
      setLoading(true);
      console.log('Fetching results from background script...');
      
      // First check if backend is running
      const isBackendRunning = await checkBackendConnection();
      if (!isBackendRunning) {
        setLoading(false);
        setError('Backend server not running. Please start your backend server.');
        return;
      }
      
      // Send message to background script
      chrome.runtime.sendMessage({ action: 'getResults' }, (response) => {
        setLoading(false);
        console.log('Received response from background script:', response);
        
        if (!response) {
          console.error('No response received from background script');
          setError('Failed to communicate with extension background. Please try reloading the extension.');
          return;
        }
        
        if (response.error) {
          console.log('Error from getResults:', response.error);
          setError(response.error);
        } else if (response.results) {
          console.log('Results received:', response.results);
          setResults(response.results);
          setError(null);
          setProcessing(false);
        } else {
          console.error('Response did not contain results or error');
          setError('Invalid response from extension. Please try reloading the extension.');
        }
      });
    } catch (err) {
      console.error('Error in fetchResults:', err);
      setLoading(false);
      setError(`An error occurred while fetching results: ${err instanceof Error ? err.message : 'Unknown error'}`);
    }
  };

  // Function to render credibility score as color-coded label
  const renderScoreLabel = (score: number | undefined) => {
    if (score === undefined) return null;
    
    let color = '#F44336'; // Red
    let label = 'Low';
    
    if (score >= 0.7) {
      color = '#4CAF50'; // Green
      label = 'High';
    } else if (score >= 0.4) {
      color = '#FFA000'; // Orange
      label = 'Medium';
    }
    
    return (
      <span style={{ 
        backgroundColor: color, 
        color: 'white', 
        padding: '3px 8px', 
        borderRadius: '10px',
        fontSize: '12px',
        fontWeight: 'bold'
      }}>
        {label} ({Math.round(score * 100)}%)
      </span>
    );
  };

  // Function to test the API connection directly
  const testAPIDirectly = async (): Promise<void> => {
    try {
      setProcessing(true);
      setError('Testing direct API connection...');
      
      // Make a simple request to the API
      const response = await fetch('http://localhost:8000');
      if (!response.ok) {
        throw new Error(`API returned ${response.status}`);
      }
      
      console.log('Direct API test succeeded:', await response.json());
      
      // Try to fetch the articles list
      const articlesResponse = await fetch('http://localhost:8000/articles');
      const articlesData = await articlesResponse.json();
      console.log('Articles list:', articlesData);
      
      // If we get here, the API is working
      setProcessing(false);
      setError('API connection successful! Check console for details.');
    } catch (err) {
      console.error('Direct API test failed:', err);
      setProcessing(false);
      setError(`API connection failed: ${err instanceof Error ? err.message : 'Unknown error'}`);
    }
  };

  // Check if we have detailed claim analysis
  const hasDetailedClaimAnalysis = (fakeNewsResult?: AnalysisResults['fake_news_result']): boolean => {
    if (!fakeNewsResult) return false;
    
    // Check if we have all_claims
    if (fakeNewsResult.all_claims && fakeNewsResult.all_claims.length > 0) {
      return true;
    }
    
    // Check if verified_claims has structured objects
    if (fakeNewsResult.verified_claims && 
        fakeNewsResult.verified_claims.length > 0 && 
        typeof fakeNewsResult.verified_claims[0] !== 'string') {
      return true;
    }
    
    return false;
  };

  // Render all claims with their analysis
  const renderAllClaims = (fakeNewsResult?: AnalysisResults['fake_news_result']) => {
    if (!fakeNewsResult) return null;
    
    // First, prepare the claims array
    let allClaims: Array<{claim: string; analysis?: string; reason?: string; is_verified?: boolean; found?: boolean}> = [];
    
    if (fakeNewsResult.all_claims) {
      // Use all_claims if available
      allClaims = fakeNewsResult.all_claims;
    } else if (fakeNewsResult.verified_claims || fakeNewsResult.unverified_claims) {
      // Try to combine verified and unverified claims if they have detailed structure
      if (fakeNewsResult.verified_claims && 
          fakeNewsResult.verified_claims.length > 0 && 
          typeof fakeNewsResult.verified_claims[0] !== 'string') {
        allClaims = allClaims.concat(fakeNewsResult.verified_claims as any[]);
      }
      
      if (fakeNewsResult.unverified_claims && 
          fakeNewsResult.unverified_claims.length > 0 && 
          typeof fakeNewsResult.unverified_claims[0] !== 'string') {
        allClaims = allClaims.concat(fakeNewsResult.unverified_claims as any[]);
      }
    }
    
    if (allClaims.length === 0) return null;
    
    return (
      <div className="all-claims">
        <h4>Analyzed Claims:</h4>
        <div className="claims-list">
          {allClaims.map((claim, i) => {
            // Determine if the claim is verified - check both is_verified and found properties
            const isVerified = claim.is_verified !== undefined 
              ? claim.is_verified 
              : claim.found === true;
            
            // Get analysis text - check both analysis and reason properties
            const analysisText = claim.analysis || claim.reason || 
              (isVerified 
                ? 'This claim is supported by the article content.' 
                : 'This claim is not supported by the article content.');
            
            return (
              <div key={i} className={`claim-item ${isVerified ? 'verified' : 'unverified'}`}>
                <div className="claim-header">
                  <span className="claim-text">{claim.claim}</span>
                  <span className={`claim-status ${isVerified ? 'verified' : 'unverified'}`}>
                    {isVerified ? 'Verified' : 'Unverified'}
                  </span>
                </div>
                <div className="claim-analysis">
                  {analysisText}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    );
  };

  // Open the detailed report page
  const openDetailedReport = () => {
    if (!currentUrl) {
      setError('Cannot open detailed report: URL not available');
      return;
    }
    
    // If we have results, use the article_url if available as it might be the canonical URL
    // that was actually used for the analysis instead of the browser URL
    const urlToUse = results?.article_url || currentUrl;
    
    console.log('Opening detailed report for URL:', urlToUse);
    
    // Open the report page in a new tab
    chrome.tabs.create({
      url: chrome.runtime.getURL(`report.html?url=${encodeURIComponent(urlToUse)}`)
    });
  };

  // Save num claims setting
  const saveNumClaims = (value: number) => {
    setNumClaims(value);
    chrome.storage.local.set({ numClaims: value });
  };

  // Settings UI Component
  const SettingsPanel = () => {
    return (
      <div className="settings-panel">
        <h3>Settings</h3>
        <div className="setting-item">
          <label htmlFor="numClaims">Number of Claims to Check:</label>
          <select 
            id="numClaims" 
            value={numClaims} 
            onChange={(e) => saveNumClaims(Number(e.target.value))}
          >
            {[1, 2, 3, 4, 5].map(num => (
              <option key={num} value={num}>{num}</option>
            ))}
          </select>
        </div>
        <div className="settings-actions">
          <button onClick={() => setShowSettings(false)}>Close</button>
        </div>
      </div>
    );
  };

  if (loading) {
    return (
      <div className="loading-container">
        <div className="loading-spinner"></div>
        <div className="loading-text">Loading analysis results...</div>
      </div>
    );
  }

  // Show start analysis button if we haven't analyzed yet and don't have results
  if (!results && !processing && initialized) {
    return (
      <div className="start-analysis-container">
        <h2>News Analyzer</h2>
        
        <div className="article-preview">
          <h3>Current Article</h3>
          <p className="url">{currentUrl}</p>
        </div>
        
        <div className="analyze-options">
          <label htmlFor="numClaimsSelect">Number of claims to check:</label>
          <select 
            id="numClaimsSelect" 
            value={numClaims}
            onChange={(e) => saveNumClaims(Number(e.target.value))}
          >
            {[1, 2, 3, 4, 5].map(num => (
              <option key={num} value={num}>{num}</option>
            ))}
          </select>
        </div>
        
        <button 
          className="start-analysis-button"
          onClick={triggerProcessing}
          disabled={processing}
        >
          Start Analysis
        </button>
        
        {error && <p className="start-error">{error}</p>}
      </div>
    );
  }

  if (error) {
    return (
      <div className="error">
        <h3>Not Available</h3>
        <p>{error}</p>
        {processing ? (
          <p>Processing in progress... Please wait.</p>
        ) : (
          <>
            <p>This may happen if:</p>
            <ul>
              <li>The current page is not a news article</li>
              <li>Analysis is still in progress</li>
              <li>The backend service is not running</li>
            </ul>
            <div className="action-buttons">
              <button 
                className="retry-button"
                onClick={triggerProcessing}
                disabled={processing}
              >
                Process Article Now
              </button>
              <button 
                className="test-button"
                onClick={testAPIDirectly}
                disabled={processing}
              >
                Test API Connection
              </button>
            </div>
          </>
        )}
      </div>
    );
  }

  return (
    <div className="popup-container">
      <div className="popup-header">
        <h1>News Analyzer</h1>
        <div className="header-actions">
          <button 
            className="refresh-button" 
            onClick={fetchResults} 
            title="Refresh Results"
            disabled={processing}
          >
            🔄
          </button>
          <button 
            className="reanalyze-button"
            onClick={triggerProcessing}
            disabled={processing}
            title="Run analysis again"
          >
            Reanalyze
          </button>
          <button 
            className="settings-button" 
            onClick={() => setShowSettings(!showSettings)} 
            title="Settings"
          >
            ⚙️
          </button>
        </div>
      </div>

      {showSettings ? (
        <SettingsPanel />
      ) : (
        <>
          {processing && (
            <div className="processing-indicator">
              <div className="spinner"></div>
              <div>Processing article, please wait...</div>
            </div>
          )}
          
          <header>
            <div className="header-main">
              <h1>News Analyzer</h1>
              <a 
                href="test-api.html" 
                target="_blank" 
                className="dev-tools-link" 
                title="Open API Testing Tools"
              >
                API Test Tools
              </a>
            </div>
            <div className="article-info">
              <h2>{results?.article_title || 'Untitled Article'}</h2>
              {results?.article_source && (
                <span className="source-badge">{results.article_source}</span>
              )}
            </div>
          </header>

          <div className="tabs">
            <button 
              className={activeTab === 'summary' ? 'active' : ''} 
              onClick={() => setActiveTab('summary')}
            >
              Summary
            </button>
            <button 
              className={activeTab === 'credibility' ? 'active' : ''} 
              onClick={() => setActiveTab('credibility')}
            >
              Credibility
            </button>
            <button 
              className={activeTab === 'fakeness' ? 'active' : ''} 
              onClick={() => setActiveTab('fakeness')}
            >
              Fact Check
            </button>
            <button 
              className={activeTab === 'sentiment' ? 'active' : ''} 
              onClick={() => setActiveTab('sentiment')}
            >
              Sentiment
            </button>
          </div>

          {/* Detailed Report Button */}
          {results && !loading && !error && (
            <div className="detailed-report-button-container">
              <button 
                className="detailed-report-button"
                onClick={openDetailedReport}
              >
                View Detailed Report
              </button>
            </div>
          )}

          <div className="tab-content">
            {activeTab === 'summary' && (
              <div className="summary-tab">
                <p>{results?.summary_result || 'No summary available.'}</p>
              </div>
            )}

            {activeTab === 'credibility' && (
              <div className="credibility-tab">
                <div className="score-row">
                  <span>Overall Credibility:</span>
                  {renderScoreLabel(results?.credibility_result?.overall_credibility)}
                </div>
                <div className="score-row">
                  <span>Source Reputation:</span>
                  {renderScoreLabel(results?.credibility_result?.source_reputation)}
                </div>
                <div className="score-row">
                  <span>Title-Content Alignment:</span>
                  {renderScoreLabel(results?.credibility_result?.title_content_alignment)}
                </div>
                <p className="evaluation">
                  {results?.credibility_result?.evaluation || 'No evaluation available.'}
                </p>
              </div>
            )}

            {activeTab === 'fakeness' && (
              <div className="fakeness-tab">
                <div className="score-row">
                  <span>Verification Score:</span>
                  {renderScoreLabel(results?.fake_news_result?.verification_score)}
                </div>
                <div className="claims-summary">
                  <p>
                    <strong>Claims Analyzed:</strong> {results?.fake_news_result?.claims_analyzed || 0}
                  </p>
                  <p>
                    <strong>Claims Verified:</strong> {results?.fake_news_result?.claims_verified || 0}
                  </p>
                </div>
                
                {/* Display all claims with their analysis */}
                {renderAllClaims(results?.fake_news_result)}
                
                {/* Legacy fallback for unverified claims without detailed analysis */}
                {!hasDetailedClaimAnalysis(results?.fake_news_result) && 
                 results?.fake_news_result?.unverified_claims && 
                 (results.fake_news_result.unverified_claims as string[]).length > 0 && (
                  <div className="unverified-claims">
                    <h4>Unverified Claims:</h4>
                    <ul>
                      {(results.fake_news_result.unverified_claims as string[]).map((claim, i) => (
                        <li key={i}>{claim}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}

            {activeTab === 'sentiment' && (
              <div className="sentiment-tab">
                <div className="score-row">
                  <span>Emotional Tone:</span>
                  <span className="tone-badge">
                    {results?.sentiment_result?.emotional_tone || 'Neutral'}
                  </span>
                </div>
                <div className="score-row">
                  <span>Bias Assessment:</span>
                  <span className="bias-badge">
                    {results?.sentiment_result?.bias_assessment || 'No bias detected'}
                  </span>
                </div>
                <div className="score-row">
                  <span>Subjectivity:</span>
                  {renderScoreLabel(results?.sentiment_result?.subjectivity)}
                </div>
                <p className="justification">
                  {results?.sentiment_result?.justification || 'No justification available.'}
                </p>
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
};

// Render the popup
const root = ReactDOM.createRoot(document.getElementById('root') as HTMLElement);
root.render(
  <React.StrictMode>
    <Popup />
  </React.StrictMode>
); 