# -*- coding: utf-8 -*-
"""
ui_html.py - REMEMBER UI Templates and Global CSS
-------------------------------------------------
Stores all HTML templates and modern CSS design system for the REMEMBER application.
"""

CSS = '''/* ==========================================================
   REMEMBER Design System - Modern Dark Slate & Glass Theme
   ========================================================== */

:root {
    --bg-main: #0b0f19;
    --bg-surface: #111827;
    --bg-card: #1e293b;
    --bg-card-hover: #243248;
    --bg-input: #0f172a;
    --bg-glass: rgba(15, 23, 42, 0.85);

    --border-subtle: rgba(255, 255, 255, 0.08);
    --border-medium: #334155;
    --border-focus: #6366f1;

    --text-primary: #f8fafc;
    --text-secondary: #94a3b8;
    --text-muted: #64748b;
    --text-accent: #38bdf8;

    --primary: #6366f1;
    --primary-hover: #4f46e5;
    --primary-gradient: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
    
    --success: #10b981;
    --success-bg: rgba(16, 185, 129, 0.15);
    --warning: #f59e0b;
    --warning-bg: rgba(245, 158, 11, 0.15);
    --danger: #ef4444;
    --danger-bg: rgba(239, 68, 68, 0.15);
    --info: #38bdf8;
    --info-bg: rgba(56, 189, 248, 0.15);

    --radius-sm: 6px;
    --radius-md: 10px;
    --radius-lg: 16px;
    --radius-full: 9999px;

    --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.3);
    --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.4), 0 2px 4px -1px rgba(0, 0, 0, 0.3);
    --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.5), 0 4px 6px -2px rgba(0, 0, 0, 0.4);
    --shadow-glow: 0 0 20px rgba(99, 102, 241, 0.25);

    --transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

/* Reset & Base */
*, *::before, *::after {
    box-sizing: border-box;
    margin: 0;
    padding: 0;
}

html {
    width: 100%;
    min-height: 100%;
    background-color: var(--bg-main);
    color-scheme: dark;
    scroll-behavior: smooth;
}

body {
    background-color: var(--bg-main);
    color: var(--text-primary);
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    font-size: 15px;
    line-height: 1.6;
    min-height: 100vh;
    display: flex;
    flex-direction: column;
    padding: 0;
    margin: 0;
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
}

/* Custom Scrollbar */
::-webkit-scrollbar {
    width: 10px;
    height: 10px;
}
::-webkit-scrollbar-track {
    background: var(--bg-main);
}
::-webkit-scrollbar-thumb {
    background: #334155;
    border-radius: var(--radius-full);
}
::-webkit-scrollbar-thumb:hover {
    background: #475569;
}

/* Typography */
h1, h2, h3, h4, h5, h6 {
    color: var(--text-primary);
    font-weight: 700;
    line-height: 1.25;
    margin-bottom: 0.75rem;
}

h1 { font-size: 1.85rem; letter-spacing: -0.025em; }
h2 { font-size: 1.45rem; letter-spacing: -0.02em; }
h3 { font-size: 1.2rem; }
h4 { font-size: 1.05rem; }

p {
    color: var(--text-secondary);
    font-size: 0.95rem;
    line-height: 1.65;
    margin-bottom: 1rem;
}

a {
    color: var(--primary);
    text-decoration: none;
    transition: var(--transition);
}
a:hover {
    color: #818cf8;
}

/* Layout Containers */
.container {
    width: 100%;
    max-width: 1200px;
    margin: 0 auto;
    padding: 24px 20px 60px 20px;
    flex: 1;
}

.container-sm {
    max-width: 800px;
}

.container-wide {
    max-width: 1400px;
}

/* Sticky Glass Navbar */
.sticky-header, header.sticky {
    position: -webkit-sticky;
    position: sticky;
    top: 0;
    z-index: 1000;
    background: var(--bg-glass);
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);
    border-bottom: 1px solid var(--border-subtle);
    padding: 12px 24px;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4);
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    width: 100%;
    margin: 0;
}

.brand-wrapper {
    display: flex;
    align-items: center;
    gap: 10px;
    text-decoration: none;
}

.brand-icon {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 36px;
    height: 36px;
    background: var(--primary-gradient);
    border-radius: var(--radius-md);
    font-size: 1.1rem;
    box-shadow: var(--shadow-glow);
}

.brand-title {
    font-size: 1.25rem;
    font-weight: 800;
    letter-spacing: -0.03em;
    background: linear-gradient(135deg, #ffffff 0%, #cbd5e1 50%, #818cf8 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

.nav-links {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 6px;
    list-style: none;
    margin: 0;
    padding: 0;
}

.nav-link, .refresh-button2, .refresh-button {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 6px 12px;
    font-size: 0.85rem;
    font-weight: 500;
    color: var(--text-secondary);
    background: rgba(255, 255, 255, 0.04);
    border: 1px solid var(--border-subtle);
    border-radius: var(--radius-full);
    text-decoration: none;
    transition: var(--transition);
    cursor: pointer;
    white-space: nowrap;
}

.nav-link:hover, .refresh-button2:hover, .refresh-button:hover {
    color: #ffffff;
    background: rgba(99, 102, 241, 0.15);
    border-color: rgba(99, 102, 241, 0.4);
    transform: translateY(-1px);
}

.nav-link.active {
    color: #ffffff;
    background: var(--primary-gradient);
    border-color: transparent;
    box-shadow: 0 2px 8px rgba(99, 102, 241, 0.4);
}

.nav-search {
    display: flex;
    align-items: center;
    gap: 6px;
    background: var(--bg-input);
    border: 1px solid var(--border-medium);
    border-radius: var(--radius-full);
    padding: 2px 4px 2px 10px;
    transition: var(--transition);
}

.nav-search:focus-within {
    border-color: var(--primary);
    box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.25);
}

.nav-search input {
    background: transparent;
    border: none;
    outline: none;
    color: var(--text-primary);
    font-size: 0.85rem;
    width: 110px;
    padding: 4px 2px;
    transition: var(--transition);
}

.nav-search input:focus {
    width: 140px;
}

.nav-search button {
    background: var(--primary);
    color: #ffffff;
    border: none;
    border-radius: var(--radius-full);
    font-size: 0.75rem;
    font-weight: 600;
    padding: 4px 10px;
    cursor: pointer;
    transition: var(--transition);
    margin: 0;
}

.nav-search button:hover {
    background: var(--primary-hover);
}

/* Cards & Surfaces */
.card {
    background: var(--bg-card);
    border: 1px solid var(--border-subtle);
    border-radius: var(--radius-lg);
    padding: 24px;
    box-shadow: var(--shadow-md);
    transition: var(--transition);
    margin-bottom: 20px;
}

.card:hover {
    border-color: rgba(99, 102, 241, 0.25);
}

.card-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 16px;
    padding-bottom: 12px;
    border-bottom: 1px solid var(--border-subtle);
}

.card-title {
    font-size: 1.25rem;
    font-weight: 700;
    color: var(--text-primary);
    margin: 0;
    display: flex;
    align-items: center;
    gap: 8px;
}

/* Badges & Chips */
.badge {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    font-size: 0.75rem;
    font-weight: 600;
    padding: 3px 8px;
    border-radius: var(--radius-full);
    background: rgba(255, 255, 255, 0.08);
    color: var(--text-secondary);
    border: 1px solid var(--border-subtle);
}

.badge-primary {
    background: rgba(99, 102, 241, 0.15);
    color: #a5b4fc;
    border-color: rgba(99, 102, 241, 0.3);
}

.badge-success {
    background: var(--success-bg);
    color: #6ee7b7;
    border-color: rgba(16, 185, 129, 0.3);
}

.badge-warning {
    background: var(--warning-bg);
    color: #fcd34d;
    border-color: rgba(245, 158, 11, 0.3);
}

.badge-danger {
    background: var(--danger-bg);
    color: #fca5a5;
    border-color: rgba(239, 68, 68, 0.3);
}

.badge-info {
    background: var(--info-bg);
    color: #7dd3fc;
    border-color: rgba(56, 189, 248, 0.3);
}

/* Flash Messages / Alerts */
.alert-container {
    margin-bottom: 20px;
}

.alert {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 12px 16px;
    border-radius: var(--radius-md);
    margin-bottom: 10px;
    font-size: 0.9rem;
    font-weight: 500;
    animation: fadeIn 0.3s ease;
}

.alert-success {
    background: var(--success-bg);
    color: #6ee7b7;
    border: 1px solid rgba(16, 185, 129, 0.4);
}

.alert-danger, .alert-error {
    background: var(--danger-bg);
    color: #fca5a5;
    border: 1px solid rgba(239, 68, 68, 0.4);
}

.alert-warning {
    background: var(--warning-bg);
    color: #fcd34d;
    border: 1px solid rgba(245, 158, 11, 0.4);
}

.alert-info {
    background: var(--info-bg);
    color: #7dd3fc;
    border: 1px solid rgba(56, 189, 248, 0.4);
}

/* Forms & Inputs */
.form-group {
    margin-bottom: 18px;
}

.form-label, label {
    display: block;
    font-size: 0.85rem;
    font-weight: 600;
    color: var(--text-secondary);
    margin-bottom: 6px;
    letter-spacing: 0.01em;
}

.form-control, input[type="text"], input[type="search"], input[type="password"], textarea, select {
    width: 100%;
    background-color: var(--bg-input);
    color: var(--text-primary);
    border: 1px solid var(--border-medium);
    border-radius: var(--radius-md);
    padding: 10px 14px;
    font-size: 0.95rem;
    font-family: inherit;
    transition: var(--transition);
    outline: none;
    box-sizing: border-box;
}

.form-control:focus, input[type="text"]:focus, textarea:focus {
    border-color: var(--border-focus);
    box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.25);
    background-color: #0d1322;
}

textarea {
    min-height: 160px;
    resize: vertical;
    line-height: 1.6;
}

.code-textarea {
    font-family: ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, "Liberation Mono", monospace;
    font-size: 14px;
    line-height: 1.5;
    background-color: #070a12;
    color: #38bdf8;
    tab-size: 4;
    white-space: pre;
    overflow-wrap: normal;
    overflow-x: auto;
}

/* File Upload Controls */
.file-upload-box {
    border: 2px dashed var(--border-medium);
    border-radius: var(--radius-md);
    padding: 16px;
    text-align: center;
    background: rgba(255, 255, 255, 0.02);
    transition: var(--transition);
    cursor: pointer;
}

.file-upload-box:hover {
    border-color: var(--primary);
    background: rgba(99, 102, 241, 0.05);
}

input[type="file"] {
    background-color: var(--bg-input);
    color: var(--text-secondary);
    border: 1px solid var(--border-medium);
    border-radius: var(--radius-md);
    padding: 8px 12px;
    font-size: 0.85rem;
    width: 100%;
    cursor: pointer;
}

input[type="file"]::file-selector-button {
    background: var(--bg-card);
    color: var(--text-primary);
    border: 1px solid var(--border-medium);
    border-radius: var(--radius-sm);
    padding: 4px 10px;
    margin-right: 12px;
    font-size: 0.85rem;
    font-weight: 500;
    cursor: pointer;
    transition: var(--transition);
}

input[type="file"]::file-selector-button:hover {
    background: var(--primary);
    color: #ffffff;
    border-color: var(--primary);
}

/* Buttons */
button, .btn, input[type="submit"] {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
    font-family: inherit;
    font-size: 0.9rem;
    font-weight: 600;
    padding: 9px 18px;
    border-radius: var(--radius-md);
    border: 1px solid transparent;
    cursor: pointer;
    transition: var(--transition);
    text-decoration: none;
    line-height: 1.4;
    white-space: nowrap;
}

.btn-primary, input[type="submit"] {
    background: var(--primary-gradient);
    color: #ffffff;
    box-shadow: 0 2px 10px rgba(99, 102, 241, 0.35);
}
.btn-primary:hover, input[type="submit"]:hover {
    box-shadow: 0 4px 15px rgba(99, 102, 241, 0.5);
    transform: translateY(-1px);
    opacity: 0.95;
}

.btn-secondary {
    background: rgba(255, 255, 255, 0.08);
    color: var(--text-primary);
    border: 1px solid var(--border-subtle);
}
.btn-secondary:hover {
    background: rgba(255, 255, 255, 0.12);
    border-color: var(--border-medium);
    color: #ffffff;
    transform: translateY(-1px);
}

.btn-success {
    background: #10b981;
    color: #ffffff;
    box-shadow: 0 2px 10px rgba(16, 185, 129, 0.3);
}
.btn-success:hover {
    background: #059669;
    transform: translateY(-1px);
}

.btn-danger, .dred {
    background: #ef4444;
    color: #ffffff;
    box-shadow: 0 2px 10px rgba(239, 68, 68, 0.3);
}
.btn-danger:hover, .dred:hover {
    background: #dc2626;
    transform: translateY(-1px);
}

.btn-outline {
    background: transparent;
    border: 1px solid var(--border-medium);
    color: var(--text-secondary);
}
.btn-outline:hover {
    border-color: var(--primary);
    color: var(--primary);
}

.btn-sm {
    padding: 5px 10px;
    font-size: 0.8rem;
    border-radius: var(--radius-sm);
}

.btn-lg {
    padding: 12px 24px;
    font-size: 1rem;
    border-radius: var(--radius-lg);
}

/* Post Cards & Grid */
.posts-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
    gap: 24px;
    margin-top: 20px;
}

.post-card {
    background: var(--bg-card);
    border: 1px solid var(--border-subtle);
    border-radius: var(--radius-lg);
    overflow: hidden;
    display: flex;
    flex-direction: column;
    transition: var(--transition);
    box-shadow: var(--shadow-md);
}

.post-card:hover {
    transform: translateY(-3px);
    border-color: rgba(99, 102, 241, 0.35);
    box-shadow: var(--shadow-lg);
}

.post-card-media {
    background: #000000;
    max-height: 220px;
    display: flex;
    align-items: center;
    justify-content: center;
    overflow: hidden;
    position: relative;
}

.post-card-media img {
    width: 100%;
    height: 200px;
    object-fit: cover;
    transition: transform 0.3s ease;
}

.post-card:hover .post-card-media img {
    transform: scale(1.03);
}

.post-card-body {
    padding: 20px;
    display: flex;
    flex-direction: column;
    flex: 1;
}

.post-card-header {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 10px;
    margin-bottom: 10px;
}

.post-card-title {
    font-size: 1.15rem;
    font-weight: 700;
    color: #ffffff;
    margin: 0;
    line-height: 1.35;
}

.post-card-excerpt {
    color: var(--text-secondary);
    font-size: 0.9rem;
    line-height: 1.55;
    margin-bottom: 16px;
    flex: 1;
    display: -webkit-box;
    -webkit-line-clamp: 4;
    -webkit-box-orient: vertical;
    overflow: hidden;
}

.post-card-footer {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding-top: 14px;
    border-top: 1px solid var(--border-subtle);
    gap: 8px;
}

/* Media Players */
.media-container {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
    gap: 20px;
    margin: 20px 0;
}

.media-item {
    background: var(--bg-card);
    border: 1px solid var(--border-subtle);
    border-radius: var(--radius-md);
    padding: 16px;
    text-align: center;
    box-shadow: var(--shadow-sm);
}

video, audio {
    width: 100%;
    border-radius: var(--radius-md);
    outline: none;
    margin: 8px 0;
}

.video-wrapper {
    position: relative;
    padding-bottom: 56.25%; /* 16:9 */
    height: 0;
    overflow: hidden;
    border-radius: var(--radius-lg);
    background: #000;
    box-shadow: var(--shadow-lg);
    margin: 16px 0;
}

.video-wrapper iframe {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    border: none;
}

/* Code & Pre Blocks */
pre {
    background-color: #070a12;
    color: #38bdf8;
    padding: 16px;
    border-radius: var(--radius-md);
    border: 1px solid var(--border-subtle);
    font-family: ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, "Liberation Mono", monospace;
    font-size: 13.5px;
    line-height: 1.6;
    overflow-x: auto;
    white-space: pre-wrap;
    word-break: break-word;
    margin: 12px 0;
}

/* Text File Management Grid & Cards */
.file-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
    gap: 16px;
    margin-top: 16px;
}

.file-card {
    background: var(--bg-card);
    border: 1px solid var(--border-subtle);
    border-radius: var(--radius-md);
    padding: 16px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    transition: var(--transition);
}

.file-card:hover {
    border-color: var(--primary);
    transform: translateY(-2px);
    box-shadow: var(--shadow-md);
}

.file-card-title {
    font-size: 1.05rem;
    font-weight: 600;
    color: #ffffff;
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 6px;
    word-break: break-all;
}

.file-card-meta {
    display: flex;
    align-items: center;
    gap: 10px;
    font-size: 0.78rem;
    color: var(--text-muted);
    margin-bottom: 10px;
}

.file-card-preview {
    background: rgba(0, 0, 0, 0.25);
    border: 1px solid var(--border-subtle);
    border-radius: var(--radius-sm);
    padding: 8px 10px;
    font-family: monospace;
    font-size: 0.8rem;
    color: var(--text-secondary);
    max-height: 60px;
    overflow: hidden;
    margin-bottom: 12px;
    white-space: pre-wrap;
}

.file-card-actions {
    display: flex;
    align-items: center;
    justify-content: flex-end;
    gap: 6px;
    padding-top: 10px;
    border-top: 1px solid var(--border-subtle);
}

/* Toolbar & Quick Action Bars */
.toolbar {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    background: var(--bg-card);
    border: 1px solid var(--border-subtle);
    border-radius: var(--radius-md);
    padding: 12px 16px;
    margin-bottom: 20px;
}

.template-btn {
    background: rgba(255, 255, 255, 0.05);
    color: var(--text-secondary);
    border: 1px solid var(--border-subtle);
    border-radius: var(--radius-full);
    padding: 4px 10px;
    font-size: 0.8rem;
    cursor: pointer;
    transition: var(--transition);
}

.template-btn:hover {
    background: rgba(99, 102, 241, 0.15);
    border-color: var(--primary);
    color: #ffffff;
}

/* Terminal / Log Viewer */
.terminal-window {
    background: #050811;
    border: 1px solid var(--border-medium);
    border-radius: var(--radius-lg);
    overflow: hidden;
    box-shadow: var(--shadow-lg);
}

.terminal-header {
    background: #0c111e;
    padding: 10px 16px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    border-bottom: 1px solid var(--border-subtle);
}

.terminal-dots {
    display: flex;
    gap: 6px;
}

.terminal-dot {
    width: 12px;
    height: 12px;
    border-radius: 50%;
}
.dot-red { background: #ef4444; }
.dot-yellow { background: #f59e0b; }
.dot-green { background: #10b981; }

.terminal-body {
    padding: 16px;
    max-height: 600px;
    overflow-y: auto;
    font-family: ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, monospace;
    font-size: 13px;
    line-height: 1.6;
    color: #94a3b8;
}

.terminal-line {
    padding: 2px 0;
    border-bottom: 1px solid rgba(255, 255, 255, 0.02);
}

/* Footer */
footer {
    border-top: 1px solid var(--border-subtle);
    padding: 24px 20px;
    text-align: center;
    color: var(--text-muted);
    font-size: 0.85rem;
    margin-top: auto;
    background: var(--bg-surface);
}

/* Utilities */
.text-center { text-align: center; }
.text-right { text-align: right; }
.text-muted { color: var(--text-muted); }
.d-flex { display: flex; }
.align-center { align-items: center; }
.justify-between { justify-content: space-between; }
.gap-2 { gap: 8px; }
.gap-3 { gap: 12px; }
.mt-1 { margin-top: 4px; }
.mt-2 { margin-top: 8px; }
.mt-3 { margin-top: 16px; }
.mt-4 { margin-top: 24px; }
.mb-1 { margin-bottom: 4px; }
.mb-2 { margin-bottom: 8px; }
.mb-3 { margin-bottom: 16px; }
.mb-4 { margin-bottom: 24px; }
.w-100 { width: 100%; }

@keyframes fadeIn {
    from { opacity: 0; transform: translateY(-4px); }
    to { opacity: 1; transform: translateY(0); }
}

/* Responsive */
@media (max-width: 768px) {
    .sticky-header, header.sticky {
        padding: 10px 14px;
    }
    .brand-title {
        font-size: 1.1rem;
    }
    .posts-grid {
        grid-template-columns: 1fr;
    }
    .container {
        padding: 16px 12px 40px 12px;
    }
}
'''

