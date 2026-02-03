/* ==============================================
   MAIN - ZenStatus
   ==============================================
   Application initialization
   Depends on: storage.js (ZenStorage), ui.js, api.js
*/

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', function() {
    // Theme is already initialized in themes.js
    console.log('ZenStatus initialized');
    
    // Initialize history dropdown
    initAuditHistory();
    
    // Initialize file upload
    initFileUpload();
});

// ============================================
// AUDIT HISTORY (using ZenStorage)
// ============================================

var HISTORY_KEY = 'zenStatusAuditHistory';
var MAX_HISTORY = 10;

function initAuditHistory() {
    var historyContainer = document.getElementById('historyContainer');
    if (!historyContainer) return;
    
    // Hide history container if storage not available
    if (!ZenStorage.isAvailable()) {
        historyContainer.style.display = 'none';
        return;
    }
    
    updateHistoryUI();
}

function saveAuditToHistory(results) {
    if (!results || results.length === 0) return;
    if (!ZenStorage.isAvailable()) return;
    
    var history = getAuditHistory();
    var entry = {
        id: Date.now(),
        date: new Date().toISOString(),
        pageCount: results.length,
        sites: [...new Set(results.map(function(r) {
            try { return new URL(r.url).hostname; } catch(e) { return 'unknown'; }
        }))],
        avgScore: Math.round(results.reduce(function(sum, r) {
            return sum + calculateSeoScore(r);
        }, 0) / results.length),
        results: results
    };
    
    history.unshift(entry);
    if (history.length > MAX_HISTORY) {
        history = history.slice(0, MAX_HISTORY);
    }
    
    if (!ZenStorage.setJSON(HISTORY_KEY, history)) {
        // Storage full, remove oldest entries
        history = history.slice(0, 5);
        ZenStorage.setJSON(HISTORY_KEY, history);
    }
    
    updateHistoryUI();
    showToast('Audit saved to history', 'success');
}

function getAuditHistory() {
    return ZenStorage.getJSON(HISTORY_KEY, []);
}

function loadAuditFromHistory(id) {
    try {
        console.log('=== loadAuditFromHistory START ===');
        console.log('Loading audit with id:', id);
        var history = getAuditHistory();
        console.log('History entries:', history.length);
        var entry = history.find(function(h) { return h.id === id; });
        console.log('Found entry:', entry ? 'yes' : 'no');
        
        if (entry && entry.results && entry.results.length > 0) {
            console.log('Results count:', entry.results.length);
            // Update global variable
            if (typeof window.lastSeoResults !== 'undefined') {
                window.lastSeoResults = entry.results;
            }
            lastSeoResults = entry.results;
            
            // Check if displaySeoResults exists
            if (typeof window.displaySeoResults === 'function') {
                console.log('Calling window.displaySeoResults...');
                try {
                    window.displaySeoResults(entry.results, null);
                    console.log('displaySeoResults completed successfully');
                    showToast('Loaded audit from ' + new Date(entry.date).toLocaleDateString(), 'success');
                } catch (displayError) {
                    console.error('Error in displaySeoResults:', displayError);
                    showToast('Error displaying results: ' + displayError.message, 'error');
                }
            } else if (typeof displaySeoResults === 'function') {
                console.log('Calling local displaySeoResults...');
                displaySeoResults(entry.results, null);
                showToast('Loaded audit from ' + new Date(entry.date).toLocaleDateString(), 'success');
            } else {
                console.error('displaySeoResults function not found');
                showToast('Error: Display function not available', 'error');
            }
        } else {
            console.log('No results in entry');
            showToast('No results found in history entry', 'error');
        }
        console.log('=== loadAuditFromHistory END ===');
    } catch (e) {
        console.error('Error in loadAuditFromHistory:', e);
        showToast('Error loading audit: ' + e.message, 'error');
    }
}

function clearAuditHistory() {
    if (!ZenStorage.isAvailable()) return;
    ZenStorage.removeItem(HISTORY_KEY);
    updateHistoryUI();
    showToast('History cleared', 'info');
}

