// JavaScript functionality for the report is embedded in the HTML file 

document.addEventListener('DOMContentLoaded', function() {
    // Show loading, hide content
    document.getElementById('loading-section').style.display = 'flex';
    document.getElementById('content-section').style.display = 'none';
    
    // Get the URL parameter from the current URL
    const urlParams = new URLSearchParams(window.location.search);
    const articleUrl = urlParams.get('url');
    
    if (!articleUrl) {
        hideLoading();
        displayError("No article URL provided. Please provide a URL to analyze.");
        return;
    }
    
    // Set the article URL link
    document.getElementById('article-url').href = articleUrl;
    
    // Fetch the article data from the backend
    fetchArticleData(articleUrl);

    // Add event listener for the close button
    document.getElementById('close-button').addEventListener('click', function(e) {
        e.preventDefault();
        window.close();
    });
});

function hideLoading() {
    document.getElementById('loading-section').style.display = 'none';
    document.getElementById('content-section').style.display = 'block';
}

async function fetchArticleData(articleUrl) {
    try {
        // Call the backend API to get article data
        const response = await fetch(`http://localhost:8000/get_article?url=${encodeURIComponent(articleUrl)}`)
            .catch(error => {
                // This will catch network errors like server not available
                throw new Error("Cannot connect to the analysis server. Please ensure the backend is running.");
            });
        
        if (!response.ok) {
            if (response.status === 404) {
                throw new Error("This article has not been analyzed yet. Please use the extension to analyze it first.");
            } else {
                throw new Error(`API error: ${response.status} - ${response.statusText || "Unknown error"}`);
            }
        }
        
        const data = await response.json();
        
        if (!data || !data.article) {
            throw new Error('No article data found for this URL. The article may not have been analyzed yet.');
        }
        
        // Hide loading indicator
        hideLoading();
        
        // Populate the report with the article data
        populateReport(data.article);
    } catch (error) {
        hideLoading();
        displayError(`${error.message}`);
    }
}

