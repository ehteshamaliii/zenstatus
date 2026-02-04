/* ==============================================
   UI UTILITIES - ZenStatus
   ==============================================
   Toast notifications, modals, and UI helpers
*/

var currentController = null;
var currentOperation = '';

function showToast(message, type) {
    var container = document.getElementById('toastContainer');
    if (!container) return;
    var toast = document.createElement('div');
    var cls = 'toast';
    if (type === 'success') cls += ' toast-success';
    else if (type === 'error') cls += ' toast-error';
    else cls += ' toast-info';
    toast.className = cls;
    toast.textContent = message;
    container.appendChild(toast);
    setTimeout(function() {
        if (toast && toast.parentNode === container) {
            container.removeChild(toast);
        }
    }, 3500);
}

function setCancelEnabled(state) {
    var cancelButton = document.getElementById('cancelButton');
    if (cancelButton) cancelButton.disabled = !state;
}

function startOperation(name) {
    if (currentController) {
        currentController.abort();
    }
    currentController = new AbortController();
    currentOperation = name || 'operation';
    setCancelEnabled(true);
    return currentController;
}

function clearOperationState() {
    currentController = null;
    currentOperation = '';
    setCancelEnabled(false);
}

function cancelCurrentOperation() {
    if (!currentController) {
        showToast('No operation to cancel.', 'info');
        return;
    }
    currentController.abort();
    // Toast is shown in the catch block of the operation
}

function confirmModal(message) {
    return new Promise(function(resolve) {
        var overlay = document.getElementById('confirmOverlay');
        var msg = document.getElementById('confirmMessage');
        if (!overlay || !msg) return resolve(true);
        overlay.classList.remove('hidden');
        msg.textContent = message;
        var yesBtn = document.getElementById('confirmYes');
        var noBtn = document.getElementById('confirmNo');
        var handled = false;
        var cleanup = function(result) {
            if (handled) return;
            handled = true;
            overlay.classList.add('hidden');
            resolve(result);
        };
        if (yesBtn) yesBtn.onclick = function() { cleanup(true); };
        if (noBtn) noBtn.onclick = function() { cleanup(false); };
    });
}

function handleClearClick() {
    confirmModal('Clear all input and results?').then(function(confirmed) {
        if (confirmed) clearAll();
    });
}

function setButtonsDisabled(state) {
    var checkButton = document.getElementById('checkButton');
    var auditButton = document.getElementById('auditButton');
    if (checkButton) checkButton.disabled = state;
    if (auditButton) auditButton.disabled = state;
}