function updateHistoryUI() {
    var historyList = document.getElementById('historyList');
    if (!historyList) return;
    
    var history = getAuditHistory();
    
    if (history.length === 0) {
        historyList.innerHTML = '<div class="history-empty">No saved audits</div>';
        return;
    }
    
    var html = history.map(function(h) {
        var date = new Date(h.date);
        var dateStr = date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
        var sites = h.sites.slice(0, 2).join(', ') + (h.sites.length > 2 ? '...' : '');
        return '<div class="history-item" onclick="loadAuditFromHistory(' + h.id + ')">' +
            '<div class="history-item-date">' + dateStr + '</div>' +
            '<div class="history-item-info">' + h.pageCount + ' pages | Avg Score: ' + h.avgScore + '</div>' +
            '<div class="history-item-sites">' + sites + '</div>' +
            '</div>';
    }).join('');
    
    html += '<div class="history-clear" onclick="clearAuditHistory()">Clear History</div>';
    historyList.innerHTML = html;
}

// ============================================
// FILE UPLOAD
// ============================================

function initFileUpload() {
    var fileInput = document.getElementById('urlFileInput');
    if (!fileInput) return;
    
    fileInput.addEventListener('change', function(e) {
        var file = e.target.files[0];
        if (!file) return;
        
        var reader = new FileReader();
        reader.onload = function(event) {
            var content = event.target.result;
            var urls = content.split(/[\r\n]+/).filter(function(line) {
                return line.trim() && !line.startsWith('#');
            });
            
            var textarea = document.getElementById('urls');
            if (textarea) {
                textarea.value = urls.join('\n');
                showToast('Loaded ' + urls.length + ' URLs from file', 'success');
            }
        };
        reader.readAsText(file);
    });
}

function triggerFileUpload() {
    var fileInput = document.getElementById('urlFileInput');
    if (fileInput) fileInput.click();
}

// ============================================
// FILTER & SORT
// ============================================

var currentFilter = 'all';
var currentSort = 'default';

function filterCards(filter) {
    console.log('filterCards called with:', filter);
    currentFilter = filter;
    applyFilterSort();
    
    // Update active button - use querySelectorAll to find the clicked button
    document.querySelectorAll('.filter-btn').forEach(function(btn) {
        btn.classList.remove('active');
        // Match button by its onclick filter value
        if (btn.getAttribute('onclick') && btn.getAttribute('onclick').indexOf("'" + filter + "'") !== -1) {
            btn.classList.add('active');
        }
    });
}

function sortCards(sortBy) {
    currentSort = sortBy;
    applyFilterSort();
}

function applyFilterSort() {
    var cards = Array.from(document.querySelectorAll('.seo-card'));
    
    // First, filter the cards
    cards.forEach(function(card) {
        var score = parseInt(card.dataset.score || 0);
        var hasIssues = card.dataset.hasIssues === 'true';
        
        var show = true;
        if (currentFilter === 'issues' && !hasIssues) show = false;
        if (currentFilter === 'good' && score < 70) show = false;
        if (currentFilter === 'poor' && score >= 70) show = false;  // Show only scores < 70
        
        card.style.display = show ? '' : 'none';
    });
    
    // Then sort the visible cards within each site-group
    if (currentSort !== 'default') {
        document.querySelectorAll('.site-group .seo-cards').forEach(function(container) {
            var sortableCards = Array.from(container.querySelectorAll('.seo-card'));
            
            sortableCards.sort(function(a, b) {
                var scoreA = parseInt(a.dataset.score || 0);
                var scoreB = parseInt(b.dataset.score || 0);
                var issuesA = parseInt(a.dataset.issueCount || 0);
                var issuesB = parseInt(b.dataset.issueCount || 0);
                
                if (currentSort === 'score-asc') return scoreA - scoreB;
                if (currentSort === 'score-desc') return scoreB - scoreA;
                if (currentSort === 'issues') return issuesB - issuesA;
                return 0;
            });
            
            // Re-append in sorted order
            sortableCards.forEach(function(card) {
                container.appendChild(card);
            });
        });
    }
}

// ============================================
// EXPOSE FUNCTIONS GLOBALLY FOR ONCLICK HANDLERS
// ============================================

window.loadAuditFromHistory = loadAuditFromHistory;
window.clearAuditHistory = clearAuditHistory;
window.triggerFileUpload = triggerFileUpload;
window.filterCards = filterCards;
window.sortCards = sortCards;
window.saveAuditToHistory = saveAuditToHistory;
