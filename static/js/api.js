/* ==============================================
   API - ZenStatus
   ==============================================
   Server communication and data fetching
*/

var lastSeoResults = [];

async function streamEndpoint(path, payload, onProgress, onComplete, controller) {
    var response = await fetch(path, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload),
        signal: controller ? controller.signal : undefined
    });

    if (!response.ok) {
        throw new Error('Server responded with status ' + response.status);
    }

    var reader = response.body.getReader();
    var decoder = new TextDecoder();
    var buffer = '';
    var completed = false;
    var serverError = null;

    while (true) {
        var part = await reader.read();
        if (part.done) break;
        buffer += decoder.decode(part.value, { stream: true });
        var lines = buffer.split('\n\n');
        buffer = lines.pop();
        for (var i = 0; i < lines.length; i++) {
            var line = lines[i];
            if (line.indexOf('data: ') !== 0) continue;
            var data;
            try {
                data = JSON.parse(line.substring(6));
            } catch (parseErr) {
                console.warn('SSE parse error:', parseErr, 'Line:', line);
                continue;
            }
            if (data.type === 'progress' && onProgress) {
                onProgress(data);
            } else if (data.type === 'complete' && onComplete) {
                completed = true;
                onComplete(data);
            } else if (data.type === 'error') {
                serverError = new Error(data.message || 'Server error');
            }
        }
    }
    
    // Throw any server error after stream ends
    if (serverError) {
        throw serverError;
    }
    
    // Process any remaining buffer
    if (buffer.trim() && buffer.indexOf('data: ') === 0) {
        var data;
        try {
            data = JSON.parse(buffer.substring(6));
        } catch (parseErr) {
            console.warn('Final buffer parse error:', parseErr);
            return;
        }
        if (data.type === 'complete' && onComplete && !completed) {
            completed = true;
            onComplete(data);
        } else if (data.type === 'error') {
            throw new Error(data.message || 'Server error');
        }
    }
}

async function checkWebsites() {
    var urls = readUrls();
    if (urls.length === 0) {
        showToast('Please enter at least one URL.', 'error');
        return;
    }

    showLoading('0/' + urls.length);
    setButtonsDisabled(true);
    var controller = startOperation('status check');

    try {
        await streamEndpoint('/check', { urls: urls }, function(data) {
            document.getElementById('progress').textContent = data.completed + '/' + data.total;
            updateProgressBar(data.completed, data.total);
        }, function(data) {
            displayResults(data.results);
        }, controller);
    } catch (err) {
        if (err.name === 'AbortError') {
            showToast('Status check canceled.', 'info');
        } else {
            showToast('Error checking websites: ' + err.message, 'error');
        }
    } finally {
        hideLoading();
        setButtonsDisabled(false);
        clearOperationState();
    }
}

function updateProgressBar(completed, total) {
    var percent = total > 0 ? Math.round((completed / total) * 100) : 0;
    var progressBar = document.getElementById('progressBar');
    var progressPercent = document.getElementById('progressPercent');
    if (progressBar) progressBar.style.width = percent + '%';
    if (progressPercent) progressPercent.textContent = percent + '%';
}