BASE1 = '''<!doctype html>
<html lang="en">
<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>REMEMBER - Media & Audio</title>
    <link rel="stylesheet" href="/_ui_css/dark.css">
    <script>
        function findString(str) {
            if (!str) return;
            if (window.find) {
                var strFound = window.find(str);
                if (!strFound) {
                    window.find(str, 0, 1);
                }
            }
        }
        function moveToNextOccurrence() {
            var search_str = document.getElementById("search_input").value;
            findString(search_str);
        }
    </script>
</head>
<body>
    <header class="sticky-header">
        <a href="{{ url_for('index') }}" class="brand-wrapper">
            <div class="brand-icon">💾</div>
            <span class="brand-title">REMEMBER</span>
        </a>
        <nav>
            <ul class="nav-links">
                <li><a href="{{ url_for('index') }}" class="nav-link">🏠 Home</a></li>
                <li><a href="{{ url_for('edit_text') }}" class="nav-link">📄 Text Files</a></li>
                <li><a href="{{ url_for('create_text') }}" class="nav-link">➕ New Text</a></li>
                <li><a href="{{ url_for('new_post') }}" class="nav-link">✍️ New Post</a></li>
                <li><a href="{{ url_for('contents') }}" class="nav-link">📑 All Contents</a></li>
                <li><a href="{{ url_for('view_log') }}" class="nav-link">📊 Logs</a></li>
                <li><a href="{{ url_for('search') }}" class="nav-link">🔍 Search</a></li>
                <li><a href="{{ url_for('tube') }}" class="nav-link active">🎬 Media</a></li>
                <li><a href="{{ url_for('edit_ui_html') }}" class="nav-link">🛠️ UI Editor</a></li>
                <li><a href="/" target="media_studio" class="nav-link">🎬 Media Studio</a></li>
            </ul>
        </nav>
        <div class="nav-search">
            <input type="text" id="search_input" placeholder="Quick find..." onkeydown="if(event.key==='Enter') moveToNextOccurrence()" />
            <button id="search_submit" onclick="moveToNextOccurrence()">Find</button>
        </div>
    </header>

    <main class="container">
        <div class="card">
            <div class="card-header">
                <h1 class="card-title">🎬 Featured Video Streams</h1>
                <span class="badge badge-primary">Streaming</span>
            </div>
            
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 20px;">
                <div class="video-wrapper">
                    <iframe 
                        src="https://www.youtube.com/embed/JPaVIDRB_28"
                        title="YouTube video player 1"
                        allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
                        allowfullscreen>
                    </iframe>
                </div>
                <div class="video-wrapper">
                    <iframe 
                        src="https://www.youtube.com/embed/tFaCZGxy1us"
                        title="YouTube video player 2"
                        allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
                        allowfullscreen>
                    </iframe>
                </div>
            </div>
        </div>

        <div class="card mt-4">
            <div class="card-header">
                <h2 class="card-title">🎵 Audio Library</h2>
                <span class="badge badge-info">{{ mp3s|length if mp3s else 0 }} Tracks</span>
            </div>

            {% if mp3s %}
                <div class="media-container">
                    {% for file in mp3s %}
                        <div class="media-item">
                            <span class="badge badge-primary mb-2">MP3 Audio</span>
                            <h4 style="color: #ffffff; font-size: 0.95rem; word-break: break-all; margin: 8px 0;">
                                {{ file.split('/')[-1] }}
                            </h4>
                            <audio controls src="{{ url_for('static', filename=file.replace('static/', '')) }}"></audio>
                        </div>
                    {% endfor %}
                </div>
            {% else %}
                <p class="text-muted text-center" style="padding: 30px 0;">No audio files found in static/play directory.</p>
            {% endif %}
        </div>
    </main>

    <footer>
        <p>&copy; REMEMBER Knowledge & Media Database</p>
    </footer>
</body>
</html>
'''

