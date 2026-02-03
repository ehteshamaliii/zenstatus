/* ==============================================
   THEMES - ZenStatus
   ==============================================
   Theme management and favicon updates
   Depends on: storage.js (ZenStorage)
*/

// Theme colors mapping
var themeColors = {
    'default': '#0F4C81',
    'sage': '#768a73',
    'rose': '#B76E79',
    'midnight': '#38bdf8'
};

// SVG favicon template
function createFaviconSvg(color) {
    return '<svg viewBox="0 0 160 160" xmlns="http://www.w3.org/2000/svg">' +
        '<path d="M147.883728,0H12C5.3725586,0,0,5.3726196,0,12v26c0,6.6274414,5.3725586,12,12,12h53.8650513L3.5147095,112.3502808C1.0344238,114.8305664-.1195068,118.1259766.0256958,121.3742065c-.0071411.1702271-.0256958.3375244-.0256958.5095215v26c0,6.6274414,5.3725586,12,12,12h26c.1224976,0,.2412109-.0146484.362793-.0183105,3.300293.1918945,6.6642456-.9597778,9.18573-3.4812622l108.8053589-108.8053589c2.4470215-2.4470215,3.6036987-5.6875,3.4952393-8.8931885.0129395-.2282104.0346069-.4541626.0346069-.6856079V12c0-6.6273804-5.3726196-12-12-12Z" fill="' + color + '"/>' +
        '<rect x="109.8837138" y="109.8837451" width="50" height="50" rx="12" ry="12" fill="' + color + '"/>' +
        '</svg>';
}

function updateFavicon(themeName) {
    var color = themeColors[themeName] || themeColors['default'];
    var svg = createFaviconSvg(color);
    var blob = new Blob([svg], { type: 'image/svg+xml' });
    var url = URL.createObjectURL(blob);
    var favicon = document.getElementById('favicon');
    if (favicon) {
        var oldUrl = favicon.href;
        favicon.href = url;
        // Clean up old blob URL if it was a blob
        if (oldUrl && oldUrl.startsWith('blob:')) {
            URL.revokeObjectURL(oldUrl);
        }
    }
}

// Use local storage to persist theme
function initTheme() {
    var savedTheme = ZenStorage.getItem('zenTheme', 'default');
    setTheme(savedTheme);
}

function toggleThemeMenu() {
    var menu = document.getElementById('themeMenu');
    if (menu) menu.classList.toggle('active');
}

function setTheme(themeName) {
    document.documentElement.setAttribute('data-theme', themeName);
    ZenStorage.setItem('zenTheme', themeName);
    var menu = document.getElementById('themeMenu');
    if (menu) menu.classList.remove('active');
    updateFavicon(themeName);
}

// Close menu when clicking outside
window.addEventListener('click', function(event) {
    if (!event.target.matches('.theme-btn') && !event.target.closest('.theme-btn')) {
        var menu = document.getElementById('themeMenu');
        if (menu && menu.classList.contains('active')) {
            menu.classList.remove('active');
        }
    }
});

// Initialize on page load
document.addEventListener('DOMContentLoaded', initTheme);
