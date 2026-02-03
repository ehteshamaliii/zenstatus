/* ==============================================
   EXPORT - ZenStatus
   ==============================================
   Export functions for JSON, CSV, and print
*/

function printSeoReport() {
    window.print();
}

function exportSeoJson() {
    if (!lastSeoResults.length) {
        showToast('Run an SEO audit first.', 'error');
        return;
    }
    var blob = new Blob([JSON.stringify(lastSeoResults, null, 2)], { type: 'application/json' });
    var link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = 'seo-audit.json';
    link.click();
    URL.revokeObjectURL(link.href);
    showToast('JSON exported successfully.', 'success');
}

function exportSeoCsv() {
    if (!lastSeoResults.length) {
        showToast('Run an SEO audit first.', 'error');
        return;
    }

    var headers = [
        'url', 'seo_score', 'status_code', 'status_message', 'response_time', 
        'title', 'title_length', 'meta_description', 'meta_description_length',
        'h1_count', 'h2_count', 'h3_count', 'h4_count', 'word_count', 
        'internal_links', 'external_links', 'images_missing_alt', 'total_images',
        'https', 'robots', 'canonical', 'has_viewport', 'has_lang', 'lang',
        'has_og_tags', 'og_title', 'has_schema', 'schema_types', 'warnings', 'h1_samples'
    ];

    var escapeCsv = function(val) {
        var v = (val === null || val === undefined ? '' : val).toString();
        if (v.indexOf('"') !== -1 || v.indexOf(',') !== -1 || v.indexOf('\n') !== -1) {
            return '"' + v.replace(/"/g, '""') + '"';
        }
        return v;
    };

    var rows = lastSeoResults.map(function(r) {
        var score = calculateSeoScore(r);
        return [
            r.url,
            score,
            r.status_code,
            r.status_message,
            r.response_time,
            r.title,
            r.title_length,
            r.meta_description,
            r.meta_description_length,
            r.h1_count,
            r.h2_count || 0,
            r.h3_count || 0,
            r.h4_count || 0,
            r.word_count,
            r.internal_links,
            r.external_links,
            r.images_missing_alt,
            r.total_images,
            r.https ? 'Yes' : 'No',
            r.robots,
            r.canonical,
            r.has_viewport ? 'Yes' : 'No',
            r.has_lang ? 'Yes' : 'No',
            r.lang || '',
            r.has_og_tags ? 'Yes' : 'No',
            r.og_title || '',
            r.has_schema ? 'Yes' : 'No',
            (r.schema_types || []).join(' | '),
            (r.warnings || []).join(' | '),
            (r.h1_samples || []).join(' | ')
        ].map(escapeCsv).join(',');
    });

    var csv = headers.join(',') + '\n' + rows.join('\n');
    var blob = new Blob([csv], { type: 'text/csv' });
    var link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = 'seo-audit.csv';
    link.click();
    URL.revokeObjectURL(link.href);
    showToast('CSV exported successfully.', 'success');
}

function exportSeoPerSiteCsv() {
    if (!lastSeoResults.length) {
        showToast('Run an SEO audit first.', 'error');
        return;
    }
    
    var escapeCsv = function(val) {
        var v = (val === null || val === undefined ? '' : val).toString();
        if (v.indexOf('"') !== -1 || v.indexOf(',') !== -1 || v.indexOf('\n') !== -1 || v.indexOf('\r') !== -1) {
            return '"' + v.replace(/"/g, '""') + '"';
        }
        return v;
    };
    
    var grouped = {};
    lastSeoResults.forEach(function(r) {
        var parser = document.createElement('a');
        parser.href = r.url;
        var host = parser.hostname || 'unknown-site';
        if (!grouped[host]) grouped[host] = [];
        grouped[host].push(r);
    });

    var hosts = Object.keys(grouped);
    var downloadIndex = 0;
    
    function downloadNext() {
        if (downloadIndex >= hosts.length) {
            showToast('Exported ' + hosts.length + ' CSV files.', 'success');
            return;
        }
        
        var host = hosts[downloadIndex];
        var rows = grouped[host].map(function(r) {
            var score = calculateSeoScore(r);
            return [
                r.url,
                score,
                r.status_code,
                r.status_message,
                r.response_time,
                r.title,
                r.title_length,
                r.meta_description,
                r.meta_description_length,
                r.h1_count,
                r.h2_count || 0,
                r.h3_count || 0,
                r.h4_count || 0,
                r.word_count,
                r.internal_links,
                r.external_links,
                r.images_missing_alt,
                r.total_images,
                r.https ? 'Yes' : 'No',
                r.robots,
                r.canonical,
                (r.warnings || []).join(' | '),
                (r.h1_samples || []).join(' | ')
            ].map(escapeCsv).join(',');
        });

        var headers = [
            'url', 'seo_score', 'status_code', 'status_message', 'response_time',
            'title', 'title_length', 'meta_description', 'meta_description_length',
            'h1_count', 'h2_count', 'h3_count', 'h4_count', 'word_count',
            'internal_links', 'external_links', 'images_missing_alt', 'total_images',
            'https', 'robots', 'canonical', 'warnings', 'h1_samples'
        ];

        var csv = headers.join(',') + '\r\n' + rows.join('\r\n');
        var blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
        var link = document.createElement('a');
        link.href = URL.createObjectURL(blob);
        link.download = 'seo-audit-' + host.replace(/[^a-zA-Z0-9_-]/g, '_') + '.csv';
        link.click();
        
        downloadIndex++;
        setTimeout(downloadNext, 300);
    }
    
    downloadNext();
}

// Executive Summary Export (NEW)
function exportExecutiveSummary() {
    if (!lastSeoResults.length) {
        showToast('Run an SEO audit first.', 'error');
        return;
    }

    // Calculate overall stats
    var total = lastSeoResults.length;
    var totalScore = 0;
    var issueCount = { high: 0, medium: 0, low: 0 };
    var warningCounts = {};

    lastSeoResults.forEach(function(r) {
        totalScore += calculateSeoScore(r);
        (r.warnings || []).forEach(function(w) {
            warningCounts[w] = (warningCounts[w] || 0) + 1;
            var sev = getSeverityClass(w);
            if (sev === 'severity-high') issueCount.high++;
            else if (sev === 'severity-medium') issueCount.medium++;
            else issueCount.low++;
        });
    });

    var avgScore = Math.round(totalScore / total);
    var scoreLabel = getScoreLabel(avgScore);

    var report = '# SEO Audit Executive Summary\n\n';
    report += 'Generated: ' + new Date().toLocaleString() + '\n\n';
    report += '## Overall Score: ' + avgScore + '/100 (' + scoreLabel + ')\n\n';
    report += '## Key Metrics\n\n';
    report += '- **Pages Audited:** ' + total + '\n';
    report += '- **High Priority Issues:** ' + issueCount.high + '\n';
    report += '- **Medium Priority Issues:** ' + issueCount.medium + '\n';
    report += '- **Low Priority Issues:** ' + issueCount.low + '\n\n';
    report += '## Top Issues\n\n';

    var topIssues = Object.keys(warningCounts)
        .sort(function(a, b) { return warningCounts[b] - warningCounts[a]; })
        .slice(0, 10);

    topIssues.forEach(function(issue, idx) {
        report += (idx + 1) + '. **' + issue + '** - ' + warningCounts[issue] + ' pages\n';
    });

    report += '\n## Recommended Actions\n\n';
    report += '1. Fix all high-priority issues first (missing titles, H1s)\n';
    report += '2. Add meta descriptions to improve click-through rates\n';
    report += '3. Ensure all pages have canonical tags\n';
    report += '4. Optimize images with proper alt text\n';
    report += '5. Improve page speed if response times exceed 2 seconds\n';

    var blob = new Blob([report], { type: 'text/markdown' });
    var link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = 'seo-executive-summary.md';
    link.click();
    URL.revokeObjectURL(link.href);
    showToast('Executive summary exported.', 'success');
}

// ============================================
// EXPOSE FUNCTIONS GLOBALLY FOR ONCLICK HANDLERS
// ============================================

window.printSeoReport = printSeoReport;
window.exportSeoJson = exportSeoJson;
window.exportSeoCsv = exportSeoCsv;
window.exportSeoPerSiteCsv = exportSeoPerSiteCsv;
window.exportExecutiveSummary = exportExecutiveSummary;