BASE2 = BASE1

HOME = '''<!doctype html>
<html lang="en">
<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>REMEMBER - Knowledge & Media Hub</title>
    <link rel="stylesheet" href="/_ui_css/dark.css">
    <script>
        function findString(str) {
            if (!str) return;
            if (window.find) {
                var strFound = window.find(str);
                if (!strFound) {
                    window.find(str, 0, 1);
                }
            }
        }
        function moveToNextOccurrence() {
            var search_str = document.getElementById("search_input").value;
            findString(search_str);
        }
    </script>
</head>
<body>
    <header class="sticky-header">
        <a href="{{ url_for('index') }}" class="brand-wrapper">
            <div class="brand-icon">💾</div>
            <span class="brand-title">REMEMBER</span>
        </a>
        <nav>
            <ul class="nav-links">
                <li><a href="{{ url_for('index') }}" class="nav-link active">🏠 Home</a></li>
                <li><a href="{{ url_for('edit_text') }}" class="nav-link">📄 Text Files</a></li>
                <li><a href="{{ url_for('create_text') }}" class="nav-link">➕ New Text</a></li>
                <li><a href="{{ url_for('new_post') }}" class="nav-link">✍️ New Post</a></li>
                <li><a href="{{ url_for('contents') }}" class="nav-link">📑 All Contents</a></li>
                <li><a href="{{ url_for('view_log') }}" class="nav-link">📊 Logs</a></li>
                <li><a href="{{ url_for('search') }}" class="nav-link">🔍 Search</a></li>
                <li><a href="{{ url_for('tube') }}" class="nav-link">🎬 Media</a></li>
                <li><a href="{{ url_for('edit_ui_html') }}" class="nav-link">🛠️ UI Editor</a></li>
                <li><a href="/" target="media_studio" class="nav-link">🎬 Media Studio</a></li>
            </ul>
        </nav>
        <div class="nav-search">
            <input type="text" id="search_input" placeholder="Quick find..." onkeydown="if(event.key==='Enter') moveToNextOccurrence()" />
            <button id="search_submit" onclick="moveToNextOccurrence()">Find</button>
        </div>
    </header>

    <main class="container">
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                <div class="alert-container">
                    {% for category, message in messages %}
                        <div class="alert alert-{{ category if category != 'message' else 'info' }}">
                            <span>{{ message }}</span>
                        </div>
                    {% endfor %}
                </div>
            {% endif %}
        {% endwith %}

        <div class="toolbar">
            <div>
                <h1 style="font-size: 1.5rem; margin: 0; color: #ffffff;">Knowledge & Media Stream</h1>
                <p style="margin: 0; font-size: 0.85rem;" class="text-muted">Explore saved posts, text notes, media clips, and long-term memory.</p>
            </div>
            <div class="d-flex gap-2">
                <a href="{{ url_for('create_text') }}" class="btn btn-secondary btn-sm">➕ New Text File</a>
                <a href="{{ url_for('new_post') }}" class="btn btn-primary btn-sm">✍️ New Post</a>
            </div>
        </div>

        {% if posts %}
            <div class="posts-grid">
                {% for post in posts %}
                    <div class="post-card">
                        {% if post[3] %}
                            <div class="post-card-media">
                                {% if post[3].startswith('data:') or post[3].startswith('/') or post[3].startswith('http') %}
                                    <img src="{{ post[3] }}" alt="{{ post[1] }}">
                                {% elif '/' in post[3] or '.' in post[3] %}
                                    <img src="/static/{{ post[3] }}" alt="{{ post[1] }}">
                                {% else %}
                                    <img src="data:image/png;base64,{{ post[3] }}" alt="{{ post[1] }}">
                                {% endif %}
                            </div>
                        {% endif %}
                        
                        <div class="post-card-body">
                            <div class="post-card-header">
                                <h3 class="post-card-title">{{ post[1] }}</h3>
                                <span class="badge badge-primary">#{{ post[0] }}</span>
                            </div>

                            {% if post[4] %}
                                <div style="margin: 8px 0;">
                                    <video controls style="width: 100%; max-height: 180px; background:#000;">
                                        <source src="{{ url_for('static', filename='videos/' ~ post[4]) }}" type="video/mp4">
                                        Your browser does not support video.
                                    </video>
                                </div>
                            {% endif %}

                            {% if post[5] %}
                                <div style="margin: 8px 0;">
                                    <audio controls style="width: 100%;">
                                        <source src="/static/audio/{{ post[5] }}" type="audio/mpeg">
                                        Your browser does not support audio.
                                    </audio>
                                </div>
                            {% endif %}

                            <p class="post-card-excerpt">{{ post[2][:220] }}{% if post[2]|length > 220 %}...{% endif %}</p>

                            <div class="post-card-footer">
                                <a href="{{ url_for('show_post', post_id=post[0]) }}" class="btn btn-secondary btn-sm">📖 Read More</a>
                                <a href="{{ url_for('edit_post', post_id=post[0]) }}" class="btn btn-outline btn-sm">✏️ Edit</a>
                            </div>
                        </div>
                    </div>
                {% endfor %}
            </div>
        {% else %}
            <div class="card text-center" style="padding: 60px 20px;">
                <div style="font-size: 3rem; margin-bottom: 12px;">📭</div>
                <h2>No Posts Created Yet</h2>
                <p class="text-muted" style="max-width: 450px; margin: 0 auto 20px auto;">
                    Start capturing knowledge, media, or notes into your REMEMBER database.
                </p>
                <div class="d-flex gap-2" style="justify-content: center;">
                    <a href="{{ url_for('new_post') }}" class="btn btn-primary">✍️ Create First Post</a>
                    <a href="{{ url_for('create_text') }}" class="btn btn-secondary">📄 Create Text File</a>
                </div>
            </div>
        {% endif %}
    </main>

    <footer>
        <p>&copy; REMEMBER Knowledge & Media Database</p>
    </footer>
</body>
</html>
'''