async function runSeoAudit() {
    var urls = readUrls();
    var useSitemap = document.getElementById('useSitemap').checked;
    var sitemapUrl = document.getElementById('sitemapUrl').value.trim();
    var maxPagesInput = document.getElementById('maxPages');
    var maxPages = (maxPagesInput && maxPagesInput.value) ? parseInt(maxPagesInput.value, 10) : 10000;

    if (!useSitemap && urls.length === 0) {
        showToast('Please enter at least one URL.', 'error');
        return;
    }

    if (useSitemap && urls.length === 0) {
        showToast('Enter at least one root URL so we can infer the sitemap.', 'error');
        return;
    }

    showLoading(useSitemap ? '0/?' : '0/' + urls.length);
    setButtonsDisabled(true);
    lastSeoResults = [];
    var controller = startOperation('SEO audit');

    try {
        await streamEndpoint('/seo-audit', {
            urls: urls,
            use_sitemap: useSitemap,
            sitemap_url: sitemapUrl,
            max_pages: maxPages
        }, function(data) {
            document.getElementById('progress').textContent = data.completed + '/' + data.total;
            updateProgressBar(data.completed, data.total);
        }, function(data) {
            console.log('SEO audit complete, results:', data.results ? data.results.length : 0);
            displaySeoResults(data.results, data.sitemap_debug);
            // Save to history
            if (typeof window.saveAuditToHistory === 'function') {
                window.saveAuditToHistory(data.results);
            } else {
                console.warn('saveAuditToHistory not available');
            }
        }, controller);
    } catch (err) {
        console.error('SEO audit error:', err);
        if (err.name === 'AbortError') {
            showToast('SEO audit canceled.', 'info');
        } else {
            showToast('Error running SEO audit: ' + err.message, 'error');
        }
    } finally {
        hideLoading();
        setButtonsDisabled(false);
        clearOperationState();
    }
}

function displayResults(results) {
    var resultsBody = document.getElementById('resultsBody');
    var summary = document.getElementById('summary');

    var total = results.length;
    var online = results.filter(function(r) { return r.status_message === 'Online'; }).length;
    var errors = total - online;
    var times = results.filter(function(r) { return r.response_time !== 'N/A'; }).map(function(r) { return parseFloat(r.response_time); });
    var avgTime = times.length ? (times.reduce(function(a, b) { return a + b; }, 0) / times.length) : 0;

    summary.innerHTML = [
        '<div class="summary-item"><div class="number">' + total + '</div><div class="label">Total Sites</div></div>',
        '<div class="summary-item"><div class="number">' + online + '</div><div class="label">Online</div></div>',
        '<div class="summary-item"><div class="number">' + errors + '</div><div class="label">Errors</div></div>',
        '<div class="summary-item"><div class="number">' + avgTime.toFixed(2) + 's</div><div class="label">Avg Response</div></div>'
    ].join('');

    resultsBody.innerHTML = '';
    results.forEach(function(result, index) {
        var row = document.createElement('tr');
        var statusClass = result.status_message === 'Online' ? 'status-online' : 'status-error';
        var codeClass = 'code-badge';
        if (typeof result.status_code === 'number') {
            if (result.status_code >= 200 && result.status_code < 300) codeClass += ' code-2xx';
            else if (result.status_code >= 300 && result.status_code < 400) codeClass += ' code-3xx';
            else if (result.status_code >= 400 && result.status_code < 500) codeClass += ' code-4xx';
            else if (result.status_code >= 500) codeClass += ' code-5xx';
        }

        var statusMessage = result.status_message;

        row.innerHTML = [
            '<td>' + (index + 1) + '</td>',
            '<td class="url-cell"><a href="' + result.url + '" target="_blank" rel="noopener noreferrer">' + result.url + '</a></td>',
            '<td><span class="' + codeClass + '">' + result.status_code + '</span></td>',
            '<td><span class="status-badge ' + statusClass + '">' + statusMessage + '</span></td>',
            '<td>' + result.response_time + '</td>'
        ].join('');

        resultsBody.appendChild(row);
    });

    document.getElementById('results').classList.add('active');
}

