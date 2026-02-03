/* ==============================================
   STORAGE - ZenStatus
   ==============================================
   Unified localStorage wrapper with safe fallbacks
   This module MUST be loaded first before any other JS
*/

// Suppress unhandled storage-related promise rejections (from VS Code Simple Browser)
window.addEventListener('unhandledrejection', function(event) {
    if (event.reason && event.reason.message && 
        event.reason.message.indexOf('storage') !== -1) {
        event.preventDefault();
        console.log('ZenStorage: Suppressed external storage error');
    }
});

// Storage module - self-contained with no external dependencies
var ZenStorage = (function() {
    'use strict';
    
    // Cache the storage availability check result
    var _isAvailable = null;
    var _memoryFallback = {};
    
    /**
     * Check if we're in a restricted context (iframe, extension, etc.)
     * Wrapped completely in try-catch to handle any security errors
     */
    function _isRestrictedContext() {
        try {
            // Any access to window.top in a cross-origin iframe throws
            return window.self !== window.top;
        } catch (e) {
            // If we can't access window.top, we're in a restricted context
            return true;
        }
    }
    
    /**
     * Test if localStorage is actually available and working
     * Only runs once, then caches the result
     */
    function _testStorage() {
        if (_isAvailable !== null) {
            return _isAvailable;
        }
        
        // Assume not available by default
        _isAvailable = false;
        
        // Skip entirely in restricted contexts
        if (_isRestrictedContext()) {
            console.log('ZenStorage: Running in restricted context, using memory fallback');
            return false;
        }
        
        try {
            // Check if localStorage exists
            if (typeof window === 'undefined') return false;
            if (typeof window.localStorage === 'undefined') return false;
            if (!window.localStorage) return false;
            
            // Actually try to use it
            var testKey = '__zen_storage_test__';
            window.localStorage.setItem(testKey, 'test');
            var result = window.localStorage.getItem(testKey);
            window.localStorage.removeItem(testKey);
            
            if (result === 'test') {
                _isAvailable = true;
                console.log('ZenStorage: localStorage is available');
            }
        } catch (e) {
            // Any error means storage is not available
            console.log('ZenStorage: localStorage not available -', e.message);
            _isAvailable = false;
        }
        
        return _isAvailable;
    }
    
    /**
     * Check if storage is available
     * @returns {boolean}
     */
    function isAvailable() {
        return _testStorage();
    }
    
    /**
     * Get an item from storage
     * @param {string} key - The key to retrieve
     * @param {*} defaultValue - Default value if key doesn't exist
     * @returns {string|*} The value or defaultValue
     */
    function getItem(key, defaultValue) {
        if (defaultValue === undefined) defaultValue = null;
        
        if (!_testStorage()) {
            // Use memory fallback
            return _memoryFallback.hasOwnProperty(key) ? _memoryFallback[key] : defaultValue;
        }
        
        try {
            var value = window.localStorage.getItem(key);
            return value !== null ? value : defaultValue;
        } catch (e) {
            return _memoryFallback.hasOwnProperty(key) ? _memoryFallback[key] : defaultValue;
        }
    }
    
    /**
     * Set an item in storage
     * @param {string} key - The key to set
     * @param {string} value - The value to store
     * @returns {boolean} True if successful
     */
    function setItem(key, value) {
        // Always update memory fallback
        _memoryFallback[key] = value;
        
        if (!_testStorage()) {
            return false;
        }
        
        try {
            window.localStorage.setItem(key, value);
            return true;
        } catch (e) {
            // Storage might be full
            console.log('ZenStorage: Failed to save -', e.message);
            return false;
        }
    }
    
    /**
     * Remove an item from storage
     * @param {string} key - The key to remove
     */
    function removeItem(key) {
        delete _memoryFallback[key];
        
        if (!_testStorage()) {
            return;
        }
        
        try {
            window.localStorage.removeItem(key);
        } catch (e) {
            // Silently fail
        }
    }
    
    /**
     * Get a JSON object from storage
     * @param {string} key - The key to retrieve
     * @param {*} defaultValue - Default value if parse fails or key doesn't exist
     * @returns {*} The parsed object or defaultValue
     */
    function getJSON(key, defaultValue) {
        if (defaultValue === undefined) defaultValue = null;
        
        var value = getItem(key, null);
        if (value === null) return defaultValue;
        
        try {
            return JSON.parse(value);
        } catch (e) {
            return defaultValue;
        }
    }
    
    /**
     * Set a JSON object in storage
     * @param {string} key - The key to set
     * @param {*} value - The object to store (will be stringified)
     * @returns {boolean} True if successful
     */
    function setJSON(key, value) {
        try {
            return setItem(key, JSON.stringify(value));
        } catch (e) {
            return false;
        }
    }
    
    // Public API
    return {
        isAvailable: isAvailable,
        getItem: getItem,
        setItem: setItem,
        removeItem: removeItem,
        getJSON: getJSON,
        setJSON: setJSON
    };
})();

// Make it globally accessible
window.ZenStorage = ZenStorage;