NEW_POST = '''<!doctype html>
<html lang="en">
<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>REMEMBER - Create New Post</title>
    <link rel="stylesheet" href="/_ui_css/dark.css">
    <script>
        function updateWordCount(textarea) {
            const text = textarea.value.trim();
            const words = text ? text.split(/\\s+/).length : 0;
            const chars = textarea.value.length;
            document.getElementById("word-count-badge").innerText = `${words} words | ${chars} chars`;
        }
    </script>
</head>
<body>
    <header class="sticky-header">
        <a href="{{ url_for('index') }}" class="brand-wrapper">
            <div class="brand-icon">💾</div>
            <span class="brand-title">REMEMBER</span>
        </a>
        <nav>
            <ul class="nav-links">
                <li><a href="{{ url_for('index') }}" class="nav-link">🏠 Home</a></li>
                <li><a href="{{ url_for('edit_text') }}" class="nav-link">📄 Text Files</a></li>
                <li><a href="{{ url_for('create_text') }}" class="nav-link">➕ New Text</a></li>
                <li><a href="{{ url_for('new_post') }}" class="nav-link active">✍️ New Post</a></li>
                <li><a href="{{ url_for('contents') }}" class="nav-link">📑 All Contents</a></li>
                <li><a href="{{ url_for('view_log') }}" class="nav-link">📊 Logs</a></li>
                <li><a href="{{ url_for('search') }}" class="nav-link">🔍 Search</a></li>
                <li><a href="{{ url_for('tube') }}" class="nav-link">🎬 Media</a></li>
                <li><a href="{{ url_for('edit_ui_html') }}" class="nav-link">🛠️ UI Editor</a></li>
                <li><a href="/" target="media_studio" class="nav-link">🎬 Media Studio</a></li>
            </ul>
        </nav>
    </header>

    <main class="container container-sm">
        <div class="card">
            <div class="card-header">
                <h1 class="card-title">✍️ Create New Post</h1>
                <span class="badge badge-primary">Database Entry</span>
            </div>

            <form action="{{ url_for('new_post') }}" method="post" enctype="multipart/form-data">
                <div class="form-group">
                    <label for="title" class="form-label">Post Title *</label>
                    <input type="text" id="title" name="title" class="form-control" placeholder="Enter an informative title..." required autofocus>
                </div>

                <div class="form-group">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                        <label for="content" class="form-label" style="margin: 0;">Content / Body *</label>
                        <span id="word-count-badge" class="badge">0 words | 0 chars</span>
                    </div>
                    <textarea id="content" name="content" class="form-control" rows="12" placeholder="Write your post content here..." oninput="updateWordCount(this)" required></textarea>
                </div>

                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 16px; margin-bottom: 20px;">
                    <div class="form-group">
                        <label for="image" class="form-label">🖼️ Attach Image</label>
                        <input type="file" id="image" name="image" accept="image/*">
                    </div>

                    <div class="form-group">
                        <label for="video" class="form-label">🎥 Attach Video (.mp4)</label>
                        <input type="file" id="video" name="video" accept="video/*">
                    </div>

                    <div class="form-group">
                        <label for="audio" class="form-label">🎵 Attach Audio (.mp3)</label>
                        <input type="file" id="audio" name="audio" accept="audio/mpeg">
                    </div>
                </div>

                <div class="d-flex justify-between align-center mt-4" style="border-top: 1px solid var(--border-subtle); padding-top: 16px;">
                    <a href="{{ url_for('index') }}" class="btn btn-secondary">↩️ Cancel</a>
                    <button type="submit" class="btn btn-primary btn-lg">💾 Create & Save Post</button>
                </div>
            </form>
        </div>
    </main>

    <footer>
        <p>&copy; REMEMBER Knowledge & Media Database</p>
    </footer>
</body>
</html>
'''

CREATE_TEXT = '''<!doctype html>
<html lang="en">
<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>REMEMBER - Create New Text File</title>
    <link rel="stylesheet" href="/_ui_css/dark.css">
    <script>
        function applyTemplate(type) {
            const textarea = document.getElementById("text_content");
            const filenameInput = document.getElementById("filename");
            const now = new Date();
            const dateStr = now.toISOString().slice(0, 10);
            
            if (type === 'note') {
                if (!filenameInput.value) filenameInput.value = `note_${dateStr}.txt`;
                textarea.value = `# Note - ${dateStr}\\n\\nKey Points:\\n- \\n- \\n\\nDetails:\\n`;
            } else if (type === 'todo') {
                if (!filenameInput.value) filenameInput.value = `todo_${dateStr}.txt`;
                textarea.value = `TODO LIST - ${dateStr}\\n====================\\n[ ] \\n[ ] \\n[ ] \\n\\nCompleted:\\n[x] Setup project\\n`;
            } else if (type === 'markdown') {
                if (!filenameInput.value) filenameInput.value = `doc_${dateStr}.md`;
                textarea.value = `# Title\\n\\n## Overview\\nBrief description of this document.\\n\\n## Specifications\\n- Item 1\\n- Item 2\\n\\n\`\`\`bash\\n# commands here\\n\`\`\`\\n`;
            } else if (type === 'code') {
                if (!filenameInput.value) filenameInput.value = `script_${dateStr}.py`;
                textarea.value = `#!/usr/bin/env python3\\n# -*- coding: utf-8 -*-\\n\\ndef main():\\n    print("Hello from REMEMBER")\\n\\nif __name__ == "__main__":\\n    main()\\n`;
            } else if (type === 'clear') {
                textarea.value = '';
            }
            updateStats();
            textarea.focus();
        }

        function updateStats() {
            const textarea = document.getElementById("text_content");
            const text = textarea.value;
            const lines = text ? text.split('\\n').length : 0;
            const words = text.trim() ? text.trim().split(/\\s+/).length : 0;
            const chars = text.length;
            document.getElementById("stats-badge").innerText = `${lines} lines | ${words} words | ${chars} chars`;
        }

        document.addEventListener("DOMContentLoaded", function() {
            const textarea = document.getElementById("text_content");
            textarea.addEventListener("keydown", function(e) {
                if (e.key === "Tab") {
                    e.preventDefault();
                    const start = this.selectionStart;
                    const end = this.selectionEnd;
                    this.value = this.value.substring(0, start) + "    " + this.value.substring(end);
                    this.selectionStart = this.selectionEnd = start + 4;
                    updateStats();
                } else if ((e.ctrlKey || e.metaKey) && e.key === 's') {
                    e.preventDefault();
                    document.getElementById("create_form").submit();
                }
            });
            updateStats();
        });
    </script>
</head>
<body>
    <header class="sticky-header">
        <a href="{{ url_for('index') }}" class="brand-wrapper">
            <div class="brand-icon">💾</div>
            <span class="brand-title">REMEMBER</span>
        </a>
        <nav>
            <ul class="nav-links">
                <li><a href="{{ url_for('index') }}" class="nav-link">🏠 Home</a></li>
                <li><a href="{{ url_for('edit_text') }}" class="nav-link">📄 Text Files</a></li>
                <li><a href="{{ url_for('create_text') }}" class="nav-link active">➕ New Text</a></li>
                <li><a href="{{ url_for('new_post') }}" class="nav-link">✍️ New Post</a></li>
                <li><a href="{{ url_for('contents') }}" class="nav-link">📑 All Contents</a></li>
                <li><a href="{{ url_for('view_log') }}" class="nav-link">📊 Logs</a></li>
                <li><a href="{{ url_for('search') }}" class="nav-link">🔍 Search</a></li>
                <li><a href="{{ url_for('tube') }}" class="nav-link">🎬 Media</a></li>
                <li><a href="{{ url_for('edit_ui_html') }}" class="nav-link">🛠️ UI Editor</a></li>
                <li><a href="/" target="media_studio" class="nav-link">🎬 Media Studio</a></li>
            </ul>
        </nav>
    </header>

    <main class="container">
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                <div class="alert-container">
                    {% for category, message in messages %}
                        <div class="alert alert-{{ category if category != 'message' else 'info' }}">
                            <span>{{ message }}</span>
                        </div>
                    {% endfor %}
                </div>
            {% endif %}
        {% endwith %}

        <div class="card">
            <div class="card-header">
                <div>
                    <h1 class="card-title">✨ Create New Text File</h1>
                    <p style="margin: 0; font-size: 0.85rem;" class="text-muted">Create and save plain text, markdown, or scripts into static/TEXT.</p>
                </div>
                <span id="stats-badge" class="badge badge-info">0 lines | 0 words | 0 chars</span>
            </div>

            <div class="toolbar" style="margin-bottom: 16px; padding: 10px 14px;">
                <span style="font-size: 0.85rem; font-weight: 600; color: var(--text-secondary);">⚡ Quick Starters:</span>
                <div class="d-flex gap-2" style="flex-wrap: wrap;">
                    <button type="button" class="template-btn" onclick="applyTemplate('note')">📝 Note</button>
                    <button type="button" class="template-btn" onclick="applyTemplate('todo')">📋 To-Do List</button>
                    <button type="button" class="template-btn" onclick="applyTemplate('markdown')">📄 Markdown</button>
                    <button type="button" class="template-btn" onclick="applyTemplate('code')">💻 Code</button>
                    <button type="button" class="template-btn" onclick="applyTemplate('clear')">🧹 Clear</button>
                </div>
            </div>

            <form id="create_form" action="{{ url_for('create_text') }}" method="post">
                <div class="form-group">
                    <label for="filename" class="form-label">Filename *</label>
                    <div style="display: flex; gap: 8px; align-items: center;">
                        <input type="text" id="filename" name="filename" class="form-control" placeholder="e.g. meeting_notes.txt or ideas.md" required autofocus style="max-width: 450px;">
                        <span class="text-muted" style="font-size: 0.85rem;">Saved in static/TEXT/</span>
                    </div>
                </div>

                <div class="form-group">
                    <label for="text_content" class="form-label">Content * (Press Ctrl+S to save)</label>
                    <textarea id="text_content" name="text" class="form-control code-textarea" rows="18" placeholder="Type or paste your text here..." oninput="updateStats()"></textarea>
                </div>

                <div class="d-flex justify-between align-center mt-4" style="border-top: 1px solid var(--border-subtle); padding-top: 16px;">
                    <a href="{{ url_for('edit_text') }}" class="btn btn-secondary">↩️ Back to Text Files</a>
                    <div class="d-flex gap-2">
                        <button type="reset" class="btn btn-outline" onclick="setTimeout(updateStats, 50)">Reset</button>
                        <button type="submit" class="btn btn-primary btn-lg">💾 Save & Create File</button>
                    </div>
                </div>
            </form>
        </div>
    </main>

    <footer>
        <p>&copy; REMEMBER Knowledge & Media Database</p>
    </footer>
</body>
</html>
'''