function readUrls() {
    var textarea = document.getElementById('urls');
    // Normalize newlines to handle Windows and stray CR characters
    var normalized = textarea.value.replace(/\r/g, '');
    var parts = normalized.split('\n');
    var cleaned = [];
    for (var i = 0; i < parts.length; i++) {
        var u = parts[i].trim();
        if (u) {
            // Add https:// if no protocol specified
            if (!u.match(/^https?:\/\//i)) {
                u = 'https://' + u;
            }
            cleaned.push(u);
        }
    }
    return cleaned;
}

function showLoading(labelText) {
    var progressElement = document.getElementById('progress');
    progressElement.textContent = labelText;
    
    // Reset progress bar to 0%
    var progressBar = document.getElementById('progressBar');
    var progressPercent = document.getElementById('progressPercent');
    if (progressBar) progressBar.style.width = '0%';
    if (progressPercent) progressPercent.textContent = '0%';
    
    document.getElementById('loading').classList.add('active');
    document.getElementById('results').classList.remove('active');
    document.getElementById('seoResults').classList.remove('active');
}

function hideLoading() {
    document.getElementById('loading').classList.remove('active');
}

function clearAll() {
    document.getElementById('urls').value = '';
    document.getElementById('results').classList.remove('active');
    document.getElementById('seoResults').classList.remove('active');
}

// SEO Score calculation helper
function calculateSeoScore(result) {
    var score = 100;
    var warnings = result.warnings || [];
    
    // CRITICAL ISSUES - Major SEO impact
    // Page accessibility & indexability (-20 points each)
    if (result.status_code >= 400) score -= 20;
    if (result.status_code >= 500) score -= 25;
    if (result.robots && result.robots.includes('noindex')) score -= 20;
    if (!result.https) score -= 15;
    
    // Missing essential meta tags (-12 points each)
    if (!result.title) score -= 12;
    if (!result.meta_description) score -= 12;
    if (result.h1_count === 0) score -= 12;
    
    // HIGH PRIORITY ISSUES - Significant SEO impact
    // Poor quality meta tags (-8 points each)
    if (result.title && result.title_length < 30) score -= 8;
    if (result.title && result.title_length > 60) score -= 8;
    if (result.meta_description && result.meta_description_length < 120) score -= 8;
    if (result.meta_description && result.meta_description_length > 160) score -= 8;
    
    // Content & structure issues (-7 points each)
    if (result.h1_count > 1) score -= 7;
    if (!result.canonical) score -= 7;
    if (!result.has_viewport) score -= 7;
    if (result.word_count < 300) score -= 7;
    
    // MEDIUM PRIORITY ISSUES - Moderate SEO impact
    // Technical SEO (-5 points each)
    if (!result.has_sitemap) score -= 5;
    if (!result.has_robots_txt) score -= 4;
    if (result.redirect_count > 0) score -= 4;
    if (result.url_has_underscores) score -= 3;
    
    // Image optimization (scale with severity)
    if (result.images_missing_alt > 0) {
        var altPenalty = Math.min(10, Math.floor(result.images_missing_alt / 5) + 3);
        score -= altPenalty;
    }
    if (result.images_no_dimensions > 10) {
        score -= Math.min(7, Math.floor(result.images_no_dimensions / 10) + 2);
    }
    if (result.images_not_lazy > 10) {
        score -= Math.min(6, Math.floor(result.images_not_lazy / 15) + 2);
    }
    
    // Link issues
    if (result.broken_links > 0) {
        score -= Math.min(8, result.broken_links * 2);
    }
    
    // LOW PRIORITY ISSUES - Minor SEO impact (-3 points each)
    if (!result.has_lang) score -= 3;
    if (!result.has_og_tags) score -= 3;
    if (!result.has_schema) score -= 3;
    if (!result.has_twitter_cards) score -= 2;
    
    // Performance issues
    if (result.render_blocking_count > 20) {
        score -= Math.min(8, Math.floor(result.render_blocking_count / 10));
    }
    if (result.response_time) {
        var responseTime = parseFloat(result.response_time);
        if (responseTime > 3) score -= 6;
        else if (responseTime > 2) score -= 4;
        else if (responseTime > 1) score -= 2;
    }
    if (result.page_size_kb > 2000) {
        score -= Math.min(5, Math.floor((result.page_size_kb - 2000) / 500));
    }
    
    return Math.max(0, Math.min(100, score));
}

function getScoreClass(score) {
    if (score >= 90) return 'score-excellent';
    if (score >= 70) return 'score-good';
    if (score >= 50) return 'score-average';
    if (score >= 30) return 'score-poor';
    return 'score-critical';
}

function getScoreLabel(score) {
    if (score >= 90) return 'Excellent';
    if (score >= 70) return 'Good';
    if (score >= 50) return 'Average';
    if (score >= 30) return 'Poor';
    return 'Critical';
}

function getSeverityClass(warning) {
    var highSeverity = ['Missing title', 'Missing H1', 'Missing meta description', 'Noindex set', 'Page Error', 'Missing viewport', 'Not using HTTPS', 'Broken internal links'];
    var mediumSeverity = ['Title too long', 'Description too long', 'Multiple H1 tags', 'No canonical tag', 'No Open Graph', 'No structured data', 'No schema', 'Redirect chain', 'No robots.txt', 'No sitemap'];
    
    if (highSeverity.some(function(h) { return warning.includes(h); })) return 'severity-high';
    if (mediumSeverity.some(function(m) { return warning.includes(m); })) return 'severity-medium';
    return 'severity-low';
}

// Issue Priority Scoring
function getIssuePriority(warning) {
    var criticalIssues = ['Missing title', 'Missing H1', 'Not using HTTPS', 'Page Error', 'Broken internal links'];
    var highIssues = ['Missing meta description', 'Missing viewport', 'Noindex set', 'No canonical'];
    var mediumIssues = ['No sitemap', 'No robots.txt', 'Multiple H1', 'Title too long', 'Description too long'];
    
    if (criticalIssues.some(function(i) { return warning.includes(i); })) return { level: 'critical', score: 10, impact: 'High SEO impact' };
    if (highIssues.some(function(i) { return warning.includes(i); })) return { level: 'high', score: 7, impact: 'Moderate SEO impact' };
    if (mediumIssues.some(function(i) { return warning.includes(i); })) return { level: 'medium', score: 4, impact: 'Minor SEO impact' };
    return { level: 'low', score: 2, impact: 'Low priority' };
}

// Executive Summary Generator
function generateExecutiveSummary(results, avgScore, topWarnings, scoreDistribution) {
    var total = results.length;
    var excellentCount = scoreDistribution.excellent + scoreDistribution.good;
    var poorCount = scoreDistribution.poor + scoreDistribution.critical;
    
    var summaryParts = [];
    
    // Overall health assessment
    if (avgScore >= 80) {
        summaryParts.push('Your website is in <strong>excellent health</strong> with an average SEO score of ' + avgScore + '.');
    } else if (avgScore >= 60) {
        summaryParts.push('Your website is in <strong>good condition</strong> with room for improvement. Average SEO score: ' + avgScore + '.');
    } else if (avgScore >= 40) {
        summaryParts.push('Your website <strong>needs attention</strong>. Several SEO issues were detected. Average score: ' + avgScore + '.');
    } else {
        summaryParts.push('Your website has <strong>critical SEO issues</strong> that require immediate attention. Average score: ' + avgScore + '.');
    }
    
    // Page breakdown
    summaryParts.push(' Audited <strong>' + total + ' pages</strong> across ' + Object.keys(results.reduce(function(acc, r) {
        try { acc[new URL(r.url).hostname] = true; } catch(e) {}
        return acc;
    }, {})).length + ' domain(s).');
    
    // Top priorities
    if (topWarnings.length > 0) {
        var topIssue = topWarnings[0];
        summaryParts.push(' <strong>Top priority:</strong> ' + topIssue.text + ' (affects ' + topIssue.count + ' pages).');
    }
    
    // Quick wins
    if (poorCount > 0) {
        summaryParts.push(' <strong>' + poorCount + ' pages</strong> need immediate attention.');
    }
    
    return summaryParts.join('');
}

// ============================================
// DETAILED AUDIT MODAL
// ============================================

var currentAuditData = null;

function openDetailedAudit(result) {
    currentAuditData = result;
    var modal = document.getElementById('detailedAuditModal');
    if (!modal) return;
    
    // Populate URL
    document.getElementById('detailedAuditUrl').innerHTML = '<a href="' + result.url + '" target="_blank">' + result.url + '</a>';
    
    // Populate Keywords
    var metaKeywords = result.meta_keywords || '-';
    document.getElementById('metaKeywords').textContent = metaKeywords;
    
    var topKeywordsDiv = document.getElementById('topKeywords');
    topKeywordsDiv.innerHTML = '';
    if (result.top_keywords && result.top_keywords.length > 0) {
        result.top_keywords.forEach(function(kw) {
            var tag = document.createElement('span');
            tag.className = 'keyword-tag';
            tag.textContent = kw.keyword + ' (' + kw.count + ')';
            topKeywordsDiv.appendChild(tag);
        });
    } else {
        topKeywordsDiv.innerHTML = '<span class="text-muted">No keywords found</span>';
    }
    
    // Populate Issues
    var issuesDiv = document.getElementById('detailedIssues');
    issuesDiv.innerHTML = '';
    if (result.warnings && result.warnings.length > 0) {
        result.warnings.forEach(function(warning) {
            var issueItem = document.createElement('div');
            issueItem.className = 'issue-item ' + getSeverityClass(warning);
            
            var issueName = document.createElement('div');
            issueName.className = 'issue-name';
            issueName.textContent = warning;
            
            var issueFix = document.createElement('div');
            issueFix.className = 'issue-fix';
            issueFix.innerHTML = getIssueFix(warning);
            
            issueItem.appendChild(issueName);
            issueItem.appendChild(issueFix);
            issuesDiv.appendChild(issueItem);
        });
    } else {
        issuesDiv.innerHTML = '<div class="success-message">✓ No issues found!</div>';
    }
    
    // Populate Broken Links
    var brokenLinksDiv = document.getElementById('detailedBrokenLinks');
    var brokenLinksSection = document.getElementById('brokenLinksSection');
    if (result.broken_link_samples && result.broken_link_samples.length > 0) {
        brokenLinksSection.style.display = 'block';
        brokenLinksDiv.innerHTML = '<p><strong>Found ' + result.broken_links + ' broken links</strong> (showing first ' + result.broken_link_samples.length + '):</p>';
        result.broken_link_samples.forEach(function(link) {
            var linkItem = document.createElement('div');
            linkItem.className = 'broken-link-item';
            linkItem.innerHTML = '<a href="' + link + '" target="_blank">' + link + '</a>';
            brokenLinksDiv.appendChild(linkItem);
        });
    } else {
        brokenLinksSection.style.display = 'none';
    }
    
    // Populate Images
    var imagesDiv = document.getElementById('detailedImages');
    var imagesSummaryDiv = document.getElementById('imagesSummary');
    var imagesSection = document.getElementById('imagesSection');
    
    if (result.images_details && result.images_details.length > 0) {
        imagesSection.style.display = 'block';
        
        // Summary
        var issueCount = result.images_details.filter(function(img) { return img.has_issues; }).length;
        imagesSummaryDiv.innerHTML = '<p><strong>' + result.total_images + ' total images</strong> | ' + 
            issueCount + ' with issues | ' + 
            result.images_missing_alt + ' missing alt text | ' +
            result.images_no_dimensions + ' missing dimensions</p>';
        
        // Show images with issues first
        imagesDiv.innerHTML = '';
        var sortedImages = result.images_details.slice().sort(function(a, b) {
            return (b.has_issues ? 1 : 0) - (a.has_issues ? 1 : 0);
        });
        
        sortedImages.forEach(function(img) {
            var imgCard = document.createElement('div');
            imgCard.className = 'image-card' + (img.has_issues ? ' image-has-issues' : '');
            
            var imgPreview = document.createElement('div');
            imgPreview.className = 'image-preview';
            var imgEl = document.createElement('img');
            imgEl.src = img.src;
            imgEl.alt = img.alt || 'No alt text';
            imgEl.onerror = function() { this.src = 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" width="100" height="100"%3E%3Crect fill="%23ddd" width="100" height="100"/%3E%3Ctext x="50%25" y="50%25" text-anchor="middle" dy=".3em" fill="%23999"%3ENo Image%3C/text%3E%3C/svg%3E'; };
            imgPreview.appendChild(imgEl);
            
            var imgInfo = document.createElement('div');
            imgInfo.className = 'image-info';
            
            var imgUrl = document.createElement('div');
            imgUrl.className = 'image-url';
            imgUrl.innerHTML = '<a href="' + img.src + '" target="_blank" title="' + img.src + '">' + img.src.substring(0, 50) + (img.src.length > 50 ? '...' : '') + '</a>';
            
            var imgDetails = document.createElement('div');
            imgDetails.className = 'image-details';
            imgDetails.innerHTML = '<strong>Alt:</strong> ' + (img.alt || '<em>Missing</em>') + '<br>' +
                '<strong>Dimensions:</strong> ' + (img.width || '?') + 'x' + (img.height || '?') + '<br>' +
                '<strong>Loading:</strong> ' + (img.loading || 'default');
            
            if (img.issues && img.issues.length > 0) {
                var imgIssues = document.createElement('div');
                imgIssues.className = 'image-issues';
                imgIssues.innerHTML = '<strong>Issues:</strong> ' + img.issues.join(', ');
                imgDetails.appendChild(imgIssues);
            }
            
            imgInfo.appendChild(imgUrl);
            imgInfo.appendChild(imgDetails);
            
            imgCard.appendChild(imgPreview);
            imgCard.appendChild(imgInfo);
            imagesDiv.appendChild(imgCard);
        });
    } else if (result.total_images > 0) {
        imagesSection.style.display = 'block';
        imagesSummaryDiv.innerHTML = '<p><strong>' + result.total_images + ' total images</strong></p>';
        imagesDiv.innerHTML = '<p class="text-muted">Detailed image information not available for this audit.</p>';
    } else {
        imagesSection.style.display = 'none';
    }
    
    // Populate Render-Blocking Resources
    var renderBlockingDiv = document.getElementById('detailedRenderBlocking');
    var renderBlockingSection = document.getElementById('renderBlockingSection');
    
    if (result.render_blocking_resources && result.render_blocking_resources.length > 0) {
        renderBlockingSection.style.display = 'block';
        renderBlockingDiv.innerHTML = '<p><strong>' + result.render_blocking_count + ' render-blocking resources found</strong> (showing first ' + result.render_blocking_resources.length + '):</p>';
        
        result.render_blocking_resources.forEach(function(resource) {
            var resourceItem = document.createElement('div');
            resourceItem.className = 'resource-item resource-' + resource.type;
            resourceItem.innerHTML = '<div class="resource-type">' + resource.type.toUpperCase() + '</div>' +
                '<div class="resource-src"><a href="' + resource.src + '" target="_blank">' + resource.src + '</a></div>' +
                '<div class="resource-reason">' + resource.reason + '</div>' +
                '<div class="resource-fix">' + getResourceFix(resource.type) + '</div>';
            renderBlockingDiv.appendChild(resourceItem);
        });
    } else if (result.render_blocking_count > 0) {
        renderBlockingSection.style.display = 'block';
        renderBlockingDiv.innerHTML = '<p><strong>' + result.render_blocking_count + ' render-blocking resources found</strong></p>' +
            '<p class="text-muted">Detailed resource information not available for this audit.</p>';
    } else {
        renderBlockingSection.style.display = 'none';
    }
    
    // Show modal
    modal.classList.remove('hidden');
    document.body.style.overflow = 'hidden';
}

function closeDetailedAudit() {
    var modal = document.getElementById('detailedAuditModal');
    if (modal) {
        modal.classList.add('hidden');
        document.body.style.overflow = '';
    }
    currentAuditData = null;
}

function getIssueFix(warning) {
    var fixes = {
        'Missing title': '💡 Add a unique, descriptive &lt;title&gt; tag (30-60 characters) in the &lt;head&gt; section.',
        'Title too short': '💡 Expand your title to at least 30 characters for better SEO impact.',
        'Title too long': '💡 Shorten your title to 60 characters or less to prevent truncation in search results.',
        'Missing meta description': '💡 Add a &lt;meta name="description"&gt; tag with a compelling summary (120-160 characters).',
        'Description too short': '💡 Expand your meta description to at least 120 characters.',
        'Description too long': '💡 Shorten your meta description to 160 characters or less.',
        'Missing H1': '💡 Add a single &lt;h1&gt; tag with your main page heading.',
        'Multiple H1 tags': '💡 Use only one &lt;h1&gt; tag per page. Convert additional H1s to &lt;h2&gt; or lower.',
        'No H2 headings': '💡 Add &lt;h2&gt; headings to structure your content and improve readability.',
        'No canonical tag': '💡 Add &lt;link rel="canonical" href="your-url"&gt; to specify the preferred URL.',
        'Not using HTTPS': '🔒 Migrate to HTTPS with an SSL certificate for security and SEO benefits.',
        'Thin content': '💡 Add more valuable content (aim for 300+ words) to improve rankings.',
        'No robots.txt': '💡 Create a robots.txt file at your domain root to guide search engine crawlers.',
        'No sitemap.xml': '💡 Generate and submit an XML sitemap to help search engines discover your pages.',
        'Large page size': '⚡ Optimize images, minify CSS/JS, and enable compression to reduce page size.',
        'Slow response': '⚡ Improve server performance, enable caching, and consider using a CDN.',
        'Missing viewport': '📱 Add &lt;meta name="viewport" content="width=device-width, initial-scale=1"&gt; for mobile compatibility.',
        'Missing lang attribute': '🌐 Add lang="en" (or appropriate language) to your &lt;html&gt; tag.',
        'No Open Graph': '📱 Add Open Graph meta tags for better social media sharing.',
        'No structured data': '🔍 Implement Schema.org structured data to enhance search results.',
        'URL too long': '💡 Keep URLs under 75 characters for better usability.',
        'URL contains underscores': '💡 Replace underscores with hyphens in URLs (e.g., my-page instead of my_page).'
    };
    
    for (var key in fixes) {
        if (warning.includes(key)) {
            return fixes[key];
        }
    }
    
    // Default fix suggestions
    if (warning.includes('Images missing alt')) {
        return '💡 Add descriptive alt attributes to all images for accessibility and SEO.';
    }
    if (warning.includes('broken links')) {
        return '💡 Fix or remove broken links to improve user experience and crawlability.';
    }
    if (warning.includes('render-blocking')) {
        return '⚡ Add async/defer attributes to scripts or move them to the footer.';
    }
    if (warning.includes('Images without dimensions')) {
        return '⚡ Add width and height attributes to images to prevent layout shifts (CLS).';
    }
    if (warning.includes('Images not lazy')) {
        return '⚡ Add loading="lazy" to images below the fold to improve page speed.';
    }
    if (warning.includes('Redirect chain')) {
        return '💡 Remove unnecessary redirects by linking directly to the final destination.';
    }
    
    return '💡 Review and address this issue according to SEO best practices.';
}

function getResourceFix(type) {
    if (type === 'script') {
        return '💡 Add async or defer attribute, or move to bottom of &lt;body&gt;';
    } else if (type === 'stylesheet') {
        return '💡 Add media="print" for print styles, inline critical CSS, or load asynchronously';
    }
    return '';
}

// ============================================
// EXPOSE FUNCTIONS GLOBALLY FOR ONCLICK HANDLERS
// ============================================

window.toggleHistory = function() {
    var historyList = document.getElementById('historyList');
    if (historyList) {
        historyList.classList.toggle('hidden');
    }
};

window.handleClearClick = handleClearClick;
window.cancelCurrentOperation = cancelCurrentOperation;
window.showToast = showToast;
window.calculateSeoScore = calculateSeoScore;
window.getScoreClass = getScoreClass;
window.getSeverityClass = getSeverityClass;
window.openDetailedAudit = openDetailedAudit;
window.closeDetailedAudit = closeDetailedAudit;