function populateReport(article) {
    // Article basics
    document.getElementById('article-title').textContent = article.title || 'Untitled Article';
    document.getElementById('source-badge').textContent = article.source || 'Unknown Source';
    
    // Format the date
    const processedDate = new Date(article.processed_at);
    document.getElementById('processed-date').textContent = `Processed: ${processedDate.toLocaleDateString('en-US', { 
        year: 'numeric', 
        month: 'long', 
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    })}`;
    
    // Get the analysis results
    const results = article.analysis_results;
    
    // Summary
    if (results.summary_result) {
        document.getElementById('summary').textContent = results.summary_result;
    }
    
    // Credibility data
    if (results.credibility_result) {
        const credibility = results.credibility_result;
        
        // Set percentages
        if (credibility.source_reputation !== undefined) {
            document.getElementById('source-reputation').textContent = `${Math.round(credibility.source_reputation * 100)}%`;
            document.getElementById('source-reputation-reasoning').textContent = credibility.sourceReputationReasoning || credibility.evaluation || '';
        }
        
        if (credibility.title_content_alignment !== undefined) {
            document.getElementById('title-content').textContent = `${Math.round(credibility.title_content_alignment * 100)}%`;
            document.getElementById('title-content-reasoning').textContent = credibility.titleContentReasoning || '';
        }
        
        if (credibility.overall_credibility !== undefined) {
            document.getElementById('overall-credibility').textContent = `${Math.round(credibility.overall_credibility * 100)}%`;
            document.getElementById('overall-conclusion').textContent = credibility.evaluation || credibility.overallConclusion || '';
        }
    }
    
    // Fake news / fact check
    if (results.fake_news_result) {
        const fakeNews = results.fake_news_result;
        
        // Update claim stats
        document.getElementById('claims-stats').textContent = 
            `Claims analyzed: ${fakeNews.claims_analyzed || 0}, Claims verified: ${fakeNews.claims_verified || 0}, Verification score: ${Math.round((fakeNews.verification_score || 0) * 100)}%`;
        
        // Render verified claims
        const verifiedClaimsContainer = document.getElementById('verified-claims');
        verifiedClaimsContainer.innerHTML = ''; // Clear existing content
        
        if (fakeNews.verified_claims && fakeNews.verified_claims.length > 0) {
            fakeNews.verified_claims.forEach(claim => {
                const claimDiv = document.createElement('div');
                claimDiv.className = 'claim verified';
                
                claimDiv.innerHTML = `
                    <h4>
                        ${claim.claim}
                        <span class="status-badge verified-badge">Verified</span>
                    </h4>
                    <p>${claim.analysis || ''}</p>
                `;
                
                verifiedClaimsContainer.appendChild(claimDiv);
            });
        } else {
            verifiedClaimsContainer.innerHTML = '<p>No verified claims found.</p>';
        }
        
        // Render unverified claims
        const unverifiedClaimsContainer = document.getElementById('unverified-claims');
        unverifiedClaimsContainer.innerHTML = ''; // Clear existing content
        
        if (fakeNews.unverified_claims && fakeNews.unverified_claims.length > 0) {
            fakeNews.unverified_claims.forEach(claim => {
                const claimDiv = document.createElement('div');
                claimDiv.className = 'claim unverified';
                
                claimDiv.innerHTML = `
                    <h4>
                        ${claim.claim}
                        <span class="status-badge unverified-badge">Unverified</span>
                    </h4>
                    <p>${claim.analysis || ''}</p>
                `;
                
                unverifiedClaimsContainer.appendChild(claimDiv);
            });
        } else {
            unverifiedClaimsContainer.innerHTML = '<p>No unverified claims found.</p>';
        }
    }
    
    // Sentiment analysis
    if (results.sentiment_result) {
        const sentiment = results.sentiment_result;
        
        // Emotional tone and subjectivity
        document.getElementById('emotional-tone').textContent = sentiment.emotional_tone || 'Neutral';
        
        if (sentiment.subjectivity !== undefined) {
            document.getElementById('subjectivity').textContent = `${Math.round(sentiment.subjectivity * 100)}%`;
        }
        
        // Polarity marker position (convert from -1...1 to 0...100)
        if (sentiment.polarity !== undefined) {
            const polarityPercent = (sentiment.polarity + 1) * 50;
            document.querySelector('.sentiment-marker').style.left = `${polarityPercent}%`;
        }
        
        // Bias assessment
        if (sentiment.bias_assessment) {
            document.getElementById('bias-assessment').textContent = sentiment.bias_assessment;
        }
        
        // Key phrases
        const keyPhrasesContainer = document.getElementById('key-phrases');
        keyPhrasesContainer.innerHTML = ''; // Clear existing content
        
        if (sentiment.key_phrases && sentiment.key_phrases.length > 0) {
            sentiment.key_phrases.forEach(phrase => {
                const span = document.createElement('span');
                span.className = 'key-phrase';
                span.textContent = phrase;
                keyPhrasesContainer.appendChild(span);
            });
        }
        
        // Justification
        const justificationContainer = document.getElementById('sentiment-justification');
        justificationContainer.innerHTML = ''; // Clear existing content
        
        if (sentiment.detailed_justification && sentiment.detailed_justification.length > 0) {
            sentiment.detailed_justification.forEach(point => {
                const li = document.createElement('li');
                li.textContent = point;
                justificationContainer.appendChild(li);
            });
        } else if (sentiment.justification) {
            // Handle string or split by periods
            const points = typeof sentiment.justification === 'string' 
                ? sentiment.justification.split('. ').filter(p => p.trim())
                : Array.isArray(sentiment.justification) ? sentiment.justification : [];
            
            points.forEach(point => {
                const li = document.createElement('li');
                li.textContent = point.trim();
                justificationContainer.appendChild(li);
            });
        }
    }
    
    // Article content
    if (results.article_content) {
        document.getElementById('article-content').textContent = results.article_content;
    }
}

function displayError(message) {
    // Hide loading indicator
    document.getElementById('loading-section').style.display = 'none';
    
    // Display error message in the page
    const container = document.querySelector('.container');
    container.innerHTML = `
        <h1>Article Analysis Report</h1>
        <div class="error">
            <h2>Error</h2>
            <p>${message}</p>
            <p>This may happen if:</p>
            <ul>
                <li>The article hasn't been analyzed yet</li>
                <li>The backend server is not running</li>
                <li>There was a problem connecting to the database</li>
            </ul>
            <p>
                <a href="#" id="go-back" class="back-btn">Go Back</a>
                <a href="#" id="close-window" class="back-btn">Close Report</a>
            </p>
        </div>
    `;
    
    // Add event listeners for the buttons in the error message
    document.getElementById('go-back').addEventListener('click', function(e) {
        e.preventDefault();
        window.history.back();
    });
    
    document.getElementById('close-window').addEventListener('click', function(e) {
        e.preventDefault();
        window.close();
    });
} 