EDIT_TEXT = '''<!doctype html>
<html lang="en">
<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>REMEMBER - Text Files Manager</title>
    <link rel="stylesheet" href="/_ui_css/dark.css">
    <script>
        function filterFiles() {
            const query = document.getElementById("file_filter_input").value.toLowerCase();
            const cards = document.querySelectorAll(".file-card");
            let visibleCount = 0;
            cards.forEach(card => {
                const name = (card.getAttribute("data-filename") || "").toLowerCase();
                const preview = (card.getAttribute("data-preview") || "").toLowerCase();
                if (name.includes(query) || preview.includes(query)) {
                    card.style.display = "flex";
                    visibleCount++;
                } else {
                    card.style.display = "none";
                }
            });
            document.getElementById("filtered-count").innerText = `${visibleCount} files`;
        }

        function toggleQuickCreate() {
            const panel = document.getElementById("quick-create-panel");
            panel.style.display = (panel.style.display === "none" || panel.style.display === "") ? "block" : "none";
            if (panel.style.display === "block") {
                document.getElementById("quick_filename").focus();
            }
        }
    </script>
</head>
<body>
    <header class="sticky-header">
        <a href="{{ url_for('index') }}" class="brand-wrapper">
            <div class="brand-icon">💾</div>
            <span class="brand-title">REMEMBER</span>
        </a>
        <nav>
            <ul class="nav-links">
                <li><a href="{{ url_for('index') }}" class="nav-link">🏠 Home</a></li>
                <li><a href="{{ url_for('edit_text') }}" class="nav-link active">📄 Text Files</a></li>
                <li><a href="{{ url_for('create_text') }}" class="nav-link">➕ New Text</a></li>
                <li><a href="{{ url_for('new_post') }}" class="nav-link">✍️ New Post</a></li>
                <li><a href="{{ url_for('contents') }}" class="nav-link">📑 All Contents</a></li>
                <li><a href="{{ url_for('view_log') }}" class="nav-link">📊 Logs</a></li>
                <li><a href="{{ url_for('search') }}" class="nav-link">🔍 Search</a></li>
                <li><a href="{{ url_for('tube') }}" class="nav-link">🎬 Media</a></li>
                <li><a href="{{ url_for('edit_ui_html') }}" class="nav-link">🛠️ UI Editor</a></li>
                <li><a href="/" target="media_studio" class="nav-link">🎬 Media Studio</a></li>
            </ul>
        </nav>
    </header>

    <main class="container">
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                <div class="alert-container">
                    {% for category, message in messages %}
                        <div class="alert alert-{{ category if category != 'message' else 'info' }}">
                            <span>{{ message }}</span>
                        </div>
                    {% endfor %}
                </div>
            {% endif %}
        {% endwith %}

        <div class="toolbar">
            <div>
                <h1 style="font-size: 1.5rem; margin: 0; color: #ffffff;">📄 Text Files Manager</h1>
                <p style="margin: 0; font-size: 0.85rem;" class="text-muted">Manage, edit, create, and download text notes stored in static/TEXT.</p>
            </div>
            <div class="d-flex gap-2">
                <button type="button" class="btn btn-secondary btn-sm" onclick="toggleQuickCreate()">⚡ Quick Create</button>
                <a href="{{ url_for('create_text') }}" class="btn btn-primary btn-sm">➕ Create New File</a>
            </div>
        </div>

        <div id="quick-create-panel" class="card" style="display: none; border-color: var(--primary);">
            <div class="card-header">
                <h3 class="card-title" style="font-size: 1.1rem;">⚡ Quick Create Text File</h3>
                <button type="button" class="btn btn-outline btn-sm" onclick="toggleQuickCreate()">✖ Close</button>
            </div>
            <form action="{{ url_for('create_text') }}" method="post">
                <div class="form-group">
                    <label for="quick_filename" class="form-label">Filename</label>
                    <input type="text" id="quick_filename" name="filename" class="form-control" placeholder="e.g. quick_note.txt" required>
                </div>
                <div class="form-group">
                    <label for="quick_text" class="form-label">Content</label>
                    <textarea id="quick_text" name="text" class="form-control code-textarea" rows="6" placeholder="Type text content here..."></textarea>
                </div>
                <div class="d-flex justify-between align-center">
                    <span class="text-muted" style="font-size: 0.85rem;">Saved automatically into static/TEXT</span>
                    <button type="submit" class="btn btn-primary">💾 Save File</button>
                </div>
            </form>
        </div>

        <div class="d-flex justify-between align-center mb-3">
            <div style="flex: 1; max-width: 400px; position: relative;">
                <input type="text" id="file_filter_input" class="form-control" placeholder="🔍 Filter text files by name or content..." oninput="filterFiles()">
            </div>
            <span id="filtered-count" class="badge badge-info">{{ files|length if files else 0 }} files</span>
        </div>

        {% if files %}
            <div class="file-grid">
                {% for file in files %}
                    <div class="file-card" data-filename="{{ file.filename }}" data-preview="{{ file.preview }}">
                        <div>
                            <div class="file-card-title">
                                <span>📄</span>
                                <a href="{{ url_for('edit', filename=file.filename) }}" style="color: #ffffff;">
                                    {{ file.filename }}
                                </a>
                            </div>
                            <div class="file-card-meta">
                                <span>📦 {{ file.size }}</span>
                                <span>🕒 {{ file.mtime }}</span>
                            </div>
                            {% if file.preview %}
                                <div class="file-card-preview">{{ file.preview }}</div>
                            {% endif %}
                        </div>
                        <div class="file-card-actions">
                            <a href="{{ url_for('download_text', filename=file.filename) }}" class="btn btn-outline btn-sm" title="Download">📥</a>
                            <a href="{{ url_for('edit', filename=file.filename) }}" class="btn btn-primary btn-sm">✏️ Edit</a>
                            <a href="{{ url_for('delete', filename=file.filename) }}" class="btn btn-danger btn-sm" onclick="return confirm('Are you sure you want to delete {{ file.filename }}?')" title="Delete">🗑️</a>
                        </div>
                    </div>
                {% endfor %}
            </div>
        {% else %}
            <div class="card text-center" style="padding: 60px 20px;">
                <div style="font-size: 3rem; margin-bottom: 12px;">📝</div>
                <h2>No Text Files Found</h2>
                <p class="text-muted" style="max-width: 450px; margin: 0 auto 20px auto;">
                    You haven't created any text files yet. Create one now to start storing notes, markdown, or scripts.
                </p>
                <a href="{{ url_for('create_text') }}" class="btn btn-primary btn-lg">➕ Create Your First Text File</a>
            </div>
        {% endif %}
    </main>

    <footer>
        <p>&copy; REMEMBER Knowledge & Media Database</p>
    </footer>
</body>
</html>
'''