function displaySeoResults(results, sitemapDebug) {
    console.log('displaySeoResults called with', results ? results.length : 0, 'results');
    
    var cards = document.getElementById('seoCards');
    var summary = document.getElementById('seoSummary');
    var issuesPanel = document.getElementById('issuesPanel');
    var recommendationsPanel = document.getElementById('recommendationsPanel');
    var executiveSummaryEl = document.getElementById('executiveSummary');
    var scoreChartEl = document.getElementById('scoreChart');
    var seoResultsEl = document.getElementById('seoResults');
    
    // Debug: Check if elements exist
    console.log('DOM elements found:', {
        cards: !!cards,
        summary: !!summary,
        issuesPanel: !!issuesPanel,
        seoResults: !!seoResultsEl
    });
    
    lastSeoResults = results || [];

    // Group results by site
    var siteBuckets = {};
    lastSeoResults.forEach(function(r) {
        var parser = document.createElement('a');
        parser.href = r.url;
        var host = parser.hostname || 'unknown';
        if (!siteBuckets[host]) siteBuckets[host] = [];
        siteBuckets[host].push(r);
    });

    var siteCount = Object.keys(siteBuckets).length;
    var total = results.length;
    var okPages = results.filter(function(r) { return r.status_message === 'OK'; }).length;
    var missingTitles = results.filter(function(r) { return !r.title; }).length;
    var missingDescriptions = results.filter(function(r) { return !r.meta_description; }).length;
    var missingH1 = results.filter(function(r) { return r.h1_count === 0; }).length;
    var httpsPages = results.filter(function(r) { return r.https; }).length;
    var avgWordsList = results.filter(function(r) { return typeof r.word_count === 'number' && r.word_count > 0; }).map(function(r) { return r.word_count; });
    var avgWords = avgWordsList.length ? avgWordsList.reduce(function(a, b) { return a + b; }, 0) / avgWordsList.length : 0;
    var avgRespList = results.filter(function(r) { return r.response_time !== 'N/A'; }).map(function(r) { return parseFloat(r.response_time); });
    var avgResponse = avgRespList.length ? avgRespList.reduce(function(a, b) { return a + b; }, 0) / avgRespList.length : 0;

    // Calculate overall SEO score
    var totalScore = 0;
    results.forEach(function(r) {
        totalScore += calculateSeoScore(r);
    });
    var avgScore = results.length ? Math.round(totalScore / results.length) : 0;

    // Warning counts for top issues
    var warningCounts = {};
    results.forEach(function(r) {
        (r.warnings || []).forEach(function(w) {
            warningCounts[w] = (warningCounts[w] || 0) + 1;
        });
    });
    var topWarnings = Object.keys(warningCounts)
        .sort(function(a, b) { return warningCounts[b] - warningCounts[a]; })
        .slice(0, 8)
        .map(function(w) { return { text: w, count: warningCounts[w] }; });

    // Calculate additional metrics
    var pagesWithIssues = results.filter(function(r) { return (r.warnings || []).length > 0; }).length;
    var httpsCount = results.filter(function(r) { return r.https; }).length;
    var noCanonical = results.filter(function(r) { return !r.canonical; }).length;

    // Enhanced summary with better structure - Score | Overview | Issues
    summary.innerHTML = [
        // SEO Score (left side)
        '<div class="seo-score-container"><div class="seo-score-circle ' + getScoreClass(avgScore) + '">' + avgScore + '</div><div class="seo-score-label">SEO Score</div></div>',
        
        // Overview section
        '<div class="summary-item"><div class="number">' + siteCount + '</div><div class="label">Sites</div></div>',
        '<div class="summary-item"><div class="number">' + total + '</div><div class="label">Pages</div></div>',
        '<div class="summary-item"><div class="number">' + okPages + '</div><div class="label">OK</div></div>',
        '<div class="summary-item"><div class="number">' + avgResponse.toFixed(1) + 's</div><div class="label">Avg Speed</div></div>',
        
        // Issues section
        '<div class="summary-item"><div class="number">' + missingTitles + '</div><div class="label">No Title</div></div>',
        '<div class="summary-item"><div class="number">' + missingH1 + '</div><div class="label">No H1</div></div>',
        '<div class="summary-item"><div class="number">' + missingDescriptions + '</div><div class="label">No Meta</div></div>',
        '<div class="summary-item"><div class="number">' + (total - httpsCount) + '</div><div class="label">No HTTPS</div></div>'
    ].join('');

    // Calculate score distribution
    var scoreDistribution = { excellent: 0, good: 0, average: 0, poor: 0, critical: 0 };
    results.forEach(function(r) {
        var score = calculateSeoScore(r);
        if (score >= 90) scoreDistribution.excellent++;
        else if (score >= 70) scoreDistribution.good++;
        else if (score >= 50) scoreDistribution.average++;
        else if (score >= 30) scoreDistribution.poor++;
        else scoreDistribution.critical++;
    });

    // Executive Summary
    if (executiveSummaryEl) {
        var summaryText = generateExecutiveSummary(results, avgScore, topWarnings, scoreDistribution);
        executiveSummaryEl.innerHTML = '<h2>Executive Summary</h2>' +
            '<div class="summary-text">' + summaryText + '</div>' +
            '<div class="key-metrics">' +
            '<div class="metric"><div class="metric-value">' + avgScore + '</div><div class="metric-label">Avg SEO Score</div></div>' +
            '<div class="metric"><div class="metric-value">' + total + '</div><div class="metric-label">Pages Audited</div></div>' +
            '<div class="metric"><div class="metric-value">' + topWarnings.length + '</div><div class="metric-label">Issue Types</div></div>' +
            '<div class="metric"><div class="metric-value">' + avgResponse.toFixed(1) + 's</div><div class="metric-label">Avg Load Time</div></div>' +
            '</div>';
        executiveSummaryEl.style.display = 'block';
    }

    // Score Distribution Chart
    if (scoreChartEl) {
        var chartHtml = '<h3>Score Distribution</h3><div class="score-distribution">';
        var categories = ['excellent', 'good', 'average', 'poor', 'critical'];
        categories.forEach(function(cat) {
            var count = scoreDistribution[cat];
            var percent = total > 0 ? (count / total) * 100 : 0;
            if (count > 0) {
                chartHtml += '<div class="score-bar ' + cat + '" style="flex:' + count + '">' + count + '</div>';
            }
        });
        chartHtml += '</div><div class="score-legend">' +
            '<div class="score-legend-item"><span class="score-legend-dot" style="background:#22c55e"></span>Excellent (90+)</div>' +
            '<div class="score-legend-item"><span class="score-legend-dot" style="background:#84cc16"></span>Good (70-89)</div>' +
            '<div class="score-legend-item"><span class="score-legend-dot" style="background:#eab308"></span>Average (50-69)</div>' +
            '<div class="score-legend-item"><span class="score-legend-dot" style="background:#f97316"></span>Poor (30-49)</div>' +
            '<div class="score-legend-item"><span class="score-legend-dot" style="background:#ef4444"></span>Critical (<30)</div>' +
            '</div>';
        scoreChartEl.innerHTML = chartHtml;
        scoreChartEl.style.display = 'block';
    }

    // Filter/Sort bar
    var filterBar = document.getElementById('filterSortBar');
    if (filterBar) {
        filterBar.innerHTML = '<button class="filter-btn active" onclick="filterCards(\'all\')">All (' + total + ')</button>' +
            '<button class="filter-btn" onclick="filterCards(\'issues\')">With Issues (' + pagesWithIssues + ')</button>' +
            '<button class="filter-btn" onclick="filterCards(\'good\')">Good Score (' + (scoreDistribution.excellent + scoreDistribution.good) + ')</button>' +
            '<button class="filter-btn" onclick="filterCards(\'poor\')">Needs Work (' + (scoreDistribution.average + scoreDistribution.poor + scoreDistribution.critical) + ')</button>' +
            '<select class="sort-select" onchange="sortCards(this.value)">' +
            '<option value="default">Sort: Default</option>' +
            '<option value="score-asc">Score: Low to High</option>' +
            '<option value="score-desc">Score: High to Low</option>' +
            '<option value="issues">Most Issues</option>' +
            '</select>';
        filterBar.style.display = 'flex';
    }

    cards.innerHTML = '';
    
    // Render grouped by site
    var globalIndex = 0;
    Object.keys(siteBuckets).sort().forEach(function(host) {
        var siteResults = siteBuckets[host];
        var siteOk = siteResults.filter(function(r) { return r.status_message === 'OK'; }).length;
        var siteWarnings = siteResults.filter(function(r) { return (r.warnings || []).length > 0; }).length;
        
        // Calculate site-level SEO score
        var siteScore = 0;
        siteResults.forEach(function(r) {
            siteScore += calculateSeoScore(r);
        });
        siteScore = Math.round(siteScore / siteResults.length);
        
        var siteGroup = document.createElement('div');
        siteGroup.className = 'site-group';
        
        var headerHtml = '<div class="site-group-header">' +
            '<h2><span class="seo-score-circle ' + getScoreClass(siteScore) + '" style="width:36px;height:36px;font-size:0.9em;">' + siteScore + '</span> ' + host + '</h2>' +
            '<div class="site-group-stats">' +
            '<div class="site-group-stat"><span>' + siteResults.length + '</span> pages</div>' +
            '<div class="site-group-stat"><span>' + siteOk + '</span> OK</div>' +
            '<div class="site-group-stat"><span>' + siteWarnings + '</span> warnings</div>' +
            '</div></div>';
        
        var cardsContainer = document.createElement('div');
        cardsContainer.className = 'seo-cards';
        
        siteResults.forEach(function(result) {
            globalIndex++;
            var hasWarnings = (result.warnings || []).length > 0;
            var isNetworkError = (typeof result.status_code === 'number' && result.status_code >= 400) || result.status_message !== 'OK';
            var isDuplicate = result.duplicate_of && result.duplicate_of.trim() !== '';

            // Calculate page SEO score
            var pageScore = calculateSeoScore(result);
            var scoreClass = getScoreClass(pageScore);
            
            // Determine SEO status based on score
            var seoStatus, seoStatusClass;
            if (isNetworkError) {
                seoStatus = 'Error';
                seoStatusClass = 'status-danger';
            } else if (pageScore >= 90) {
                seoStatus = 'Excellent';
                seoStatusClass = 'status-ok';
            } else if (pageScore >= 70) {
                seoStatus = 'Good';
                seoStatusClass = 'status-ok';
            } else if (pageScore >= 50) {
                seoStatus = 'Needs Work';
                seoStatusClass = 'status-warn';
            } else {
                seoStatus = 'Poor';
                seoStatusClass = 'status-danger';
            }

            var codeClass = 'pill';
            if (typeof result.status_code === 'number') {
                if (result.status_code >= 200 && result.status_code < 300) codeClass += ' status-ok';
                else if (result.status_code >= 300 && result.status_code < 400) codeClass += '';
                else if (result.status_code >= 400) codeClass += ' status-danger';
            }

            var warningsText = (result.warnings || []).join('; ');
            var warningsClass = isNetworkError ? 'warnings danger' : (hasWarnings ? 'warnings warn' : 'warnings ok');
            var titleText = result.title || 'No title';
            var metaText = result.meta_description || 'No description';
            var h1Sample = (result.h1_samples || []).slice(0, 2).join(' | ') || 'No H1';
            
            var duplicateBadge = '';
            if (isDuplicate) {
                duplicateBadge = '<div class="pill status-warn" title="Duplicate of: ' + result.duplicate_of + '" style="cursor: help;">⚠ Duplicate</div>';
            }

            // Build heading hierarchy
            var headingHtml = '<div class="heading-hierarchy">';
            headingHtml += '<div class="heading-tag"><span class="tag-name">H1</span><span class="tag-count">' + result.h1_count + '</span></div>';
            if (result.h2_count !== undefined) {
                headingHtml += '<div class="heading-tag"><span class="tag-name">H2</span><span class="tag-count">' + result.h2_count + '</span></div>';
            }
            if (result.h3_count !== undefined) {
                headingHtml += '<div class="heading-tag"><span class="tag-name">H3</span><span class="tag-count">' + result.h3_count + '</span></div>';
            }
            if (result.h4_count !== undefined) {
                headingHtml += '<div class="heading-tag"><span class="tag-name">H4</span><span class="tag-count">' + result.h4_count + '</span></div>';
            }
            headingHtml += '</div>';

            var card = document.createElement('div');
            card.className = 'seo-card';
            // Add data attributes for filtering/sorting
            var resultWarnings = result.warnings || [];
            card.dataset.score = pageScore;
            card.dataset.hasIssues = (resultWarnings.length > 0).toString();
            card.dataset.issueCount = resultWarnings.length;
            card.innerHTML = [
                '<div class="card-header">',
                '  <div class="card-header-left">',
                '    <div class="pill pill-number">#' + globalIndex + '</div>',
                '    <div class="seo-score-circle ' + scoreClass + '" style="width:32px;height:32px;font-size:0.8em;">' + pageScore + '</div>',
                '    <div class="' + codeClass + '" title="HTTP Status">' + result.status_code + '</div>',
                '    <div class="pill">' + result.response_time + '</div>',
                (isDuplicate ? '    ' + duplicateBadge : ''),
                '  </div>',
                '  <div class="card-header-right">',
                (result.https ? '    <div class="pill status-ok">🔒 HTTPS</div>' : '    <div class="pill status-warn">⚠ HTTP</div>'),
                '    <div class="pill ' + seoStatusClass + '" title="SEO Status">' + seoStatus + '</div>',
                '  </div>',
                '</div>',
                '<div class="card-body">',
                '  <div class="url"><a href="' + result.url + '" target="_blank" rel="noopener noreferrer">' + result.url + '</a></div>',
                '  <div class="metrics-grid">',
                '    <div class="metric-item"><div class="metric-value">' + (result.title_length || 0) + '</div><div class="metric-label">Title Chars</div></div>',
                '    <div class="metric-item"><div class="metric-value">' + (result.meta_description_length || 0) + '</div><div class="metric-label">Meta Chars</div></div>',
                '    <div class="metric-item"><div class="metric-value">' + result.h1_count + '</div><div class="metric-label">H1 Tags</div></div>',
                '    <div class="metric-item"><div class="metric-value">' + result.word_count + '</div><div class="metric-label">Words</div></div>',
                '    <div class="metric-item"><div class="metric-value">' + result.internal_links + '/' + result.external_links + '</div><div class="metric-label">Int/Ext Links</div></div>',
                '    <div class="metric-item"><div class="metric-value">' + result.images_missing_alt + '/' + result.total_images + '</div><div class="metric-label">Img No Alt</div></div>',
                '  </div>',
                '  ' + headingHtml,
                '  <div class="content-section">',
                '    <div class="content-section-header">Page Title</div>',
                '    <div class="content-section-body">' + titleText + '</div>',
                '  </div>',
                '  <div class="content-section">',
                '    <div class="content-section-header">Meta Description</div>',
                '    <div class="content-section-body">' + metaText + '</div>',
                '  </div>',
                '  <div class="tags-row">',
                '    <div class="pill">H1: ' + h1Sample + '</div>',
                '    <div class="pill">Robots: ' + (result.robots || 'none') + '</div>',
                (result.canonical ? '    <div class="pill status-ok">Canonical</div>' : '    <div class="pill status-warn">No Canonical</div>'),
                (result.has_viewport ? '    <div class="pill status-ok">Viewport</div>' : '    <div class="pill status-warn">No Viewport</div>'),
                (result.has_lang ? '    <div class="pill status-ok">Lang: ' + result.lang + '</div>' : '    <div class="pill status-warn">No Lang</div>'),
                '  </div>',
                '  <div class="tags-row">',
                (result.has_og_tags ? '    <div class="pill status-ok">Open Graph</div>' : '    <div class="pill status-info">No OG Tags</div>'),
                (result.has_schema ? '    <div class="pill status-ok">Schema: ' + (result.schema_types || []).slice(0, 2).join(', ') + '</div>' : '    <div class="pill status-info">No Schema</div>'),
                (result.has_twitter_cards ? '    <div class="pill status-ok">Twitter Card</div>' : ''),
                '  </div>',
                '  <div class="' + warningsClass + '">' + (warningsText || 'No issues detected') + '</div>',
                '</div>'
            ].join('');

            cardsContainer.appendChild(card);
        });
        
        siteGroup.innerHTML = headerHtml;
        siteGroup.appendChild(cardsContainer);
        cards.appendChild(siteGroup);
    });

    // Issues panel with severity
    if (issuesPanel) {
        if (topWarnings.length === 0) {
            issuesPanel.innerHTML = '<h3>✓ Top Issues</h3><p>No major issues detected. Great job!</p>';
            issuesPanel.className = 'issues-panel';
            issuesPanel.style.background = 'var(--status-ok-bg)';
            issuesPanel.style.borderColor = 'var(--status-ok-border)';
            issuesPanel.style.color = 'var(--status-ok-text)';
        } else {
            var issuesHtml = '<h3>⚠ Top Issues to Improve (' + Object.keys(warningCounts).length + ' total)</h3><ul>';
            topWarnings.forEach(function(t) {
                var sevClass = getSeverityClass(t.text);
                issuesHtml += '<li><span class="recommendation-severity ' + sevClass + '" style="display:inline;padding:2px 8px;font-size:0.7em;margin-right:8px;">' + 
                    (sevClass === 'severity-high' ? 'HIGH' : (sevClass === 'severity-medium' ? 'MED' : 'LOW')) + 
                    '</span>' + t.text + ' <strong>(' + t.count + ' pages)</strong></li>';
            });
            issuesHtml += '</ul>';
            issuesPanel.innerHTML = issuesHtml;
            issuesPanel.style.background = '';
            issuesPanel.style.borderColor = '';
            issuesPanel.style.color = '';
        }
    }

    // Recommendations panel
    if (recommendationsPanel) {
        var recsHtml = '<h3>Prioritized Recommendations</h3>';
        
        // Generate recommendations based on issues
        var recommendations = [];
        
        if (missingTitles > 0) {
            recommendations.push({
                severity: 'high',
                title: 'Add Missing Page Titles',
                description: missingTitles + ' pages are missing title tags. Titles are critical for SEO rankings and click-through rates.',
                impact: 'High impact on rankings'
            });
        }
        
        if (missingH1 > 0) {
            recommendations.push({
                severity: 'high',
                title: 'Add Missing H1 Tags',
                description: missingH1 + ' pages are missing H1 tags. Each page should have exactly one H1 describing the main topic.',
                impact: 'High impact on content structure'
            });
        }
        
        if (missingDescriptions > 0) {
            recommendations.push({
                severity: 'medium',
                title: 'Add Meta Descriptions',
                description: missingDescriptions + ' pages are missing meta descriptions. These improve click-through rates in search results.',
                impact: 'Medium impact on CTR'
            });
        }
        
        if (warningCounts['No canonical tag']) {
            recommendations.push({
                severity: 'medium',
                title: 'Add Canonical Tags',
                description: warningCounts['No canonical tag'] + ' pages lack canonical tags. This helps prevent duplicate content issues.',
                impact: 'Medium impact on indexing'
            });
        }
        
        // New: Broken links recommendation
        var brokenLinkCount = results.filter(function(r) { return r.broken_links > 0; }).length;
        if (brokenLinkCount > 0) {
            recommendations.push({
                severity: 'high',
                title: 'Fix Broken Internal Links',
                description: brokenLinkCount + ' pages have broken internal links. These hurt user experience and crawlability.',
                impact: 'High impact on UX and SEO'
            });
        }
        
        // New: Robots.txt recommendation
        var noRobots = results.filter(function(r) { return !r.has_robots_txt; }).length;
        if (noRobots > 0) {
            recommendations.push({
                severity: 'medium',
                title: 'Add robots.txt File',
                description: 'Your site is missing a robots.txt file. This helps control search engine crawling.',
                impact: 'Medium impact on crawlability'
            });
        }
        
        // New: Sitemap recommendation
        var noSitemap = results.filter(function(r) { return !r.has_sitemap; }).length;
        if (noSitemap > 0) {
            recommendations.push({
                severity: 'medium',
                title: 'Add XML Sitemap',
                description: 'Your site is missing an XML sitemap. This helps search engines discover all your pages.',
                impact: 'Medium impact on indexing'
            });
        }
        
        // New: Image optimization
        var imgNoDimensions = results.filter(function(r) { return r.images_no_dimensions > 0; }).length;
        if (imgNoDimensions > 0) {
            recommendations.push({
                severity: 'low',
                title: 'Add Image Dimensions',
                description: imgNoDimensions + ' pages have images without width/height attributes. This causes layout shifts (CLS).',
                impact: 'Medium impact on Core Web Vitals'
            });
        }
        
        // New: Large page size
        var largePagesCount = results.filter(function(r) { return r.page_size_kb > 500; }).length;
        if (largePagesCount > 0) {
            recommendations.push({
                severity: 'medium',
                title: 'Reduce Page Size',
                description: largePagesCount + ' pages are larger than 500KB. Consider optimizing images and code.',
                impact: 'Medium impact on load time'
            });
        }
        
        if (warningCounts['Images missing alt text']) {
            recommendations.push({
                severity: 'low',
                title: 'Add Image Alt Text',
                description: 'Some images are missing alt text. This affects accessibility and image search rankings.',
                impact: 'Low-medium impact'
            });
        }
        
        if (warningCounts['Thin content']) {
            recommendations.push({
                severity: 'medium',
                title: 'Expand Thin Content',
                description: warningCounts['Thin content'] + ' pages have less than 300 words. Consider adding more valuable content.',
                impact: 'Medium impact on rankings'
            });
        }
        
        if (avgResponse > 2) {
            recommendations.push({
                severity: 'high',
                title: 'Improve Page Speed',
                description: 'Average response time is ' + avgResponse.toFixed(2) + 's. Aim for under 2 seconds for better user experience.',
                impact: 'High impact on UX and rankings'
            });
        }
        
        // Sort by severity
        var severityOrder = { high: 1, medium: 2, low: 3 };
        recommendations.sort(function(a, b) { return severityOrder[a.severity] - severityOrder[b.severity]; });
        
        if (recommendations.length === 0) {
            recsHtml += '<p style="color: var(--status-ok-text);">✓ No critical recommendations. Your site is in good shape!</p>';
        } else {
            recommendations.forEach(function(rec) {
                recsHtml += '<div class="recommendation-item">' +
                    '<div class="recommendation-severity severity-' + rec.severity + '">' + rec.severity.toUpperCase() + '</div>' +
                    '<div class="recommendation-content">' +
                    '<h4>' + rec.title + '</h4>' +
                    '<p>' + rec.description + '</p>' +
                    '<span class="recommendation-impact">' + rec.impact + '</span>' +
                    '</div></div>';
            });
        }
        
        recommendationsPanel.innerHTML = recsHtml;
    }

    var seoResultsEl = document.getElementById('seoResults');
    if (seoResultsEl) {
        seoResultsEl.classList.add('active');
        console.log('displaySeoResults complete. seoResults has active class:', seoResultsEl.classList.contains('active'));
    } else {
        console.error('seoResults element not found!');
    }
}

// ============================================
// EXPOSE FUNCTIONS GLOBALLY FOR ONCLICK HANDLERS
// ============================================

window.checkWebsites = checkWebsites;
window.runSeoAudit = runSeoAudit;
window.displaySeoResults = displaySeoResults;
