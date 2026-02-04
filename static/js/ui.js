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