EDIT = '''<!doctype html>
<html lang="en">
<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>REMEMBER - Editing {{ filename }}</title>
    <link rel="stylesheet" href="/_ui_css/dark.css">
    <script>
        function updateStats() {
            const textarea = document.getElementById("text");
            const text = textarea.value;
            const lines = text ? text.split('\\n').length : 0;
            const words = text.trim() ? text.trim().split(/\\s+/).length : 0;
            const chars = text.length;
            document.getElementById("stats-badge").innerText = `${lines} lines | ${words} words | ${chars} chars`;
        }

        function copyAllText() {
            const textarea = document.getElementById("text");
            navigator.clipboard.writeText(textarea.value).then(() => {
                const btn = document.getElementById("copy-btn");
                const orig = btn.innerHTML;
                btn.innerHTML = "✅ Copied!";
                setTimeout(() => { btn.innerHTML = orig; }, 2000);
            });
        }

        document.addEventListener("DOMContentLoaded", function() {
            const textarea = document.getElementById("text");
            textarea.addEventListener("keydown", function(e) {
                if (e.key === "Tab") {
                    e.preventDefault();
                    const start = this.selectionStart;
                    const end = this.selectionEnd;
                    this.value = this.value.substring(0, start) + "    " + this.value.substring(end);
                    this.selectionStart = this.selectionEnd = start + 4;
                    updateStats();
                } else if ((e.ctrlKey || e.metaKey) && e.key === 's') {
                    e.preventDefault();
                    document.getElementById("edit_form").submit();
                }
            });
            updateStats();
        });
    </script>
</head>
<body>
    <header class="sticky-header">
        <a href="{{ url_for('index') }}" class="brand-wrapper">
            <div class="brand-icon">💾</div>
            <span class="brand-title">REMEMBER</span>
        </a>
        <nav>
            <ul class="nav-links">
                <li><a href="{{ url_for('index') }}" class="nav-link">🏠 Home</a></li>
                <li><a href="{{ url_for('edit_text') }}" class="nav-link active">📄 Text Files</a></li>
                <li><a href="{{ url_for('create_text') }}" class="nav-link">➕ New Text</a></li>
                <li><a href="{{ url_for('new_post') }}" class="nav-link">✍️ New Post</a></li>
                <li><a href="{{ url_for('contents') }}" class="nav-link">📑 All Contents</a></li>
                <li><a href="{{ url_for('view_log') }}" class="nav-link">📊 Logs</a></li>
                <li><a href="{{ url_for('search') }}" class="nav-link">🔍 Search</a></li>
                <li><a href="{{ url_for('tube') }}" class="nav-link">🎬 Media</a></li>
                <li><a href="{{ url_for('edit_ui_html') }}" class="nav-link">🛠️ UI Editor</a></li>
                <li><a href="/" target="media_studio" class="nav-link">🎬 Media Studio</a></li>
            </ul>
        </nav>
    </header>

    <main class="container">
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                <div class="alert-container">
                    {% for category, message in messages %}
                        <div class="alert alert-{{ category if category != 'message' else 'info' }}">
                            <span>{{ message }}</span>
                        </div>
                    {% endfor %}
                </div>
            {% endif %}
        {% endwith %}

        <div class="card">
            <div class="card-header">
                <div>
                    <h1 class="card-title" style="font-size: 1.35rem;">
                        📝 Editing: <span style="color: var(--accent-blue);">{{ filename }}</span>
                    </h1>
                    <div class="d-flex gap-2 mt-1">
                        {% if file_info %}
                            <span class="badge">Size: {{ file_info.size }}</span>
                            <span class="badge">Modified: {{ file_info.mtime }}</span>
                        {% endif %}
                    </div>
                </div>
                <div class="d-flex gap-2 align-center">
                    <span id="stats-badge" class="badge badge-info">0 lines | 0 words | 0 chars</span>
                    <button id="copy-btn" type="button" class="btn btn-secondary btn-sm" onclick="copyAllText()">📋 Copy All</button>
                    <a href="{{ url_for('download_text', filename=filename) }}" class="btn btn-outline btn-sm">📥 Download</a>
                    <a href="{{ url_for('delete', filename=filename) }}" class="btn btn-danger btn-sm" onclick="return confirm('Delete {{ filename }}?')">🗑️ Delete</a>
                </div>
            </div>

            <form id="edit_form" action="{{ url_for('edit', filename=filename) }}" method="post">
                <div class="form-group">
                    <textarea id="text" name="text" class="form-control code-textarea" rows="22" oninput="updateStats()" required>{{ text }}</textarea>
                </div>

                <div class="d-flex justify-between align-center mt-3" style="border-top: 1px solid var(--border-subtle); padding-top: 16px;">
                    <a href="{{ url_for('edit_text') }}" class="btn btn-secondary">↩️ Back to Text Files</a>
                    <div class="d-flex gap-2">
                        <a href="{{ url_for('create_text') }}" class="btn btn-outline">➕ Create Another File</a>
                        <button type="submit" class="btn btn-primary btn-lg">💾 Save Changes (Ctrl+S)</button>
                    </div>
                </div>
            </form>
        </div>
    </main>

    <footer>
        <p>&copy; REMEMBER Knowledge & Media Database</p>
    </footer>
</body>
</html>
'''

CONTENTS = '''<!doctype html>
<html lang="en">
<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>REMEMBER - Table of Contents</title>
    <link rel="stylesheet" href="/_ui_css/dark.css">
    <script>
        function filterContents() {
            const query = document.getElementById("search_filter").value.toLowerCase();
            const rows = document.querySelectorAll(".content-row");
            let count = 0;
            rows.forEach(row => {
                const title = (row.getAttribute("data-title") || "").toLowerCase();
                const excerpt = (row.getAttribute("data-excerpt") || "").toLowerCase();
                if (title.includes(query) || excerpt.includes(query)) {
                    row.style.display = "block";
                    count++;
                } else {
                    row.style.display = "none";
                }
            });
            document.getElementById("count-badge").innerText = `${count} entries`;
        }
    </script>
</head>
<body>
    <header class="sticky-header">
        <a href="{{ url_for('index') }}" class="brand-wrapper">
            <div class="brand-icon">💾</div>
            <span class="brand-title">REMEMBER</span>
        </a>
        <nav>
            <ul class="nav-links">
                <li><a href="{{ url_for('index') }}" class="nav-link">🏠 Home</a></li>
                <li><a href="{{ url_for('edit_text') }}" class="nav-link">📄 Text Files</a></li>
                <li><a href="{{ url_for('create_text') }}" class="nav-link">➕ New Text</a></li>
                <li><a href="{{ url_for('new_post') }}" class="nav-link">✍️ New Post</a></li>
                <li><a href="{{ url_for('contents') }}" class="nav-link active">📑 All Contents</a></li>
                <li><a href="{{ url_for('view_log') }}" class="nav-link">📊 Logs</a></li>
                <li><a href="{{ url_for('search') }}" class="nav-link">🔍 Search</a></li>
                <li><a href="{{ url_for('tube') }}" class="nav-link">🎬 Media</a></li>
                <li><a href="{{ url_for('edit_ui_html') }}" class="nav-link">🛠️ UI Editor</a></li>
                <li><a href="/" target="media_studio" class="nav-link">🎬 Media Studio</a></li>
            </ul>
        </nav>
    </header>

    <main class="container">
        <div class="toolbar">
            <div>
                <h1 style="font-size: 1.5rem; margin: 0; color: #ffffff;">📑 Table of Contents</h1>
                <p style="margin: 0; font-size: 0.85rem;" class="text-muted">Master index of all memory posts stored in SQLite database.</p>
            </div>
            <div class="d-flex gap-2">
                <input type="text" id="search_filter" class="form-control" placeholder="🔍 Filter contents..." oninput="filterContents()" style="width: 220px;">
                <span id="count-badge" class="badge badge-primary">{{ contents_data|length if contents_data else 0 }} entries</span>
            </div>
        </div>

        {% if contents_data %}
            {% for content in contents_data %}
                <div class="card content-row mb-3" data-title="{{ content.title }}" data-excerpt="{{ content.excerpt }}">
                    <div class="d-flex justify-between align-center mb-2">
                        <div class="d-flex align-center gap-2">
                            <span class="badge badge-primary">#{{ content.id }}</span>
                            <h2 style="font-size: 1.2rem; margin: 0; color: #ffffff;">{{ content.title }}</h2>
                        </div>
                        <div class="d-flex gap-2">
                            <a href="{{ url_for('show_post', post_id=content.id) }}" class="btn btn-secondary btn-sm">📖 Read Full Post</a>
                            <a href="{{ url_for('edit_post', post_id=content.id) }}" class="btn btn-outline btn-sm">✏️ Edit</a>
                        </div>
                    </div>
                    <pre style="margin: 8px 0; max-height: 120px; overflow-y: hidden;">{{ content.excerpt }}</pre>
                </div>
            {% endfor %}
        {% else %}
            <div class="card text-center" style="padding: 50px 20px;">
                <h2>No Posts Found in Database</h2>
                <p class="text-muted">Create a new post to build your table of contents.</p>
                <a href="{{ url_for('new_post') }}" class="btn btn-primary">✍️ Create New Post</a>
            </div>
        {% endif %}
    </main>

    <footer>
        <p>&copy; REMEMBER Knowledge & Media Database</p>
    </footer>
</body>
</html>
'''

VIEW_LOG = '''<!doctype html>
<html lang="en">
<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>REMEMBER - Application Logs</title>
    <link rel="stylesheet" href="/_ui_css/dark.css">
    <script>
        function filterLogs() {
            const query = document.getElementById("log_filter").value.toLowerCase();
            const lines = document.querySelectorAll(".terminal-line");
            let count = 0;
            lines.forEach(line => {
                const text = line.innerText.toLowerCase();
                if (text.includes(query)) {
                    line.style.display = "block";
                    count++;
                } else {
                    line.style.display = "none";
                }
            });
            document.getElementById("log-count").innerText = `${count} lines`;
        }
    </script>
</head>
<body>
    <header class="sticky-header">
        <a href="{{ url_for('index') }}" class="brand-wrapper">
            <div class="brand-icon">💾</div>
            <span class="brand-title">REMEMBER</span>
        </a>
        <nav>
            <ul class="nav-links">
                <li><a href="{{ url_for('index') }}" class="nav-link">🏠 Home</a></li>
                <li><a href="{{ url_for('edit_text') }}" class="nav-link">📄 Text Files</a></li>
                <li><a href="{{ url_for('create_text') }}" class="nav-link">➕ New Text</a></li>
                <li><a href="{{ url_for('new_post') }}" class="nav-link">✍️ New Post</a></li>
                <li><a href="{{ url_for('contents') }}" class="nav-link">📑 All Contents</a></li>
                <li><a href="{{ url_for('view_log') }}" class="nav-link active">📊 Logs</a></li>
                <li><a href="{{ url_for('search') }}" class="nav-link">🔍 Search</a></li>
                <li><a href="{{ url_for('tube') }}" class="nav-link">🎬 Media</a></li>
                <li><a href="{{ url_for('edit_ui_html') }}" class="nav-link">🛠️ UI Editor</a></li>
                <li><a href="/" target="media_studio" class="nav-link">🎬 Media Studio</a></li>
            </ul>
        </nav>
    </header>

    <main class="container">
        <div class="toolbar">
            <div>
                <h1 style="font-size: 1.5rem; margin: 0; color: #ffffff;">📊 Application Logs</h1>
                <p style="margin: 0; font-size: 0.85rem;" class="text-muted">Real-time trace generated by the logit utility in static/REMEMBER_log.txt.</p>
            </div>
            <div class="d-flex gap-2 align-center">
                <input type="text" id="log_filter" class="form-control" placeholder="🔍 Filter log entries..." oninput="filterLogs()" style="width: 200px;">
                <span id="log-count" class="badge badge-info">{{ data|length if data else 0 }} lines</span>
                <a href="{{ url_for('view_log') }}" class="btn btn-secondary btn-sm">🔄 Refresh</a>
                <a href="{{ url_for('delete_log') }}" class="btn btn-danger btn-sm" onclick="return confirm('Clear all application logs?')">🗑️ Clear Log</a>
            </div>
        </div>

        <div class="terminal-window">
            <div class="terminal-header">
                <div class="terminal-dots">
                    <div class="terminal-dot dot-red"></div>
                    <div class="terminal-dot dot-yellow"></div>
                    <div class="terminal-dot dot-green"></div>
                </div>
                <span style="font-size: 0.8rem; color: var(--text-muted); font-family: monospace;">static/REMEMBER_log.txt</span>
                <span class="badge badge-primary">Trace Output</span>
            </div>
            <div class="terminal-body" id="log-body">
                {% if data %}
                    {% for log in data %}
                        {% if log.strip() %}
                            <div class="terminal-line">
                                <span style="color: var(--text-muted); margin-right: 8px;">{{ loop.index }}.</span>
                                {{ log }}
                            </div>
                        {% endif %}
                    {% endfor %}
                {% else %}
                    <div class="text-center text-muted" style="padding: 40px 0;">Log is currently empty.</div>
                {% endif %}
            </div>
        </div>
    </main>

    <footer>
        <p>&copy; REMEMBER Knowledge & Media Database</p>
    </footer>
</body>
</html>
'''

