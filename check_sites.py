from flask import Flask, render_template_string, request, jsonify, Response
import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from urllib.parse import urlparse
import xml.etree.ElementTree as ET
import re
import json
import time
import gzip

app = Flask(__name__)

# HTML Template
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ZenStatus - Website Auditor</title>
    <link rel="icon" id="favicon" type="image/svg+xml" href="/static/logo.svg">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;500;600;700&family=Outfit:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {
            /* Default: Serenity (Classic Blue & Cool Grays) */
            --bg-primary: #ffffff;
            --bg-secondary: #f8f9fa;
            --bg-tertiary: #e9ecef;
            --text-primary: #1a202c;
            --text-secondary: #4a5568;
            --text-on-accent: #ffffff;
            --accent-primary: #0F4C81; /* Pantone Classic Blue */
            --accent-hover: #0a365c;
            --border-color: #e2e8f0;
            --card-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
            --header-bg: #0F4C81;
            --header-text: #ffffff;
            
            --status-ok-bg: #f0fdf4;
            --status-ok-border: #86efac;
            --status-ok-text: #166534;
            
            --status-warn-bg: #fffbeb;
            --status-warn-border: #fcd34d;
            --status-warn-text: #92400e;
            
            --status-error-bg: #fef2f2;
            --status-error-border: #fca5a5;
            --status-error-text: #991b1b;
            
            --font-display: 'Montserrat', sans-serif;
            --font-body: 'Outfit', sans-serif;
        }

        [data-theme="sage"] {
            /* Sage (Renewal) - Desert Sage & Earth Tones */
            --bg-primary: #fcfcfc;
            --bg-secondary: #f4f5f1;
            --bg-tertiary: #e8e8e4;
            --text-primary: #2c3327;
            --text-secondary: #5c6159;
            --text-on-accent: #ffffff;
            --accent-primary: #5b6e58;
            --accent-hover: #4a5a47;
            --border-color: #d8dcd6;
            --header-bg: #768a73; 
            --header-text: #ffffff;
        }

        [data-theme="rose"] {
            /* Rose (Compassion) - Rose Quartz & Soft Grays */
            --bg-primary: #fffafa;
            --bg-secondary: #fdf2f4;
            --bg-tertiary: #fce7eb;
            --text-primary: #4a4a4a;
            --text-secondary: #757575;
            --text-on-accent: #ffffff;
            --accent-primary: #B76E79; 
            --accent-hover: #9e5b65;
            --border-color: #f0dcdf;
            --header-bg: #d69ca5;
            --header-text: #ffffff;
        }

        /* Dark Mode Potential Future Proofing */
        [data-theme="midnight"] {
            --bg-primary: #0f172a;
            --bg-secondary: #1e293b;
            --bg-tertiary: #334155;
            --text-primary: #f1f5f9;
            --text-secondary: #cbd5e1;
            --text-on-accent: #ffffff;
            --accent-primary: #38bdf8;
            --accent-hover: #0284c7;
            --border-color: #334155;
            --header-bg: #020617;
            --header-text: #f8fafc;
        }

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: var(--font-body);
            background: var(--bg-primary);
            color: var(--text-primary);
            min-height: 100vh;
            line-height: 1.6;
            transition: background 0.3s ease, color 0.3s ease;
        }
        
        .container {
            width: 100%;
            background: var(--bg-primary);
            overflow: hidden;
        }
        
        .header {
            background: var(--header-bg);
            color: var(--header-text);
            padding: 80px 60px;
            position: relative;
            overflow: visible;
            transition: background 0.3s ease;
        }

        /* Subtle pattern overlay */
        .header::before {
            content: '';
            position: absolute;
            inset: 0;
            background-image: 
                radial-gradient(circle at 20% 150%, rgba(255,255,255,0.1) 0%, transparent 50%),
                radial-gradient(circle at 80% -50%, rgba(255,255,255,0.15) 0%, transparent 50%);
            pointer-events: none;
        }
        
        .header-content {
            position: relative;
            z-index: 2;
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
        }

        .title-group {
            display: flex;
            flex-direction: column;
        }

        .logo-row {
            display: flex;
            align-items: center;
            gap: 16px;
            margin-bottom: 12px;
        }
        
        .logo {
            height: 48px;
            width: auto;
            fill: var(--header-text);
            color: var(--header-text);
            transition: fill 0.3s ease;
        }

        .title-group h1 {
            font-family: var(--font-display);
            font-size: 2.5em;
            margin: 0;
            font-weight:700;
            letter-spacing: -2px;
            color: var(--header-text);
            line-height: 1;
            text-transform:uppercase;
        }
        
        .title-group p {
            font-family: var(--font-body);
            color: rgba(255, 255, 255, 0.9);
            font-size: 1.2em;
            font-weight: 300;
            letter-spacing: 0.5px;
            max-width: 600px;
        }

        .theme-switcher {
            position: relative;
            display: inline-block;
        }

        .theme-btn {
            background: rgba(255,255,255,0.2);
            border: 1px solid rgba(255,255,255,0.3);
            color: white;
            padding: 10px 20px;
            border-radius: 30px;
            cursor: pointer;
            font-family: var(--font-body);
            font-size: 0.9em;
            display: flex;
            align-items: center;
            gap: 8px;
            transition: all 0.2s ease;
        }

        .theme-btn:hover {
            background: rgba(255,255,255,0.3);
        }

        .theme-menu {
            position: absolute;
            top: 100%;
            right: 0;
            margin-top: 10px;
            background: var(--bg-primary);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 8px;
            box-shadow: var(--card-shadow);
            display: none;
            min-width: 180px;
            z-index: 100;
        }

        .theme-menu.active {
            display: block;
            animation: fadeIn 0.15s ease-out;
        }

        .theme-option {
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 10px 12px;
            cursor: pointer;
            border-radius: 8px;
            color: var(--text-primary);
            transition: background 0.2s;
        }

        .theme-option:hover {
            background: var(--bg-secondary);
        }

        .color-dot {
            width: 16px;
            height: 16px;
            border-radius: 50%;
            border: 1px solid rgba(0,0,0,0.1);
        }
        
        .content {
            padding: 60px 60px 80px 60px;
            max-width: 100%;
        }
        
        .input-section {
            margin-bottom: 60px;
        }
        
        label {
            display: block;
            font-weight: 500;
            margin-bottom: 16px;
            color: var(--text-primary);
            font-size: 1.1em;
            letter-spacing: -0.3px;
        }
        
        textarea {
            width: 100%;
            min-height: 240px;
            padding: 24px;
            border: 1px solid var(--border-color);
            border-radius: 12px;
            font-family: 'SF Mono', 'Monaco', 'Courier New', monospace;
            font-size: 14px;
            resize: vertical;
            transition: all 0.2s ease;
            background: var(--bg-primary);
            color: var(--text-primary);
            line-height: 1.8;
            box-shadow: inset 0 2px 4px rgba(0,0,0,0.02);
        }
        
        textarea:focus {
            outline: none;
            border-color: var(--accent-primary);
            box-shadow: 0 0 0 3px rgba(15, 76, 129, 0.1);
        }
        
        .button-group {
            display: flex;
            gap: 12px;
            margin-top: 24px;
        }

        .toast-container {
            position: fixed;
            top: 20px;
            right: 20px;
            display: flex;
            flex-direction: column;
            gap: 12px;
            z-index: 2000;
        }

        .toast {
            padding: 16px 20px;
            border-radius: 8px;
            border: 1px solid var(--border-color);
            background: var(--bg-primary);
            box-shadow: var(--card-shadow);
            min-width: 280px;
            font-size: 0.95em;
            color: var(--text-primary);
            animation: slideIn 0.3s ease-out;
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .toast.toast-success { border: 1px solid var(--status-ok-text); background: var(--status-ok-bg); }
        .toast.toast-error { border: 1px solid var(--status-error-text); background: var(--status-error-bg); }
        .toast.toast-info { border: 1px solid var(--accent-primary); background: var(--bg-secondary); }

        @keyframes slideIn {
            from { opacity: 0; transform: translateX(20px); }
            to { opacity: 1; transform: translateX(0); }
        }

        .modal-overlay {
            position: fixed;
            inset: 0;
            background: rgba(0,0,0,0.4);
            backdrop-filter: blur(4px);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 1500;
        }

        .modal-box {
            background: var(--bg-primary);
            border: 1px solid var(--border-color);
            padding: 32px;
            width: 400px;
            border-radius: 16px;
            box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
            display: flex;
            flex-direction: column;
            gap: 24px;
        }

        .modal-message {
            font-size: 1.1em;
            color: var(--text-primary);
            text-align: center;
        }

        .modal-actions {
            display: flex;
            gap: 16px;
            justify-content: center;
        }

        .hidden { display: none !important; }

        .sitemap-controls {
            margin-top: 24px;
            display: flex;
            flex-direction: column;
            gap: 16px;
            background: var(--bg-secondary);
            border: 1px solid var(--border-color);
            padding: 24px;
            border-radius: 12px;
        }

        .checkbox-label {
            display: flex;
            gap: 12px;
            align-items: center;
            font-size: 1em;
            color: var(--text-primary);
            font-weight: 500;
        }

        .sitemap-fields {
            display: flex;
            gap: 16px;
            flex-wrap: wrap;
        }

        .sitemap-fields input[type="text"],
        .sitemap-fields input[type="number"] {
            flex: 1;
            min-width: 220px;
            padding: 12px 16px;
            border: 1px solid var(--border-color);
            border-radius: 8px;
            font-size: 0.95em;
            background: var(--bg-primary);
            color: var(--text-primary);
            transition: all 0.2s ease;
        }

        .sitemap-fields input:focus {
            outline: none;
            border-color: var(--accent-primary);
        }
        
        button {
            padding: 14px 28px;
            font-size: 15px;
            font-weight: 600;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.2s ease;
            letter-spacing: 0.3px;
            font-family: var(--font-body);
        }
        
        .btn-primary {
            background: var(--accent-primary);
            color: var(--text-on-accent);
        }
        
        .btn-primary:hover {
            background: var(--accent-hover);
            transform: translateY(-1px);
        }
        
        .btn-primary:active {
            transform: translateY(0);
        }
        
        .btn-primary:disabled {
            background: var(--text-secondary);
            opacity: 0.5;
            cursor: not-allowed;
            transform: none;
        }
        
        .btn-secondary {
            background: var(--bg-primary);
            color: var(--text-secondary);
            border: 1px solid var(--border-color);
        }
        
        .btn-secondary:hover {
            background: var(--bg-secondary);
            color: var(--text-primary);
            border-color: var(--text-secondary);
        }
        
        .loading {
            display: none;
            text-align: center;
            padding: 80px;
            background: var(--bg-secondary);
            border-radius: 16px;
            border: 1px dashed var(--border-color);
            margin-top: 40px;
        }
        
        .loading.active {
            display: block;
            animation: fadeIn 0.3s ease;
        }
        
        .spinner {
            border: 4px solid var(--border-color);
            border-top: 4px solid var(--accent-primary);
            border-radius: 50%;
            width: 48px;
            height: 48px;
            animation: spin 1s linear infinite;
            margin: 0 auto 24px;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        .results {
            display: none;
            margin-top: 60px;
        }
        
        .results.active {
            display: block;
            animation: fadeIn 0.4s ease-out;
        }
        
        .summary {
            background: var(--bg-primary);
            padding: 40px;
            border-radius: 16px;
            margin-bottom: 32px;
            display: flex;
            justify-content: space-around;
            flex-wrap: wrap;
            gap: 40px;
            border: 1px solid var(--border-color);
            box-shadow: var(--card-shadow);
        }
        
        .summary-item {
            text-align: center;
            flex: 1;
            min-width: 180px;
        }
        
        .summary-item .number {
            font-size: 3.5em;
            font-weight: 700;
            color: var(--text-primary);
            font-family: var(--font-display);
            line-height: 1.2;
        }
        
        .summary-item .label {
            color: var(--text-secondary);
            margin-top: 8px;
            font-size: 0.85em;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        
        .table-container {
            overflow-x: auto;
            border-radius: 16px;
            border: 1px solid var(--border-color);
            background: var(--bg-primary);
            box-shadow: var(--card-shadow);
        }

        .report-section {
            margin-top: 20px;
        }

        .issues-row {
            margin: 16px 0 12px 0;
        }

        /* Site Group Styling */
        .site-group {
            margin-bottom: 48px;
            background: var(--bg-secondary);
            border-radius: 16px;
            padding: 32px;
            border: 1px solid var(--border-color);
        }

        .site-group-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 24px;
            padding-bottom: 16px;
            border-bottom: 2px solid var(--accent-primary);
        }

        .site-group-header h2 {
            font-family: var(--font-display);
            font-size: 1.5em;
            font-weight: 600;
            color: var(--accent-primary);
            margin: 0;
            display: flex;
            align-items: center;
            gap: 12px;
        }


        .site-group-stats {
            display: flex;
            gap: 16px;
        }

        .site-group-stat {
            background: var(--bg-primary);
            padding: 8px 16px;
            border-radius: 8px;
            font-size: 0.85em;
            font-weight: 600;
            color: var(--text-secondary);
            border: 1px solid var(--border-color);
        }

        .site-group-stat span {
            color: var(--accent-primary);
            font-weight: 700;
        }
        #seoCards {
            display: flex !important;
            flex-direction: column;
        }
        .seo-cards {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(420px, 1fr));
            gap: 24px;
        }

        .seo-card {
            border: 1px solid var(--border-color);
            padding: 0;
            background: var(--bg-primary);
            display: flex;
            flex-direction: column;
            border-radius: 16px;
            box-shadow: var(--card-shadow);
            transition: transform 0.2s ease, box-shadow 0.2s ease;
            font-family: var(--font-body);
            overflow: hidden;
        }
        
        .seo-card:hover {
            transform: translateY(-4px);
            box-shadow: 0 12px 24px -8px rgba(0, 0, 0, 0.15);
        }

        .seo-card .card-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 16px 20px;
            background: var(--bg-secondary);
            border-bottom: 1px solid var(--border-color);
            flex-wrap: wrap;
            gap: 8px;
        }

        .seo-card .card-header-left {
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .seo-card .card-header-right {
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .seo-card .card-body {
            padding: 20px;
            display: flex;
            flex-direction: column;
            gap: 16px;
        }

        .seo-card .url {
            font-family: 'SF Mono', 'Monaco', 'Courier New', monospace;
            font-size: 0.9em;
            word-break: break-all;
            color: var(--accent-primary);
            font-weight: 600;
            padding: 12px 16px;
            background: var(--bg-secondary);
            border-radius: 8px;
            border: 1px solid var(--border-color);
        }

        .seo-card .url a {
            color: inherit;
            text-decoration: none;
        }

        .seo-card .url a:hover {
            text-decoration: underline;
        }

        .seo-card .metrics-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 12px;
        }

        .seo-card .metric-item {
            background: var(--bg-secondary);
            padding: 12px;
            border-radius: 8px;
            text-align: center;
            border: 1px solid var(--border-color);
        }

        .seo-card .metric-item .metric-value {
            font-size: 1.25em;
            font-weight: 700;
            color: var(--text-primary);
            font-family: var(--font-display);
        }

        .seo-card .metric-item .metric-label {
            font-size: 0.7em;
            color: var(--text-secondary);
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-top: 4px;
        }

        .seo-card .content-section {
            border: 1px solid var(--border-color);
            border-radius: 8px;
            overflow: hidden;
        }

        .seo-card .content-section-header {
            background: var(--bg-tertiary);
            padding: 8px 12px;
            font-size: 0.75em;
            font-weight: 600;
            color: var(--text-secondary);
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        .seo-card .content-section-body {
            padding: 12px;
            font-size: 0.9em;
            color: var(--text-primary);
            line-height: 1.5;
            max-height: 80px;
            overflow: hidden;
            text-overflow: ellipsis;
        }

        .seo-card .tags-row {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
        }

        .pill {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 6px 12px;
            border-radius: 6px;
            border: 1px solid var(--border-color);
            font-size: 0.8em;
            font-weight: 500;
            background: var(--bg-primary);
            color: var(--text-secondary);
        }

        .pill.status-ok { background: var(--status-ok-bg); border-color: var(--status-ok-border); color: var(--status-ok-text); }
        .pill.status-warn { background: var(--status-warn-bg); border-color: var(--status-warn-border); color: var(--status-warn-text); }
        .pill.status-danger { background: var(--status-error-bg); border-color: var(--status-error-border); color: var(--status-error-text); }

        .pill-number {
            background: var(--accent-primary);
            color: white;
            font-weight: 700;
            min-width: 28px;
            text-align: center;
        }

        .warnings {
            padding: 12px 16px;
            font-size: 0.85em;
            border-radius: 8px;
            border: 1px solid transparent;
            line-height: 1.6;
        }

        .warnings.ok { background: var(--status-ok-bg); color: var(--status-ok-text); border-color: var(--status-ok-border); }
        .warnings.warn { background: var(--status-warn-bg); color: var(--status-warn-text); border-color: var(--status-warn-border); }
        .warnings.danger { background: var(--status-error-bg); color: var(--status-error-text); border-color: var(--status-error-border); }

        .export-actions {
            display: flex;
            gap: 12px;
            flex-wrap: wrap;
            margin: 24px 0;
        }
        
        .export-actions button {
            background: var(--bg-primary);
            color: var(--text-primary);
            border: 1px solid var(--border-color);
            padding: 10px 20px;
            border-radius: 8px;
        }
        
        .export-actions button:hover {
            background: var(--bg-secondary);
            border-color: var(--text-secondary);
        }

        .issues-panel {
            border: 1px solid var(--status-warn-border);
            background: var(--status-warn-bg);
            padding: 24px;
            border-radius: 12px;
            color: var(--status-warn-text);
        }

        .issues-panel h3 {
            margin-bottom: 12px;
            font-size: 1.1em;
            color: var(--status-warn-text);
        }

        .issues-panel ul {
            list-style: disc inside;
            margin-left: 8px;
        }

        @media print {
            @page { size: A4 portrait; margin: 12mm; }
            body { background: #ffffff; color: #000; }
            .header, .input-section, .button-group, .export-actions, .theme-switcher { display: none !important; }
            .seo-card, .summary, .issues-panel, .site-group { box-shadow: none; border: 1px solid #ccc; break-inside: avoid; }
            .site-group { background: #f9f9f9; }
            .seo-card .card-header { background: #f0f0f0; }
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
            background: var(--bg-primary);
        }
        
        thead {
            background: var(--bg-secondary);
            border-bottom: 1px solid var(--border-color);
        }
        
        th {
            padding: 16px 24px;
            text-align: left;
            font-weight: 600;
            color: var(--text-secondary);
            border-bottom: 1px solid var(--border-color);
            font-size: 0.8em;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        td {
            padding: 16px 24px;
            border-bottom: 1px solid var(--bg-tertiary);
            color: var(--text-primary);
            font-size: 0.95em;
        }
        
        tbody tr {
            transition: background 0.2s ease;
        }
        
        tbody tr:hover {
            background: var(--bg-secondary);
        }
        
        .status-badge {
            display: inline-flex;
            align-items: center;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.8em;
            font-weight: 600;
            letter-spacing: 0.5px;
            text-transform: uppercase;
        }
        
        .status-online {
            background: var(--status-ok-bg);
            color: var(--status-ok-text);
            border: 1px solid var(--status-ok-border);
        }
        
        .status-error {
            background: var(--status-error-bg);
            color: var(--status-error-text);
            border: 1px solid var(--status-error-border);
        }
        
        .url-cell a {
            color: var(--text-primary);
            text-decoration: none;
            transition: color 0.2s;
        }
        
        .url-cell a:hover {
            color: var(--accent-primary);
            text-decoration: underline;
        }
        
        .code-badge {
            font-weight: 600;
            padding: 4px 10px;
            border-radius: 6px;
            background: var(--bg-tertiary);
            font-size: 0.85em;
            font-family: 'SF Mono', 'Monaco', 'Courier New', monospace;
            color: var(--text-primary);
        }
        
        .code-2xx { background: var(--status-ok-bg); color: var(--status-ok-text); border: 1px solid var(--status-ok-border); }
        .code-3xx { background: var(--bg-tertiary); color: var(--text-secondary); }
        .code-4xx, .code-5xx { background: var(--status-error-bg); color: var(--status-error-text); border: 1px solid var(--status-error-border); }
        
        @media (max-width: 768px) {
            .header { padding: 40px 24px; }
            .header-content { flex-direction: column; gap: 24px; }
            .title-group h1 { font-size: 2.5em; }
            .content { padding: 32px 20px; }
            .button-group { flex-direction: column; }
            button { width: 100%; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="header-content">
                <div class="title-group">
                    <div class="logo-row">
                        <svg class="logo" viewBox="0 0 160 160" xmlns="http://www.w3.org/2000/svg">
                             <path d="M147.883728,0H12C5.3725586,0,0,5.3726196,0,12v26c0,6.6274414,5.3725586,12,12,12h53.8650513L3.5147095,112.3502808C1.0344238,114.8305664-.1195068,118.1259766.0256958,121.3742065c-.0071411.1702271-.0256958.3375244-.0256958.5095215v26c0,6.6274414,5.3725586,12,12,12h26c.1224976,0,.2412109-.0146484.362793-.0183105,3.300293.1918945,6.6642456-.9597778,9.18573-3.4812622l108.8053589-108.8053589c2.4470215-2.4470215,3.6036987-5.6875,3.4952393-8.8931885.0129395-.2282104.0346069-.4541626.0346069-.6856079V12c0-6.6273804-5.3726196-12-12-12Z" fill="currentColor"/>
                             <rect x="109.8837138" y="109.8837451" width="50" height="50" rx="12" ry="12" fill="currentColor"/>
                        </svg>
                        <h1>Zen Status</h1>
                    </div>
                    <p>Status & SEO Auditing. Reimagined for clarity and calm.</p>
                </div>
                <div class="theme-switcher">
                    <button class="theme-btn" onclick="toggleThemeMenu()">
                        <span class="color-dot" style="background: currentColor;"></span>
                        Theme
                    </button>
                    <div class="theme-menu" id="themeMenu">
                        <div class="theme-option" onclick="setTheme('default')">
                            <span class="color-dot" style="background: #0F4C81;"></span> Serenity
                        </div>
                        <div class="theme-option" onclick="setTheme('sage')">
                            <span class="color-dot" style="background: #768a73;"></span> Sage
                        </div>
                        <div class="theme-option" onclick="setTheme('rose')">
                            <span class="color-dot" style="background: #F7CAC9;"></span> Rose
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="content">
            <div class="input-section">
                <label for="urls">Target URLs</label>
                <textarea id="urls" placeholder="https://example.com&#10;http://example2.com"></textarea>
                <div class="button-group">
                    <button class="btn-primary" id="checkButton" onclick="checkWebsites()">Check Status</button>
                    <button class="btn-secondary" id="auditButton" onclick="runSeoAudit()">SEO Audit</button>
                    <button class="btn-secondary" id="cancelButton" onclick="cancelCurrentOperation()" disabled>Cancel</button>
                    <button class="btn-secondary" onclick="handleClearClick()">Clear</button>
                </div>
                <div class="sitemap-controls">
                    <label class="checkbox-label"><input type="checkbox" checked id="useSitemap"> Crawl sitemap automatically</label>
                    <div class="sitemap-fields">
                        <input type="text" id="sitemapUrl" placeholder="Optional sitemap URL">
                        <input type="number" id="maxPages" min="1" max="10000" placeholder="Max Pages (upto 10000)" title="Max pages limit">
                    </div>
                </div>
            </div>
            
            <div class="loading" id="loading">
                <div class="spinner"></div>
                <p>Finding zen... <span id="progress">0/0</span></p>
            </div>
            
            <div class="results" id="results">
                <div class="summary" id="summary"></div>
                <div class="table-container">
                    <table>
                        <thead>
                            <tr>
                                <th>#</th>
                                <th>URL</th>
                                <th>Code</th>
                                <th>Status</th>
                                <th>Time</th>
                            </tr>
                        </thead>
                        <tbody id="resultsBody"></tbody>
                    </table>
                </div>
            </div>

            <div class="results" id="seoResults">
                <div class="summary" id="seoSummary"></div>
                <div class="export-actions">
                    <button onclick="exportSeoJson()">Export JSON</button>
                    <button onclick="exportSeoCsv()">Export CSV</button>
                    <button onclick="exportSeoPerSiteCsv()">Export per-site CSV</button>
                    <button onclick="printSeoReport()">Print Report</button>
                </div>
                <div class="issues-row">
                    <div class="issues-panel" id="issuesPanel"></div>
                </div>
                <div class="report-section">
                    <div class="seo-cards" id="seoCards"></div>
                </div>
            </div>
        </div>
    </div>
    <div id="toastContainer" class="toast-container"></div>
    <div id="confirmOverlay" class="modal-overlay hidden">
        <div class="modal-box">
            <div id="confirmMessage" class="modal-message"></div>
            <div class="modal-actions">
                <button class="btn-primary" id="confirmYes">Yes</button>
                <button class="btn-secondary" id="confirmNo">No</button>
            </div>
        </div>
    </div>
    
    <script>
        // Theme colors mapping
        var themeColors = {
            'default': '#0F4C81',
            'sage': '#768a73',
            'rose': '#B76E79'
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
            const savedTheme = localStorage.getItem('zenTheme') || 'default';
            setTheme(savedTheme);
        }

        function toggleThemeMenu() {
            const menu = document.getElementById('themeMenu');
            menu.classList.toggle('active');
        }

        function setTheme(themeName) {
            document.documentElement.setAttribute('data-theme', themeName);
            localStorage.setItem('zenTheme', themeName);
            document.getElementById('themeMenu').classList.remove('active');
            updateFavicon(themeName);
        }

        // Close menu when clicking outside
        window.onclick = function(event) {
            if (!event.target.matches('.theme-btn') && !event.target.closest('.theme-btn')) {
                const menu = document.getElementById('themeMenu');
                if (menu && menu.classList.contains('active')) {
                    menu.classList.remove('active');
                }
            }
        }

        // Initialize immediately
        initTheme();

        var lastSeoResults = [];
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
            var normalized = textarea.value.replace(/\\r/g, '');
            var parts = normalized.split('\\n');
            var cleaned = [];
            for (var i = 0; i < parts.length; i++) {
                var u = parts[i].trim();
                if (u) {
                    // Add https:// if no protocol specified
                    if (!u.match(/^https?:\\/\\//i)) {
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
            document.getElementById('loading').classList.add('active');
            document.getElementById('results').classList.remove('active');
            document.getElementById('seoResults').classList.remove('active');
        }

        function hideLoading() {
            document.getElementById('loading').classList.remove('active');
        }

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

            while (true) {
                var part = await reader.read();
                if (part.done) break;
                buffer += decoder.decode(part.value, { stream: true });
                var lines = buffer.split('\\n\\n');
                buffer = lines.pop();
                for (var i = 0; i < lines.length; i++) {
                    var line = lines[i];
                    if (line.indexOf('data: ') !== 0) continue;
                    var data = JSON.parse(line.substring(6));
                    if (data.type === 'progress' && onProgress) {
                        onProgress(data);
                    } else if (data.type === 'complete' && onComplete) {
                        onComplete(data);
                    }
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
                }, function(data) {
                    displaySeoResults(data.results, data.sitemap_debug);
                }, controller);
            } catch (err) {
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
            const resultsBody = document.getElementById('resultsBody');
            const summary = document.getElementById('summary');

            const total = results.length;
            const online = results.filter(r => r.status_message === 'Online').length;
            const errors = total - online;
            const times = results.filter(r => r.response_time !== 'N/A').map(r => parseFloat(r.response_time));
            const avgTime = times.length ? (times.reduce((a, b) => a + b, 0) / times.length) : 0;

            summary.innerHTML = [
                '<div class="summary-item"><div class="number">' + total + '</div><div class="label">Total Sites</div></div>',
                '<div class="summary-item"><div class="number">' + online + '</div><div class="label">Online</div></div>',
                '<div class="summary-item"><div class="number">' + errors + '</div><div class="label">Errors</div></div>',
                '<div class="summary-item"><div class="number">' + avgTime.toFixed(2) + 's</div><div class="label">Avg Response</div></div>'
            ].join('');

            resultsBody.innerHTML = '';
            results.forEach((result, index) => {
                const row = document.createElement('tr');
                const statusClass = result.status_message === 'Online' ? 'status-online' : 'status-error';
                let codeClass = 'code-badge';
                if (typeof result.status_code === 'number') {
                    if (result.status_code >= 200 && result.status_code < 300) codeClass += ' code-2xx';
                    else if (result.status_code >= 300 && result.status_code < 400) codeClass += ' code-3xx';
                    else if (result.status_code >= 400 && result.status_code < 500) codeClass += ' code-4xx';
                    else if (result.status_code >= 500) codeClass += ' code-5xx';
                }

                const statusMessage = result.status_message;

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
            const cards = document.getElementById('seoCards');
            const summary = document.getElementById('seoSummary');
            const issuesPanel = document.getElementById('issuesPanel');
            lastSeoResults = results || [];

            // Group results by site
            const siteBuckets = {};
            lastSeoResults.forEach(function(r) {
                var parser = document.createElement('a');
                parser.href = r.url;
                var host = parser.hostname || 'unknown';
                if (!siteBuckets[host]) siteBuckets[host] = [];
                siteBuckets[host].push(r);
            });

            const siteCount = Object.keys(siteBuckets).length;
            const total = results.length;
            const okPages = results.filter(r => r.status_message === 'OK').length;
            const missingTitles = results.filter(r => !r.title).length;
            const missingDescriptions = results.filter(r => !r.meta_description).length;
            const avgWordsList = results.filter(r => typeof r.word_count === 'number' && r.word_count > 0).map(r => r.word_count);
            const avgWords = avgWordsList.length ? avgWordsList.reduce((a, b) => a + b, 0) / avgWordsList.length : 0;
            const avgRespList = results.filter(r => r.response_time !== 'N/A').map(r => parseFloat(r.response_time));
            const avgResponse = avgRespList.length ? avgRespList.reduce((a, b) => a + b, 0) / avgRespList.length : 0;

            const warningCounts = {};
            results.forEach(function(r) {
                (r.warnings || []).forEach(function(w) {
                    warningCounts[w] = (warningCounts[w] || 0) + 1;
                });
            });
            const topWarnings = Object.keys(warningCounts)
                .sort(function(a, b) { return warningCounts[b] - warningCounts[a]; })
                .slice(0, 6)
                .map(function(w) { return { text: w, count: warningCounts[w] }; });

            summary.innerHTML = [
                '<div class="summary-item"><div class="number">' + siteCount + '</div><div class="label">Sites Audited</div></div>',
                '<div class="summary-item"><div class="number">' + total + '</div><div class="label">Pages Audited</div></div>',
                '<div class="summary-item"><div class="number">' + okPages + '</div><div class="label">OK Status</div></div>',
                '<div class="summary-item"><div class="number">' + missingTitles + '</div><div class="label">Missing Title</div></div>',
                '<div class="summary-item"><div class="number">' + missingDescriptions + '</div><div class="label">Missing Desc</div></div>',
                '<div class="summary-item"><div class="number">' + avgResponse.toFixed(2) + 's</div><div class="label">Avg Response</div></div>'
            ].join('');

            cards.innerHTML = '';
            
            // Render grouped by site
            var globalIndex = 0;
            Object.keys(siteBuckets).sort().forEach(function(host) {
                var siteResults = siteBuckets[host];
                var siteOk = siteResults.filter(r => r.status_message === 'OK').length;
                var siteWarnings = siteResults.filter(r => (r.warnings || []).length > 0).length;
                
                var siteGroup = document.createElement('div');
                siteGroup.className = 'site-group';
                
                var headerHtml = '<div class="site-group-header">' +
                    '<h2>' + host + '</h2>' +
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
                    var isError = (typeof result.status_code === 'number' && result.status_code >= 400) || result.status_message !== 'OK';
                    var statusClass = isError ? 'status-danger' : (hasWarnings ? 'status-warn' : 'status-ok');
                    var isDuplicate = result.duplicate_of && result.duplicate_of !== result.url;

                    var codeClass = 'pill';
                    if (typeof result.status_code === 'number') {
                        if (result.status_code >= 200 && result.status_code < 300) codeClass += ' status-ok';
                        else if (result.status_code >= 300 && result.status_code < 400) codeClass += '';
                        else if (result.status_code >= 400) codeClass += ' status-danger';
                    }

                    var warningsText = (result.warnings || []).join('; ');
                    var warningsClass = isError ? 'warnings danger' : (hasWarnings ? 'warnings warn' : 'warnings ok');
                    var titleText = result.title || 'No title';
                    var metaText = result.meta_description || 'No description';
                    var h1Sample = (result.h1_samples || []).slice(0, 2).join(' | ') || 'No H1';
                    
                    var duplicateBadge = '';
                    if (isDuplicate) {
                        duplicateBadge = '<div class="pill status-warn" title="Duplicate of: ' + result.duplicate_of + '" style="cursor: help;">⚠ Duplicate</div>';
                    }

                    var card = document.createElement('div');
                    card.className = 'seo-card';
                    card.innerHTML = [
                        '<div class="card-header">',
                        '  <div class="card-header-left">',
                        '    <div class="pill pill-number">#' + globalIndex + '</div>',
                        '    <div class="' + codeClass + '">' + result.status_code + '</div>',
                        '    <div class="pill">' + result.response_time + '</div>',
                        (isDuplicate ? '    ' + duplicateBadge : ''),
                        '  </div>',
                        '  <div class="card-header-right">',
                        '    <div class="pill ' + statusClass + '">' + result.status_message + '</div>',
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

            if (issuesPanel) {
                if (topWarnings.length === 0) {
                    issuesPanel.innerHTML = '<h3>Top Issues</h3><p>No major issues detected.</p>';
                } else {
                    issuesPanel.innerHTML = '<h3>Top Issues to Improve</h3><ul>' +
                        topWarnings.map(function(t) { return '<li>' + t.text + ' (' + t.count + ')</li>'; }).join('') +
                        '</ul>';
                }
            }

            document.getElementById('seoResults').classList.add('active');
        }

        function printSeoReport() {
            window.print();
        }

        function exportSeoJson() {
            if (!lastSeoResults.length) {
                showToast('Run an SEO audit first.', 'error');
                return;
            }
            const blob = new Blob([JSON.stringify(lastSeoResults, null, 2)], { type: 'application/json' });
            const link = document.createElement('a');
            link.href = URL.createObjectURL(blob);
            link.download = 'seo-audit.json';
            link.click();
            URL.revokeObjectURL(link.href);
        }

        function exportSeoCsv() {
            if (!lastSeoResults.length) {
                showToast('Run an SEO audit first.', 'error');
                return;
            }

            const headers = [
                'url','status_code','status_message','response_time','title_length','meta_description_length',
                'h1_count','word_count','internal_links','external_links','images_missing_alt','total_images',
                'robots','canonical','warnings','title','meta_description','h1_samples','current_title','current_meta_description'
            ];

            const escapeCsv = function(val) {
                const v = (val === null || val === undefined ? '' : val).toString();
                if (v.indexOf('"') !== -1 || v.indexOf(',') !== -1 || v.indexOf('\\n') !== -1) {
                    return '"' + v.replace(/"/g, '""') + '"';
                }
                return v;
            };

            const rows = lastSeoResults.map(function(r) {
                return [
                    r.url,
                    r.status_code,
                    r.status_message,
                    r.response_time,
                    r.title_length,
                    r.meta_description_length,
                    r.h1_count,
                    r.word_count,
                    r.internal_links,
                    r.external_links,
                    r.images_missing_alt,
                    r.total_images,
                    r.robots,
                    r.canonical,
                    (r.warnings || []).join(' | '),
                    r.title,
                    r.meta_description,
                    (r.h1_samples || []).join(' | '),
                    r.title,
                    r.meta_description
                ].map(escapeCsv).join(',');
            });

            const csv = headers.join(',') + '\\n' + rows.join('\\n');
            const blob = new Blob([csv], { type: 'text/csv' });
            const link = document.createElement('a');
            link.href = URL.createObjectURL(blob);
            link.download = 'seo-audit.csv';
            link.click();
            URL.revokeObjectURL(link.href);
        }

        function exportSeoPerSiteCsv() {
            if (!lastSeoResults.length) {
                showToast('Run an SEO audit first.', 'error');
                return;
            }
            
            var escapeCsv = function(val) {
                var v = (val === null || val === undefined ? '' : val).toString();
                if (v.indexOf('"') !== -1 || v.indexOf(',') !== -1 || v.indexOf('\\n') !== -1 || v.indexOf('\\r') !== -1) {
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
                    return [
                        r.url,
                        r.status_code,
                        r.status_message,
                        r.response_time,
                        r.title_length,
                        r.meta_description_length,
                        r.h1_count,
                        r.word_count,
                        r.internal_links,
                        r.external_links,
                        r.images_missing_alt,
                        r.total_images,
                        r.robots,
                        r.canonical,
                        (r.warnings || []).join(' | '),
                        r.title,
                        r.meta_description,
                        (r.h1_samples || []).join(' | ')
                    ].map(escapeCsv).join(',');
                });

                var headers = [
                    'url','status_code','status_message','response_time','title_length','meta_description_length',
                    'h1_count','word_count','internal_links','external_links','images_missing_alt','total_images',
                    'robots','canonical','warnings','title','meta_description','h1_samples'
                ];

                var csv = headers.join(',') + '\\r\\n' + rows.join('\\r\\n');
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
        
        function clearAll() {
            document.getElementById('urls').value = '';
            document.getElementById('results').classList.remove('active');
            document.getElementById('seoResults').classList.remove('active');
        }
    </script>
</body>
</html>
'''

def check_website_status(url, timeout=10):
    """Check the status of a website and verify it's actually working (not showing WordPress DB errors)."""
    try:
        start_time = datetime.now()
        response = requests.get(url, timeout=timeout, allow_redirects=True)
        end_time = datetime.now()
        response_time = (end_time - start_time).total_seconds()
        
        # Check for WordPress database connection error
        response_text = response.text.lower()
        if 'error establishing a database connection' in response_text:
            return {
                'url': url,
                'status_code': response.status_code,
                'status_message': 'DB Connection Error',
                'response_time': f"{response_time:.2f}s"
            }
        
        # Check for other common WordPress/site errors
        if 'fatal error' in response_text or 'database error' in response_text:
            return {
                'url': url,
                'status_code': response.status_code,
                'status_message': 'Site Error',
                'response_time': f"{response_time:.2f}s"
            }
        
        return {
            'url': url,
            'status_code': response.status_code,
            'status_message': 'Online' if response.status_code < 400 else 'Error',
            'response_time': f"{response_time:.2f}s"
        }
    except requests.exceptions.Timeout:
        return {
            'url': url,
            'status_code': 'N/A',
            'status_message': 'Timeout',
            'response_time': 'N/A'
        }
    except requests.exceptions.ConnectionError:
        return {
            'url': url,
            'status_code': 'N/A',
            'status_message': 'Connection Error',
            'response_time': 'N/A'
        }
    except Exception as e:
        return {
            'url': url,
            'status_code': 'N/A',
            'status_message': f'Error',
            'response_time': 'N/A'
        }


def audit_website(url, timeout=15, max_retries=2):
    """Perform a lightweight SEO audit for a single URL with simple retry/backoff."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    try:
        attempt = 0
        while True:
            try:
                start_time = datetime.now()
                response = requests.get(url, timeout=timeout, allow_redirects=True, headers=headers)
                response_time = (datetime.now() - start_time).total_seconds()
                break
            except (requests.exceptions.Timeout, requests.exceptions.ConnectionError):
                attempt += 1
                if attempt >= max_retries:
                    raise
                time.sleep(1.0 * attempt)

        soup = BeautifulSoup(response.text, 'html.parser')

        title = soup.title.string.strip() if soup.title and soup.title.string else ''
        meta_desc_tag = soup.find('meta', attrs={'name': 'description'})
        meta_description = meta_desc_tag.get('content', '').strip() if meta_desc_tag else ''
        canonical_tag = soup.find('link', rel=lambda rel: rel and 'canonical' in rel.lower())
        canonical = canonical_tag.get('href') if canonical_tag else ''
        robots_tag = soup.find('meta', attrs={'name': 'robots'})
        robots = robots_tag.get('content', '').lower().strip() if robots_tag and robots_tag.get('content') else ''
        h1_tags = [h.get_text(strip=True) for h in soup.find_all('h1')]
        word_count = len(re.findall(r'\w+', soup.get_text(' ')))

        images = soup.find_all('img')
        total_images = len(images)
        images_missing_alt = sum(1 for img in images if not (img.get('alt') and img.get('alt').strip()))

        parsed_base = urlparse(response.url)
        links = [a.get('href') for a in soup.find_all('a', href=True)]
        internal_links = 0
        external_links = 0
        for href in links:
            parsed_href = urlparse(href)
            if not parsed_href.netloc or parsed_href.netloc == parsed_base.netloc:
                internal_links += 1
            else:
                external_links += 1

        warnings = []
        if not title:
            warnings.append('Missing title')
        elif len(title) > 60:
            warnings.append('Title too long')

        if not meta_description:
            warnings.append('Missing meta description')
        elif len(meta_description) > 160:
            warnings.append('Description too long')

        if len(h1_tags) == 0:
            warnings.append('Missing H1')
        elif len(h1_tags) > 1:
            warnings.append('Multiple H1 tags')

        if not canonical:
            warnings.append('No canonical tag')
        if 'noindex' in robots:
            warnings.append('Noindex set')
        if images_missing_alt > 0:
            warnings.append('Images missing alt text')
        if word_count < 200:
            warnings.append('Thin content')

        return {
            'url': url,
            'status_code': response.status_code,
            'status_message': 'OK' if response.status_code < 400 else 'Page Error',
            'response_time': f"{response_time:.2f}s",
            'title': title,
            'title_length': len(title),
            'meta_description': meta_description,
            'meta_description_length': len(meta_description),
            'h1_count': len(h1_tags),
            'h1_samples': h1_tags[:3],
            'canonical': canonical,
            'robots': robots,
            'word_count': word_count,
            'internal_links': internal_links,
            'external_links': external_links,
            'images_missing_alt': images_missing_alt,
            'total_images': total_images,
            'warnings': warnings
        }
    except requests.exceptions.Timeout:
        return {
            'url': url,
            'status_code': 'N/A',
            'status_message': 'Timeout',
            'response_time': 'N/A',
            'title': '',
            'title_length': 0,
            'meta_description': '',
            'meta_description_length': 0,
            'h1_count': 0,
            'h1_samples': [],
            'canonical': '',
            'robots': '',
            'word_count': 0,
            'internal_links': 0,
            'external_links': 0,
            'images_missing_alt': 0,
            'total_images': 0,
            'warnings': ['Timeout']
        }
    except requests.exceptions.ConnectionError:
        return {
            'url': url,
            'status_code': 'N/A',
            'status_message': 'Connection Error',
            'response_time': 'N/A',
            'title': '',
            'title_length': 0,
            'meta_description': '',
            'meta_description_length': 0,
            'h1_count': 0,
            'h1_samples': [],
            'canonical': '',
            'robots': '',
            'word_count': 0,
            'internal_links': 0,
            'external_links': 0,
            'images_missing_alt': 0,
            'total_images': 0,
            'warnings': ['Connection error']
        }
    except Exception:
        return {
            'url': url,
            'status_code': 'N/A',
            'status_message': 'Error',
            'response_time': 'N/A',
            'title': '',
            'title_length': 0,
            'meta_description': '',
            'meta_description_length': 0,
            'h1_count': 0,
            'h1_samples': [],
            'canonical': '',
            'robots': '',
            'word_count': 0,
            'internal_links': 0,
            'external_links': 0,
            'images_missing_alt': 0,
            'total_images': 0,
            'warnings': ['Unexpected error']
        }


def _extract_urlset_urls(root, remaining):
    urls = []
    # Generic iteration to handle namespaces effectively
    for child in root:
        if child.tag.endswith('url'):
            loc = None
            for sub in child:
                if sub.tag.endswith('loc'):
                    loc = sub
                    break
            
            if loc is None or not loc.text:
                continue
                
            text = loc.text.strip()
            if not text.startswith(('http://', 'https://')):
                continue
            urls.append(text)
            if len(urls) >= remaining:
                break
    return urls


def fetch_sitemap_urls(sitemap_url, max_urls=250, max_depth=15, debug=False):
    """Fetch URLs from a sitemap or sitemap index (supports .xml and .xml.gz).

    If debug=True, returns a tuple (urls, debug_info) where debug_info lists each
    sitemap fetched with status and counts.
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    collected = []
    collected_set = set()
    collected_norm_set = set()
    first_seen_norm = {}
    duplicates = []
    seen_sitemaps = set()
    queue = [(sitemap_url, 0)]
    debug_info = []
    skipped_samples = []

    def normalize_url(u):
        """Normalize URL for dedupe (scheme/netloc lower, strip default ports, trim trailing slash)."""
        try:
            parsed = urlparse(u.strip())
            if parsed.scheme not in ('http', 'https'):
                return None
            netloc = parsed.netloc.lower()
            if parsed.scheme == 'http' and netloc.endswith(':80'):
                netloc = netloc[:-3]
            if parsed.scheme == 'https' and netloc.endswith(':443'):
                netloc = netloc[:-4]
            path = parsed.path or '/'
            if len(path) > 1 and path.endswith('/'):
                path = path[:-1]
            normalized = f"{parsed.scheme}://{netloc}{path}"
            if parsed.query:
                normalized += f"?{parsed.query}"
            return normalized
        except Exception:
            return None

    def record_skip(url, source, reason):
        if len(skipped_samples) < 50:
            skipped_samples.append({'url': url, 'source': source, 'reason': reason})

    def add_urls(url_list, source):
        """Add URLs to collection (no dedupe) and return count of items appended."""
        nonlocal collected
        added = 0
        for u in url_list:
            norm = normalize_url(u)
            if not norm:
                record_skip(u, source, 'normalize-failed')
            else:
                if norm in first_seen_norm:
                    duplicates.append({'url': u, 'duplicate_of': first_seen_norm[norm], 'source': source})
                else:
                    first_seen_norm[norm] = u
            collected.append(u)
            collected_set.add(u)
            if norm:
                collected_norm_set.add(norm)
            added += 1
            if len(collected) >= max_urls:
                break
        return added

    while queue and len(collected) < max_urls:
        current_url, depth = queue.pop(0)
        if current_url in seen_sitemaps or depth > max_depth:
            continue
        seen_sitemaps.add(current_url)

        try:
            resp = requests.get(current_url, timeout=15, headers=headers)
        except (requests.exceptions.RequestException, ValueError) as e:
            debug_info.append({
                'url': current_url,
                'depth': depth,
                'status': 'Connection Error',
                'parsed': False,
                'type': 'error',
                'found': 0
                })
            continue
            
        status = resp.status_code
        if status >= 400:
            debug_info.append({
                'url': current_url,
                'depth': depth,
                'status': status,
                'parsed': False,
                'type': 'error',
                'found': 0
                })
            continue

        content_type = resp.headers.get('Content-Type', '').lower()
        content_encoding = resp.headers.get('Content-Encoding', '').lower()
        is_gzip_hint = current_url.lower().endswith('.gz') or 'gzip' in content_type

        raw_xml = resp.content if resp.content else resp.text

        root = None
        parsed_ok = False
        parsed_type = 'unknown'
        found_count = 0
        added_now = 0

        # Try parsing XML directly first
        try:
            root = ET.fromstring(raw_xml)
            parsed_ok = True
        except Exception as e:
            # Try gzip decompression if URL suggests it
            if is_gzip_hint and 'gzip' not in content_encoding:
                try:
                    decompressed = gzip.decompress(resp.content)
                    root = ET.fromstring(decompressed)
                    parsed_ok = True
                except Exception:
                    root = None

        # If parsing failed, log and continue to next sitemap
        if not parsed_ok or root is None:
            debug_info.append({
                'url': current_url,
                'depth': depth,
                'status': status,
                'parsed': False,
                'type': 'unparsed',
                'found': 0
            })
            continue

        # Process the parsed XML
        try:
            if root.tag.endswith('sitemapindex'):
                parsed_type = 'sitemapindex'
                child_sitemaps_added = 0
                if depth < max_depth:
                    # Generic iteration for sitemapindex
                    for child in root:
                        if child.tag.endswith('sitemap'):
                            loc = None
                            for sub in child:
                                if sub.tag.endswith('loc'):
                                    loc = sub
                                    break
                            if loc is not None and loc.text:
                                child_url = loc.text.strip()
                                if child_url and child_url not in seen_sitemaps and len(collected) < max_urls:
                                    queue.append((child_url, depth + 1))
                                    child_sitemaps_added += 1
                found_count = child_sitemaps_added
            elif root.tag.endswith('urlset'):
                parsed_type = 'urlset'
                new_urls = _extract_urlset_urls(root, max_urls - len(collected))
                added_now = add_urls(new_urls, current_url)
                found_count = len(new_urls)

            debug_info.append({
                'url': current_url,
                'depth': depth,
                'status': status,
                'parsed': True,
                'type': parsed_type,
                'found': found_count,
                'added': added_now
            })

        except Exception:
            continue

    result_urls = collected[:max_urls]
    if debug:
        return result_urls, {
            'sitemaps': debug_info,
            'skipped_samples': skipped_samples,
            'duplicates': duplicates
        }
    return result_urls

@app.route('/')
def index():
    """Serve the main page."""
    return render_template_string(HTML_TEMPLATE)

@app.route('/check', methods=['POST'])
def check_websites():
    """Check the status of submitted URLs with progress updates."""
    data = request.get_json()
    urls = data.get('urls', [])
    
    if not urls:
        return jsonify({'error': 'No URLs provided'}), 400
    
    def generate():
        results = []
        completed = 0
        total = len(urls)
        
        # Use ThreadPoolExecutor for concurrent requests
        with ThreadPoolExecutor(max_workers=10) as executor:
            future_to_url = {executor.submit(check_website_status, url): url for url in urls}
            
            for future in as_completed(future_to_url):
                result = future.result()
                results.append(result)
                completed += 1
                
                # Send progress update
                progress_data = {
                    'type': 'progress',
                    'completed': completed,
                    'total': total
                }
                yield f"data: {json.dumps(progress_data)}\n\n"
        
        # Sort results: errors first, then by status code
        sorted_results = sorted(results, key=lambda x: (
            0 if x['status_message'] not in ['Online'] else 1,
            x['status_code'] if isinstance(x['status_code'], int) else 999
        ))
        
        # Send final results
        final_data = {
            'type': 'complete',
            'results': sorted_results
        }
        yield f"data: {json.dumps(final_data)}\n\n"
    
    return Response(generate(), mimetype='text/event-stream')


@app.route('/seo-audit', methods=['POST'])
def seo_audit():
    """Run a lightweight SEO audit for the submitted URLs with progress updates."""
    data = request.get_json()
    urls = data.get('urls', [])
    use_sitemap = bool(data.get('use_sitemap'))
    sitemap_url = (data.get('sitemap_url') or '').strip()
    max_pages = data.get('max_pages') or 100
    try:
        max_pages = max(1, min(int(max_pages), 10000))
    except Exception:
        max_pages = 100

    sitemap_debug = []
    dup_map = {}
    original_urls = list(urls)  # Keep original URLs for merging
    
    if use_sitemap:
        if not urls:
            return jsonify({'error': 'Provide at least one URL to infer sitemap'}), 400
        
        # Collect sitemap URLs from all input URLs
        all_crawled_urls = []
        seen_crawled = set()
        
        for base_input_url in original_urls:
            base_url = base_input_url.rstrip('/')
            target_sitemap = sitemap_url or f"{base_url}/sitemap.xml"
            sitemap_found_urls = False
            
            try:
                crawled_urls, site_debug = fetch_sitemap_urls(target_sitemap, max_pages, debug=True)
                if isinstance(site_debug, dict):
                    for d in site_debug.get('duplicates', []) or []:
                        src = d.get('url')
                        tgt = d.get('duplicate_of')
                        if src and tgt:
                            dup_map[src] = tgt
                    # Merge debug info
                    if 'sitemaps' in site_debug:
                        sitemap_debug.extend(site_debug['sitemaps'])
                
                # Add all crawled URLs (including duplicates)
                if crawled_urls:
                    sitemap_found_urls = True
                    for u in crawled_urls:
                        all_crawled_urls.append(u)
                        # Track if this URL was already seen (mark as duplicate)
                        if u in seen_crawled:
                            # Find the first occurrence to mark as duplicate_of
                            if u not in dup_map:
                                dup_map[u] = u  # Self-reference indicates exact duplicate in list
                        else:
                            seen_crawled.add(u)
                        
            except Exception as e:
                debug_entry = {
                    'type': 'error',
                    'status': 'Error',
                    'url': target_sitemap,
                    'note': f"Sitemap fetch failed: {str(e)}. Adding {base_input_url} to audit."
                }
                sitemap_debug.append(debug_entry)
            
            # If no URLs found from sitemap, add the original input URL to audit
            if not sitemap_found_urls:
                if base_input_url not in seen_crawled:
                    all_crawled_urls.append(base_input_url)
                    seen_crawled.add(base_input_url)
        
        # Use crawled URLs if found, otherwise fall back to original URLs
        if all_crawled_urls:
            urls = all_crawled_urls
        else:
            debug_entry = {
                'type': 'warning',
                'status': 'Empty',
                'url': 'All sitemaps',
                'note': 'No URLs found in sitemaps. Auditing entered URLs only.'
            }
            sitemap_debug.append(debug_entry)
            
    elif not urls:
        return jsonify({'error': 'No URLs provided'}), 400
    dup_map = dup_map if use_sitemap else {}

    def generate():
        results = []
        completed = 0
        total = len(urls)
        last_update = time.time()

        # Send initial keep-alive
        yield ": keep-alive\n\n"

        batch_size = 300
        start_index = 0
        while start_index < total:
            batch = urls[start_index:start_index + batch_size]
            pool_size = min(8, max(2, len(batch)))
            with ThreadPoolExecutor(max_workers=pool_size) as executor:
                future_to_url = {executor.submit(audit_website, url): url for url in batch}

                for future in as_completed(future_to_url):
                    # Send keep-alive every 10 seconds to prevent timeout
                    if time.time() - last_update > 10:
                        yield ": keep-alive\n\n"
                        last_update = time.time()
                    
                    result = future.result()
                    if dup_map:
                        result['duplicate_of'] = dup_map.get(result.get('url'))
                    results.append(result)
                    completed += 1

                    progress_data = {
                        'type': 'progress',
                        'completed': completed,
                        'total': total
                    }
                    yield f"data: {json.dumps(progress_data)}\n\n"
                    last_update = time.time()
            start_index += batch_size

        sorted_results = sorted(results, key=lambda x: (
            0 if x.get('status_message') == 'OK' else 1,
            x.get('status_code') if isinstance(x.get('status_code'), int) else 999
        ))

        final_data = {
            'type': 'complete',
            'results': sorted_results,
            'sitemap_debug': sitemap_debug
        }
        yield f"data: {json.dumps(final_data)}\n\n"

    return Response(generate(), mimetype='text/event-stream')

if __name__ == '__main__':
    import sys
    
    # Check if running in production mode
    production = '--production' in sys.argv
    
    if production:
        # Production settings
        print("\n" + "="*60)
        print("🌐 Website Status Checker - Production Mode")
        print("="*60)
        print("\n✓ Running on http://127.0.0.1:5001")
        print("✓ Access via: https://vault.quickworx.io/webchecker")
        print("\n⏹  Press CTRL+C to stop the server\n")
        print("="*60 + "\n")
        app.run(debug=False, host='127.0.0.1', port=5001, threaded=True)
    else:
        # Development settings
        print("\n" + "="*60)
        print("🌐 Website Status Checker Server Starting...")
        print("="*60)
        print("\n📍 Open your browser and go to: http://127.0.0.1:5000")
        print("\n💡 Paste your URLs in the text area and click 'Check Status'")
        print("\n⏹  Press CTRL+C to stop the server\n")
        print("="*60 + "\n")
        app.run(debug=True, host='0.0.0.0', port=5000)