SEARCH = '''<!doctype html>
<html lang="en">
<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>REMEMBER - Search Database</title>
    <link rel="stylesheet" href="/_ui_css/dark.css">
    <script>
        function setQuery(term) {
            const input = document.getElementById("search_terms");
            input.value = term;
            document.getElementById("search_form").submit();
        }
    </script>
</head>
<body>
    <header class="sticky-header">
        <a href="{{ url_for('index') }}" class="brand-wrapper">
            <div class="brand-icon">💾</div>
            <span class="brand-title">REMEMBER</span>
        </a>
        <nav>
            <ul class="nav-links">
                <li><a href="{{ url_for('index') }}" class="nav-link">🏠 Home</a></li>
                <li><a href="{{ url_for('edit_text') }}" class="nav-link">📄 Text Files</a></li>
                <li><a href="{{ url_for('create_text') }}" class="nav-link">➕ New Text</a></li>
                <li><a href="{{ url_for('new_post') }}" class="nav-link">✍️ New Post</a></li>
                <li><a href="{{ url_for('contents') }}" class="nav-link">📑 All Contents</a></li>
                <li><a href="{{ url_for('view_log') }}" class="nav-link">📊 Logs</a></li>
                <li><a href="{{ url_for('search') }}" class="nav-link active">🔍 Search</a></li>
                <li><a href="{{ url_for('tube') }}" class="nav-link">🎬 Media</a></li>
                <li><a href="{{ url_for('edit_ui_html') }}" class="nav-link">🛠️ UI Editor</a></li>
                <li><a href="/" target="media_studio" class="nav-link">🎬 Media Studio</a></li>
            </ul>
        </nav>
    </header>

    <main class="container">
        <div class="card">
            <div class="card-header">
                <h1 class="card-title">🔍 Search Memory Database</h1>
                <span class="badge badge-primary">SQLite Match</span>
            </div>

            <form id="search_form" action="{{ url_for('search') }}" method="post">
                <div class="form-group">
                    <label for="search_terms" class="form-label">Search Query (Separate multiple terms with commas):</label>
                    <div style="display: flex; gap: 10px;">
                        <input type="text" id="search_terms" name="search_terms" class="form-control" placeholder="e.g. python, flask, audio, documentation..." required autofocus>
                        <button type="submit" class="btn btn-primary btn-lg">🔍 Search</button>
                    </div>
                </div>
            </form>
        </div>

        {% if results %}
            <div class="toolbar mt-4">
                <h2 style="font-size: 1.25rem; margin: 0; color: #ffffff;">Search Results</h2>
                <span class="badge badge-success">{{ results|length }} matches found</span>
            </div>

            <div class="posts-grid">
                {% for post in results %}
                    <div class="post-card">
                        {% if post[3] %}
                            <div class="post-card-media">
                                {% if post[3].startswith('data:') or post[3].startswith('/') or post[3].startswith('http') %}
                                    <img src="{{ post[3] }}" alt="{{ post[1] }}">
                                {% elif '/' in post[3] or '.' in post[3] %}
                                    <img src="/static/{{ post[3] }}" alt="{{ post[1] }}">
                                {% else %}
                                    <img src="data:image/png;base64,{{ post[3] }}" alt="{{ post[1] }}">
                                {% endif %}
                            </div>
                        {% endif %}

                        <div class="post-card-body">
                            <div class="post-card-header">
                                <h3 class="post-card-title">{{ post[1] }}</h3>
                                <span class="badge badge-primary">#{{ post[0] }}</span>
                            </div>

                            {% if post[4] %}
                                <div style="margin: 8px 0;">
                                    <video controls style="width: 100%; max-height: 180px;">
                                        <source src="/static/videos/{{ post[4] }}" type="video/mp4">
                                    </video>
                                </div>
                            {% endif %}

                            {% if post[5] %}
                                <div style="margin: 8px 0;">
                                    <audio controls style="width: 100%;">
                                        <source src="/static/audio/{{ post[5] }}" type="audio/mpeg">
                                    </audio>
                                </div>
                            {% endif %}

                            <p class="post-card-excerpt">{{ post[2][:220] }}{% if post[2]|length > 220 %}...{% endif %}</p>

                            <div class="post-card-footer">
                                <a href="{{ url_for('show_post', post_id=post[0]) }}" class="btn btn-secondary btn-sm">📖 Read More</a>
                                <a href="{{ url_for('edit_post', post_id=post[0]) }}" class="btn btn-outline btn-sm">✏️ Edit</a>
                            </div>
                        </div>
                    </div>
                {% endfor %}
            </div>
        {% elif request.method == 'POST' %}
            <div class="card text-center mt-4" style="padding: 50px 20px;">
                <div style="font-size: 2.5rem; margin-bottom: 10px;">🔍</div>
                <h2>No Matching Posts Found</h2>
                <p class="text-muted">Try searching with different keywords or broader terms.</p>
            </div>
        {% endif %}
    </main>

    <footer>
        <p>&copy; REMEMBER Knowledge & Media Database</p>
    </footer>
</body>
</html>
'''

EDIT_POST = '''<!doctype html>
<html lang="en">
<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>REMEMBER - Edit Post #{{ post[0] }}</title>
    <link rel="stylesheet" href="/_ui_css/dark.css">
</head>
<body>
    <header class="sticky-header">
        <a href="{{ url_for('index') }}" class="brand-wrapper">
            <div class="brand-icon">💾</div>
            <span class="brand-title">REMEMBER</span>
        </a>
        <nav>
            <ul class="nav-links">
                <li><a href="{{ url_for('index') }}" class="nav-link">🏠 Home</a></li>
                <li><a href="{{ url_for('edit_text') }}" class="nav-link">📄 Text Files</a></li>
                <li><a href="{{ url_for('create_text') }}" class="nav-link">➕ New Text</a></li>
                <li><a href="{{ url_for('new_post') }}" class="nav-link">✍️ New Post</a></li>
                <li><a href="{{ url_for('contents') }}" class="nav-link">📑 All Contents</a></li>
                <li><a href="{{ url_for('view_log') }}" class="nav-link">📊 Logs</a></li>
                <li><a href="{{ url_for('search') }}" class="nav-link">🔍 Search</a></li>
                <li><a href="{{ url_for('tube') }}" class="nav-link">🎬 Media</a></li>
                <li><a href="{{ url_for('edit_ui_html') }}" class="nav-link">🛠️ UI Editor</a></li>
                <li><a href="/" target="media_studio" class="nav-link">🎬 Media Studio</a></li>
            </ul>
        </nav>
    </header>

    <main class="container container-sm">
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                <div class="alert-container">
                    {% for category, message in messages %}
                        <div class="alert alert-{{ category if category != 'message' else 'info' }}">
                            <span>{{ message }}</span>
                        </div>
                    {% endfor %}
                </div>
            {% endif %}
        {% endwith %}

        <div class="card">
            <div class="card-header">
                <div>
                    <h1 class="card-title">✏️ Edit Post</h1>
                    <span class="badge badge-primary">ID: #{{ post[0] }}</span>
                </div>
                <a href="{{ url_for('show_post', post_id=post[0]) }}" class="btn btn-secondary btn-sm">👁️ View Post</a>
            </div>

            <form method="POST" enctype="multipart/form-data">
                <div class="form-group">
                    <label for="title" class="form-label">Title *</label>
                    <input type="text" id="title" name="title" class="form-control" value="{{ post[1] }}" required>
                </div>

                <div class="form-group">
                    <label for="content" class="form-label">Content *</label>
                    <textarea id="content" name="content" class="form-control" rows="14" required>{{ post[2] }}</textarea>
                </div>

                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 16px; margin: 20px 0;">
                    <div class="form-group">
                        <label class="form-label">🖼️ Replace Image</label>
                        {% if post[3] %}
                            <div style="margin-bottom: 8px;">
                                <img src="data:image/png;base64,{{ post[3] }}" alt="Current Image" style="max-height: 120px; border-radius: var(--radius-sm);">
                            </div>
                        {% endif %}
                        <input type="file" name="image" accept="image/*">
                    </div>

                    <div class="form-group">
                        <label class="form-label">🎥 Replace Video</label>
                        {% if post[4] %}
                            <div style="margin-bottom: 8px;">
                                <video controls style="max-height: 120px; width: 100%;">
                                    <source src="{{ url_for('static', filename='videos/' + post[4]) }}" type="video/mp4">
                                </video>
                            </div>
                        {% endif %}
                        <input type="file" id="video" name="video" accept="video/*">
                    </div>

                    <div class="form-group">
                        <label class="form-label">🎵 Replace Audio</label>
                        {% if post[5] %}
                            <div style="margin-bottom: 8px;">
                                <audio controls style="width: 100%;">
                                    <source src="/static/audio/{{ post[5] }}" type="audio/mpeg">
                                </audio>
                            </div>
                        {% endif %}
                        <input type="file" id="audio" name="audio" accept="audio/*">
                    </div>
                </div>

                <div class="d-flex justify-between align-center mt-4" style="border-top: 1px solid var(--border-subtle); padding-top: 16px;">
                    <a href="{{ url_for('show_post', post_id=post[0]) }}" class="btn btn-secondary">↩️ Cancel</a>
                    <button type="submit" class="btn btn-primary btn-lg">💾 Update Post</button>
                </div>
            </form>
        </div>
    </main>

    <footer>
        <p>&copy; REMEMBER Knowledge & Media Database</p>
    </footer>
</body>
</html>
'''

READ_LOG = '''<!doctype html>
<html lang="en">
<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>REMEMBER - Log Viewer</title>
    <link rel="stylesheet" href="/_ui_css/dark.css">
</head>
<body>
    <header class="sticky-header">
        <a href="{{ url_for('index') }}" class="brand-wrapper">
            <div class="brand-icon">💾</div>
            <span class="brand-title">REMEMBER</span>
        </a>
        <nav>
            <ul class="nav-links">
                <li><a href="{{ url_for('index') }}" class="nav-link">🏠 Home</a></li>
                <li><a href="{{ url_for('edit_text') }}" class="nav-link">📄 Text Files</a></li>
                <li><a href="{{ url_for('create_text') }}" class="nav-link">➕ New Text</a></li>
                <li><a href="{{ url_for('new_post') }}" class="nav-link">✍️ New Post</a></li>
                <li><a href="{{ url_for('contents') }}" class="nav-link">📑 All Contents</a></li>
                <li><a href="{{ url_for('view_log') }}" class="nav-link active">📊 Logs</a></li>
                <li><a href="{{ url_for('search') }}" class="nav-link">🔍 Search</a></li>
                <li><a href="{{ url_for('tube') }}" class="nav-link">🎬 Media</a></li>
                <li><a href="{{ url_for('edit_ui_html') }}" class="nav-link">🛠️ UI Editor</a></li>
                <li><a href="/" target="media_studio" class="nav-link">🎬 Media Studio</a></li>
            </ul>
        </nav>
    </header>

    <main class="container">
        <div class="toolbar">
            <h1 style="font-size: 1.5rem; margin: 0; color: #ffffff;">📊 Application Log Stream</h1>
            <div class="d-flex gap-2">
                <a href="/readlog" class="btn btn-secondary btn-sm">🔄 Refresh</a>
                <a href="/delete_log" class="btn btn-danger btn-sm" onclick="return confirm('Delete logs?')">🗑️ Delete Log</a>
            </div>
        </div>

        <div class="terminal-window">
            <div class="terminal-header">
                <span style="font-family: monospace; font-size: 0.85rem; color: #94a3b8;">static/REMEMBER_log.txt</span>
                <span class="badge badge-info">{{ log_content|length if log_content else 0 }} entries</span>
            </div>
            <div class="terminal-body">
                {% if log_content %}
                    {% for log in log_content %}
                        {% if log.strip() %}
                            <div class="terminal-line">{{ log }}</div>
                        {% endif %}
                    {% endfor %}
                {% else %}
                    <div class="text-center text-muted">No log entries found.</div>
                {% endif %}
            </div>
        </div>
    </main>

    <footer>
        <p>&copy; REMEMBER Knowledge & Media Database</p>
    </footer>
</body>
</html>
'''

POST = '''<!doctype html>
<html lang="en">
<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>REMEMBER - {{ post[1] }}</title>
    <link rel="stylesheet" href="/_ui_css/dark.css">
</head>
<body>
    <header class="sticky-header">
        <a href="{{ url_for('index') }}" class="brand-wrapper">
            <div class="brand-icon">💾</div>
            <span class="brand-title">REMEMBER</span>
        </a>
        <nav>
            <ul class="nav-links">
                <li><a href="{{ url_for('index') }}" class="nav-link">🏠 Home</a></li>
                <li><a href="{{ url_for('edit_text') }}" class="nav-link">📄 Text Files</a></li>
                <li><a href="{{ url_for('create_text') }}" class="nav-link">➕ New Text</a></li>
                <li><a href="{{ url_for('new_post') }}" class="nav-link">✍️ New Post</a></li>
                <li><a href="{{ url_for('contents') }}" class="nav-link">📑 All Contents</a></li>
                <li><a href="{{ url_for('view_log') }}" class="nav-link">📊 Logs</a></li>
                <li><a href="{{ url_for('search') }}" class="nav-link">🔍 Search</a></li>
                <li><a href="{{ url_for('tube') }}" class="nav-link">🎬 Media</a></li>
                <li><a href="{{ url_for('edit_ui_html') }}" class="nav-link">🛠️ UI Editor</a></li>
                <li><a href="/" target="media_studio" class="nav-link">🎬 Media Studio</a></li>
            </ul>
        </nav>
    </header>

    <main class="container">
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                <div class="alert-container">
                    {% for category, message in messages %}
                        <div class="alert alert-{{ category if category != 'message' else 'info' }}">
                            <span>{{ message }}</span>
                        </div>
                    {% endfor %}
                </div>
            {% endif %}
        {% endwith %}

        <div class="card">
            <div class="card-header">
                <div>
                    <span class="badge badge-primary mb-1">Post #{{ post[0] }}</span>
                    <h1 style="font-size: 1.8rem; margin: 0; color: #ffffff;">{{ post[1] }}</h1>
                </div>
                <div class="d-flex gap-2">
                    <a href="{{ url_for('index') }}" class="btn btn-secondary btn-sm">↩️ Back</a>
                    <a href="{{ url_for('edit_post', post_id=post[0]) }}" class="btn btn-primary btn-sm">✏️ Edit Post</a>
                </div>
            </div>

            <pre style="font-size: 1rem; line-height: 1.7; padding: 20px; background: #070a12;">{{ post[2] }}</pre>

            {% if post[3] or post[4] or post[5] %}
                <div class="mt-4" style="border-top: 1px solid var(--border-subtle); padding-top: 20px;">
                    <h3 style="margin-bottom: 16px;">Attached Media</h3>
                    
                        {% if post[3] %}
                            <div class="media-item">
                                <span class="badge badge-info mb-2">Image</span>
                                {% if post[3].startswith('data:') or post[3].startswith('/') or post[3].startswith('http') %}
                                    <img src="{{ post[3] }}" alt="{{ post[1] }}" style="max-height: 480px; width: 100%; object-fit: contain; border-radius: var(--radius-md);">
                                {% elif '/' in post[3] or '.' in post[3] %}
                                    <img src="/static/{{ post[3] }}" alt="{{ post[1] }}" style="max-height: 480px; width: 100%; object-fit: contain; border-radius: var(--radius-md);">
                                {% else %}
                                    <img src="data:image/png;base64,{{ post[3] }}" alt="{{ post[1] }}" style="max-height: 480px; width: 100%; object-fit: contain; border-radius: var(--radius-md);">
                                {% endif %}
                            </div>
                        {% endif %}

                        {% if post[4] %}
                            <div class="media-item">
                                <span class="badge badge-primary mb-2">Video Attachment</span>
                                <video controls style="width: 100%; max-height: 300px; background: #000;">
                                    <source src="/static/videos/{{ post[4] }}" type="video/mp4" />
                                    Your browser does not support video.
                                </video>
                            </div>
                        {% endif %}

                        {% if post[5] %}
                            <div class="media-item">
                                <span class="badge badge-success mb-2">Audio Attachment</span>
                                <audio controls style="width: 100%; margin-top: 20px;">
                                    <source src="/static/audio/{{ post[5] }}" type="audio/mpeg">
                                    Your browser does not support audio.
                                </audio>
                            </div>
                        {% endif %}
                    </div>
                </div>
            {% endif %}
        </div>

        <div class="card mt-4">
            <div class="card-header">
                <h3 class="card-title">📎 Add Attachments to Post #{{ post[0] }}</h3>
            </div>

            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 20px;">
                <form method="post" enctype="multipart/form-data" action="{{ url_for('upload_image', post_id=post[0]) }}" class="card" style="margin: 0; background: rgba(0,0,0,0.2); border: 1px solid var(--border-subtle);">
                    <label for="imageFile" class="form-label">🖼️ Upload / Replace Image (.png, .jpg, .webp):</label>
                    <div class="form-group">
                        <input type="file" id="imageFile" name="imageFile" accept="image/*" required />
                    </div>
                    <button type="submit" class="btn btn-primary w-100">Upload Image</button>
                </form>

                <form method="post" enctype="multipart/form-data" action="{{ url_for('upload_video', post_id=post[0]) }}" class="card" style="margin: 0; background: rgba(0,0,0,0.2); border: 1px solid var(--border-subtle);">
                    <label for="videoFile" class="form-label">🎥 Upload / Replace Video (.mp4):</label>
                    <div class="form-group">
                        <input type="file" id="videoFile" name="videoFile" accept="video/mp4" required />
                    </div>
                    <button type="submit" class="btn btn-secondary w-100">Upload Video</button>
                </form>

                <form method="post" enctype="multipart/form-data" action="{{ url_for('upload_audio', post_id=post[0]) }}" class="card" style="margin: 0; background: rgba(0,0,0,0.2); border: 1px solid var(--border-subtle);">
                    <label for="audio" class="form-label">🎵 Upload / Replace Audio (.mp3):</label>
                    <div class="form-group">
                        <input type="file" id="audio" name="audio" accept="audio/mpeg" required />
                    </div>
                    <button type="submit" class="btn btn-secondary w-100">Upload Audio</button>
                </form>
            </div>
        </div>
    </main>

    <footer>
        <p>&copy; REMEMBER Knowledge & Media Database</p>
    </footer>
</body>
</html>
'''
