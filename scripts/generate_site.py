#!/usr/bin/env python3
"""
Generate static HTML site from user data and file listings.
"""
import json
import sys
import base64
from pathlib import Path

def get_file_icon(category):
    """Get emoji icon for file category."""
    icons = {
        'video': '🎥',
        'audio': '🎵',
        'image': '🖼️',
        'pdf': '📄',
        'other': '📎'
    }
    return icons.get(category, '📎')

def render_file_card(file):
    """Render a single file card."""
    icon = get_file_icon(file['category'])
    link = file['link']
    name = file['name']
    size = file['size']
    
    if file['category'] == 'video':
        return f'''
        <div class="file-item">
            <div class="file-info">
                <div class="file-name">{name}</div>
                <div class="file-size">{size}</div>
            </div>
            <video controls style="width: 100%; max-width: 700px; margin: 10px 0;">
                <source src="{link}" type="video/mp4">
                Your browser does not support the video element.
            </video>
            <a href="{link}" download class="download-btn">Download</a>
        </div>
        '''
    elif file['category'] == 'audio':
        return f'''
        <div class="file-item">
            <div class="file-info">
                <div class="file-name">{name}</div>
                <div class="file-size">{size}</div>
            </div>
            <audio controls style="width: 100%; max-width: 700px; margin: 10px 0;">
                <source src="{link}" type="audio/mpeg">
                Your browser does not support the audio element.
            </audio>
            <a href="{link}" download class="download-btn">Download</a>
        </div>
        '''
    elif file['category'] == 'image':
        return f'''
        <div class="file-item">
            <div class="file-info">
                <div class="file-name">{name}</div>
                <div class="file-size">{size}</div>
            </div>
            <img src="{link}" alt="{name}" style="max-width: 700px; width: 100%; margin: 10px 0; border: 1px solid #333;" loading="lazy">
            <a href="{link}" download class="download-btn">Download</a>
        </div>
        '''
    elif file['category'] == 'pdf':
        return f'''
        <div class="file-item">
            <div class="file-info">
                <div class="file-name">{name}</div>
                <div class="file-size">{size}</div>
            </div>
            <iframe src="{link}" style="width: 100%; max-width: 700px; height: 500px; margin: 10px 0; border: 1px solid #333;"></iframe>
            <a href="{link}" target="_blank" class="download-btn">Open PDF</a>
        </div>
        '''
    else:
        return f'''
        <div class="file-item">
            <div class="file-info">
                <div class="file-name">{name}</div>
                <div class="file-size">{size}</div>
            </div>
            <div style="padding: 20px; background: #f5f5f5; margin: 10px 0; border: 1px solid #333;">
                File preview not available
            </div>
            <a href="{link}" download class="download-btn">Download</a>
        </div>
        '''

def generate_index_html(users_data, users_config):
    """Generate the main index.html with login and file views."""
    
    # Create password hash mapping for frontend
    user_hashes = {}
    for username, config in users_config.items():
        user_hashes[username] = config.get('password_hash', '')
    
    # Create file data for each user (sorted by type then name)
    # Then XOR-encrypt each user's file list with their password hash
    user_files_encrypted = {}
    for username, files in users_data.items():
        if isinstance(files, list):
            sorted_files = sorted(files, key=lambda f: (f.get('folder', ''), f.get('category', 'other'), f.get('name', '')))
        else:
            sorted_files = []
        plaintext = json.dumps(sorted_files)
        key = user_hashes.get(username, '')
        if key:
            # XOR encrypt the JSON string with the password hash
            key_bytes = key.encode('utf-8')
            plain_bytes = plaintext.encode('utf-8')
            encrypted = bytes([plain_bytes[i] ^ key_bytes[i % len(key_bytes)] for i in range(len(plain_bytes))])
            user_files_encrypted[username] = base64.b64encode(encrypted).decode('ascii')
        else:
            user_files_encrypted[username] = ''
    
    user_hashes_json = json.dumps(user_hashes)
    user_files_json = json.dumps(user_files_encrypted)
    
    # CSS as a separate string to avoid f-string hash issues
    css = """        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        html, body {
            height: 100%;
        }

        body {
            font-family: 'Courier New', Courier, monospace;
            background: #fafafa;
            color: #333;
            padding: 20px;
            line-height: 1.6;
            text-transform: lowercase;
            font-size: 15px;
        }

        .container {
            max-width: 900px;
            margin: 0 auto;
            padding: 20px;
            overflow-x: hidden;
        }

        .login-section {
            max-width: 340px;
            margin: 0 auto;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            min-height: calc(100vh - 120px);
        }

        .login-section.hidden {
            display: none;
        }

        h1 {
            color: #333;
            margin-bottom: 30px;
            font-size: 20px;
            font-weight: 400;
            letter-spacing: 2px;
        }

        .form-group {
            margin-bottom: 18px;
            width: 100%;
        }

        label {
            display: block;
            color: #999;
            margin-bottom: 6px;
            font-size: 14px;
            letter-spacing: 1px;
        }

        input[type="text"],
        input[type="password"] {
            width: 100%;
            padding: 10px 0;
            background: transparent;
            border: none;
            border-bottom: 1px solid #ddd;
            color: #333;
            font-family: 'Courier New', Courier, monospace;
            font-size: 15px;
        }

        input[type="text"]:focus,
        input[type="password"]:focus {
            outline: none;
            border-bottom-color: #333;
        }

        button {
            width: 100%;
            padding: 10px;
            background: #333;
            color: #fafafa;
            border: none;
            font-size: 14px;
            font-family: 'Courier New', Courier, monospace;
            font-weight: 400;
            cursor: pointer;
            letter-spacing: 2px;
            margin-top: 8px;
        }

        button:hover {
            background: #555;
        }

        .error {
            color: #c44;
            font-size: 13px;
            margin-top: 12px;
        }

        .files-section {
            display: none;
        }

        .files-section.active {
            display: block;
        }

        .user-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 40px;
            padding-bottom: 20px;
            border-bottom: 1px solid #e0e0e0;
        }

        .welcome-text {
            color: #999;
            font-size: 16px;
            letter-spacing: 1px;
        }

        .logout-btn {
            width: auto;
            padding: 6px 16px;
            background: transparent;
            color: #999;
            border: 1px solid #ddd;
            font-size: 14px;
            margin-top: 0;
        }

        .logout-btn:hover {
            color: #333;
            border-color: #333;
            background: transparent;
        }

        .files-list {
            list-style: none;
        }

        .file-item {
            padding: 30px 0;
            border-bottom: 1px solid #eee;
        }

        .file-item:last-child {
            border-bottom: none;
        }

        .file-info {
            margin-bottom: 15px;
        }

        .file-name {
            color: #333;
            font-weight: bold;
            font-size: 16px;
            margin-bottom: 4px;
        }

        .file-size {
            color: #aaa;
            font-size: 13px;
        }

        .download-btn {
            display: inline-block;
            margin-top: 10px;
            padding: 8px 16px;
            background: #333;
            color: #fafafa;
            text-decoration: none;
            font-size: 13px;
            letter-spacing: 1px;
        }

        .download-btn:hover {
            background: #555;
        }

        .no-files {
            color: #aaa;
            text-align: center;
            padding: 40px 20px;
        }

        a {
            color: #333;
            text-decoration: none;
        }

        .file-table {
            width: 100%;
            border-collapse: collapse;
        }

        .file-row {
            cursor: default;
            border-bottom: 1px solid #eee;
        }

        .file-row:hover {
            background: #f0f0f0;
        }

        .file-row td {
            padding: 12px 8px;
            font-size: 14px;
        }

        .file-row .col-icon {
            width: 100px;
            padding-right: 0;
            text-transform: none;
            white-space: nowrap;
        }

        .file-row .col-icon svg {
            width: 18px;
            height: 18px;
            vertical-align: middle;
            fill: none;
            stroke: #999;
            stroke-width: 1.5;
            stroke-linecap: round;
            stroke-linejoin: round;
            margin-right: 6px;
        }

        .file-row .col-icon .type-label {
            color: #999;
            font-size: 12px;
            vertical-align: middle;
        }

        .file-row .col-icon .thumb {
            width: 28px;
            height: 28px;
            object-fit: cover;
            border-radius: 3px;
            vertical-align: middle;
            margin-right: 6px;
            background: #f0f0f0;
        }

        .file-row .col-name {
            color: #333;
        }

        .file-row .col-size {
            color: #aaa;
            text-align: right;
            width: 90px;
            font-size: 13px;
        }

        .file-row .col-actions {
            text-align: right;
            white-space: nowrap;
            width: 260px;
        }

        .action-btn {
            display: inline-block;
            padding: 5px 12px;
            font-size: 12px;
            font-family: 'Courier New', Courier, monospace;
            color: #999;
            border: 1px solid #ddd;
            background: transparent;
            text-decoration: none;
            cursor: pointer;
            letter-spacing: 1px;
            margin-left: 6px;
            width: auto;
            margin-top: 0;
        }

        .action-btn:hover {
            color: #333;
            border-color: #333;
            background: transparent;
        }

        .detail-view {
            display: none;
        }

        .detail-view.active {
            display: block;
        }

        .back-btn {
            width: auto;
            display: inline-block;
            padding: 6px 16px;
            background: transparent;
            color: #999;
            border: 1px solid #ddd;
            font-size: 14px;
            margin-bottom: 24px;
            margin-top: 0;
        }

        .back-btn:hover {
            color: #333;
            border-color: #333;
            background: transparent;
        }

        .detail-header {
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 4px;
        }

        .detail-header svg {
            width: 20px;
            height: 20px;
            fill: none;
            stroke: #999;
            stroke-width: 1.5;
            stroke-linecap: round;
            stroke-linejoin: round;
            flex-shrink: 0;
        }

        .detail-name {
            font-size: 18px;
            color: #333;
        }

        .detail-meta {
            font-size: 13px;
            color: #aaa;
            margin-bottom: 20px;
        }

        .preview-area {
            margin: 20px 0;
        }

        .preview-area video,
        .preview-area audio {
            width: 100%;
            max-width: 700px;
        }

        .preview-area img {
            max-width: 700px;
            width: 100%;
        }

        .preview-area iframe {
            width: 100%;
            max-width: 700px;
            height: 500px;
            border: 1px solid #eee;
        }

        .preview-area iframe.audio-frame {
            height: 80px;
            border-radius: 4px;
            border: 1px solid #e0e0e0;
            background: #f5f5f5;
        }

        .no-preview {
            padding: 40px;
            color: #aaa;
            text-align: center;
        }

        .folder-row {
            cursor: pointer;
        }

        .folder-heading {
            font-size: 14px;
            color: #999;
            letter-spacing: 1px;
            padding: 18px 0 8px 0;
            border-bottom: 1px solid #e0e0e0;
            margin-top: 12px;
        }

        .folder-heading svg {
            width: 16px;
            height: 16px;
            fill: none;
            stroke: #999;
            stroke-width: 1.5;
            stroke-linecap: round;
            stroke-linejoin: round;
            vertical-align: middle;
            margin-right: 6px;
        }

        .folder-heading span {
            vertical-align: middle;
        }

        .back-folder-btn {
            display: inline-block;
            margin: 10px 0 16px 0;
            font-size: 13px;
            color: #999;
        }

        .back-folder-btn:hover {
            color: #333;
        }

        .detail-nav {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-top: 20px;
            padding-top: 16px;
            border-top: 1px solid #eee;
        }

        .nav-btn {
            display: inline-block;
            padding: 6px 16px;
            background: transparent;
            color: #999;
            border: 1px solid #ddd;
            font-size: 13px;
            font-family: 'Courier New', Courier, monospace;
            cursor: pointer;
            letter-spacing: 1px;
            width: auto;
            margin-top: 0;
        }

        .nav-btn:hover {
            color: #333;
            border-color: #333;
            background: transparent;
        }

        .nav-btn.disabled {
            opacity: 0.3;
            cursor: default;
            pointer-events: none;
        }

        .nav-counter {
            color: #aaa;
            font-size: 12px;
        }

        @media (max-width: 700px) {
            body {
                padding: 10px;
                font-size: 14px;
            }

            .container {
                padding: 12px;
            }

            .user-header {
                margin-bottom: 20px;
                padding-bottom: 12px;
            }

            .file-table,
            .file-table tbody,
            .file-table tr,
            .file-table td {
                display: block;
                width: 100%;
            }

            .file-row {
                padding: 14px 0;
                border-bottom: 1px solid #eee;
            }

            .file-row td {
                padding: 2px 0;
            }

            .file-row .col-icon {
                width: auto;
                margin-bottom: 2px;
            }

            .file-row .col-name {
                font-size: 14px;
                word-break: break-word;
            }

            .file-row .col-size {
                text-align: left;
                width: auto;
                font-size: 12px;
                margin-bottom: 6px;
            }

            .file-row .col-actions {
                text-align: left;
                width: auto;
                white-space: normal;
            }

            .action-btn {
                margin-left: 0;
                margin-right: 6px;
                margin-top: 4px;
            }

            .detail-name {
                font-size: 15px;
                word-break: break-word;
            }

            .detail-header {
                flex-wrap: wrap;
            }

            .preview-area iframe {
                height: 300px;
            }

            .preview-area iframe.audio-frame {
                height: 80px;
            }

            .preview-area img {
                max-width: 100%;
            }

            .download-btn {
                font-size: 12px;
                padding: 8px 14px;
            }
        }
"""
    
    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>File Share</title>
    <style>
{css}
    </style>
</head>
<body>
    <div class="container">
        <div class="login-section" id="loginSection">
            <h1>login</h1>
            
            <div class="form-group">
                <label>username</label>
                <input type="text" id="username" autocomplete="username">
            </div>
            
            <div class="form-group">
                <label>password</label>
                <input type="password" id="password" autocomplete="current-password">
            </div>
            
            <button onclick="login()">login</button>
            <div class="error" id="loginError"></div>
        </div>

        <div class="files-section" id="filesSection">
            <div class="user-header">
                <div class="welcome-text"><span id="displayName"></span> file share</div>
                <button class="logout-btn" onclick="logout()">logout</button>
            </div>
            
            <div class="files-list" id="filesGrid"></div>
        </div>

        <div class="detail-view" id="detailView">
            <button class="back-btn" onclick="backToList()">← back</button>
            <div class="detail-header">
                <span id="detailIcon"></span>
                <div class="detail-name" id="detailFileName"></div>
            </div>
            <div class="detail-meta" id="detailFileMeta"></div>
            <div class="preview-area" id="previewArea"></div>
            <a href="#" id="downloadBtn" class="download-btn" download>download</a>
            <div class="detail-nav" id="detailNav">
                <button class="nav-btn" id="prevBtn" onclick="navFile(-1)">← prev</button>
                <span class="nav-counter" id="navCounter"></span>
                <button class="nav-btn" id="nextBtn" onclick="navFile(1)">next →</button>
            </div>
        </div>
    </div>

    <script>
        const USER_HASHES = {user_hashes_json};
        const USER_FILES_ENC = {user_files_json};

        function xorDecrypt(b64, key) {{
            const raw = atob(b64);
            let out = '';
            for (let i = 0; i < raw.length; i++) {{
                out += String.fromCharCode(raw.charCodeAt(i) ^ key.charCodeAt(i % key.length));
            }}
            return out;
        }}

        function fileIcon(cat) {{
            const icons = {{
                video: '<svg viewBox="0 0 24 24"><polygon points="23 7 16 12 23 17 23 7"></polygon><rect x="1" y="5" width="15" height="14" rx="2" ry="2"></rect></svg>',
                audio: '<svg viewBox="0 0 24 24"><path d="M9 18V5l12-2v13"></path><circle cx="6" cy="18" r="3"></circle><circle cx="18" cy="16" r="3"></circle></svg>',
                image: '<svg viewBox="0 0 24 24"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect><circle cx="8.5" cy="8.5" r="1.5"></circle><polyline points="21 15 16 10 5 21"></polyline></svg>',
                pdf: '<svg viewBox="0 0 24 24"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line></svg>',
                gdoc: '<svg viewBox="0 0 24 24"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line><line x1="10" y1="9" x2="8" y2="9"></line></svg>',
                gsheet: '<svg viewBox="0 0 24 24"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect><line x1="3" y1="9" x2="21" y2="9"></line><line x1="3" y1="15" x2="21" y2="15"></line><line x1="9" y1="3" x2="9" y2="21"></line><line x1="15" y1="3" x2="15" y2="21"></line></svg>',
                gslides: '<svg viewBox="0 0 24 24"><rect x="2" y="3" width="20" height="14" rx="2" ry="2"></rect><line x1="8" y1="21" x2="16" y2="21"></line><line x1="12" y1="17" x2="12" y2="21"></line></svg>',
                gform: '<svg viewBox="0 0 24 24"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><circle cx="8" cy="13" r="1"></circle><circle cx="8" cy="17" r="1"></circle><line x1="11" y1="13" x2="16" y2="13"></line><line x1="11" y1="17" x2="16" y2="17"></line></svg>',
                gdrawing: '<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"></circle><path d="M8 14s1.5 2 4 2 4-2 4-2"></path><line x1="9" y1="9" x2="9.01" y2="9"></line><line x1="15" y1="9" x2="15.01" y2="9"></line></svg>',
                other: '<svg viewBox="0 0 24 24"><path d="M13 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z"></path><polyline points="13 2 13 9 20 9"></polyline></svg>'
            }};
            return icons[cat] || icons.other;
        }}

        let currentFiles = [];

        async function sha256(message) {{
            const msgBuffer = new TextEncoder().encode(message);
            const hashBuffer = await crypto.subtle.digest('SHA-256', msgBuffer);
            const hashArray = Array.from(new Uint8Array(hashBuffer));
            const hashHex = hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
            return hashHex;
        }}

        async function login() {{
            const username = document.getElementById('username').value.trim().toLowerCase();
            const password = document.getElementById('password').value;
            const errorDiv = document.getElementById('loginError');
            
            if (!username || !password) {{
                errorDiv.textContent = 'please enter username and password';
                return;
            }}

            if (!(username in USER_HASHES)) {{
                errorDiv.textContent = 'invalid username or password';
                return;
            }}

            const passwordHash = await sha256(password);
            if (passwordHash !== USER_HASHES[username]) {{
                errorDiv.textContent = 'invalid username or password';
                return;
            }}

            // Decrypt file data using the password hash
            const enc = USER_FILES_ENC[username] || '';
            let decrypted = [];
            if (enc) {{
                try {{
                    decrypted = JSON.parse(xorDecrypt(enc, passwordHash));
                }} catch(e) {{
                    errorDiv.textContent = 'error decrypting files';
                    return;
                }}
            }}
            sessionStorage.setItem('userFiles', JSON.stringify(decrypted));
            sessionStorage.setItem('username', username);
            sessionStorage.setItem('displayName', username.charAt(0).toUpperCase() + username.slice(1));
            showFiles();
        }}

        function logout() {{
            sessionStorage.clear();
            currentFiles = [];
            document.getElementById('loginSection').classList.remove('hidden');
            document.getElementById('filesSection').classList.remove('active');
            document.getElementById('detailView').classList.remove('active');
            document.getElementById('username').value = '';
            document.getElementById('password').value = '';
            document.getElementById('loginError').textContent = '';
        }}

        function showFiles() {{
            const username = sessionStorage.getItem('username');
            if (!username) return;

            document.getElementById('loginSection').classList.add('hidden');
            document.getElementById('filesSection').classList.add('active');
            document.getElementById('detailView').classList.remove('active');
            document.getElementById('displayName').textContent = sessionStorage.getItem('displayName');

            try {{
                currentFiles = JSON.parse(sessionStorage.getItem('userFiles') || '[]');
            }} catch(e) {{
                currentFiles = [];
            }}
            currentView = 'root';
            currentFolder = '';
            renderFileList();
        }}

        const folderSvg = '<svg viewBox="0 0 24 24"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"></path></svg>';
        const googleNativeTypes = ['gdoc', 'gsheet', 'gslides', 'gform', 'gdrawing'];
        const categoryLabel = {{gdoc: 'document', gsheet: 'spreadsheet', gslides: 'slides', gform: 'form', gdrawing: 'drawing'}};
        function catLabel(cat) {{ return categoryLabel[cat] || cat; }}
        function downloadUrl(f) {{
            if (googleNativeTypes.includes(f.category)) {{
                const base = f.category === 'gsheet' ? 'spreadsheets' : f.category === 'gslides' ? 'presentation' : f.category === 'gdoc' ? 'document' : 'document';
                return 'https://docs.google.com/' + base + '/d/' + f.id + '/export?format=pdf';
            }}
            return 'https://drive.google.com/uc?export=download&id=' + f.id;
        }}
        let currentView = 'root';
        let currentFolder = '';
        let levelFiles = [];
        let folderNames = [];

        function renderFileList() {{
            const grid = document.getElementById('filesGrid');
            if (!currentFiles.length) {{
                grid.innerHTML = '<p class="no-files">no files available</p>';
                return;
            }}

            const prefix = currentFolder ? currentFolder + '/' : '';

            // Files directly at this level
            levelFiles = currentFolder
                ? currentFiles.filter(f => f.folder === currentFolder)
                : currentFiles.filter(f => !f.folder);

            // Subfolders at this level
            const subfolderSet = new Set();
            currentFiles.forEach(f => {{
                if (!f.folder) return;
                if (currentFolder) {{
                    if (f.folder.startsWith(prefix) && f.folder !== currentFolder) {{
                        const rest = f.folder.slice(prefix.length);
                        const next = rest.split('/')[0];
                        if (next) subfolderSet.add(next);
                    }}
                }} else {{
                    subfolderSet.add(f.folder.split('/')[0]);
                }}
            }});
            const subfolders = [...subfolderSet].sort();
            folderNames = subfolders;

            let html = '';

            // Back button + heading when inside a folder
            if (currentFolder) {{
                html += '<div class="folder-heading">' + folderSvg + '<span>' + currentFolder + '</span></div>';
                html += '<a class="action-btn back-folder-btn" href="#" onclick="event.preventDefault();goBack()">\u2190 back</a>';
            }}

            // Render subfolders
            if (subfolders.length) {{
                html += '<table class="file-table">';
                subfolders.forEach((name, fi) => {{
                    const fullPath = currentFolder ? currentFolder + '/' + name : name;
                    const count = currentFiles.filter(f => f.folder && (f.folder === fullPath || f.folder.startsWith(fullPath + '/'))).length;
                    html += '<tr class="file-row folder-row" onclick="openFolder(' + fi + ')">';
                    html += '<td class="col-icon">' + folderSvg + '<span class="type-label">folder</span></td>';
                    html += '<td class="col-name">' + name + '</td>';
                    html += '<td class="col-size">' + count + ' file' + (count !== 1 ? 's' : '') + '</td>';
                    html += '<td class="col-actions">';
                    html += '<a class="action-btn" href="#" onclick="event.stopPropagation();event.preventDefault();openFolder(' + fi + ')">view folder contents</a>';
                    html += '</td>';
                    html += '</tr>';
                }});
                html += '</table>';
            }}

            // Render files at this level
            if (levelFiles.length) {{
                html += '<table class="file-table">';
                levelFiles.forEach((f, i) => {{
                    const gi = currentFiles.indexOf(f);
                    html += '<tr class="file-row">';
                    if (f.category === 'image') {{
                        html += '<td class="col-icon">' + fileIcon(f.category) + '<img class="thumb" src="https://lh3.googleusercontent.com/d/' + f.id + '=s56" alt=""><span class="type-label">' + catLabel(f.category) + '</span></td>';
                    }} else {{
                        html += '<td class="col-icon">' + fileIcon(f.category) + '<span class="type-label">' + catLabel(f.category) + '</span></td>';
                    }}
                    html += '<td class="col-name">' + f.name + '</td>';
                    html += '<td class="col-size">' + f.size + '</td>';
                    html += '<td class="col-actions">';
                    html += '<a class="action-btn" href="#" onclick="event.preventDefault();openFileDetail(' + gi + ',' + i + ')">view file</a>';
                    html += '<a class="action-btn" href="' + downloadUrl(f) + '" download>download file</a>';
                    html += '</td>';
                    html += '</tr>';
                }});
                html += '</table>';
            }}

            if (!subfolders.length && !levelFiles.length) {{
                html += '<p class="no-files">' + (currentFolder ? 'no files in this folder' : 'no files available') + '</p>';
            }}
            grid.innerHTML = html;
        }}

        function openFolder(idx) {{
            const name = folderNames[idx];
            if (!name) return;
            currentFolder = currentFolder ? currentFolder + '/' + name : name;
            currentView = 'folder';
            history.pushState({{view: 'folder', folder: currentFolder}}, '');
            renderFileList();
        }}

        function goBack() {{
            if (!currentFolder) return;
            const parts = currentFolder.split('/');
            parts.pop();
            currentFolder = parts.join('/');
            currentView = currentFolder ? 'folder' : 'root';
            history.pushState({{view: currentView, folder: currentFolder}}, '');
            renderFileList();
        }}

        let currentIndex = -1;
        let navContext = 'none';

        function openFileDetail(globalIdx, levelIdx) {{
            if (currentFolder && levelFiles.length > 1) {{
                navContext = 'folder';
                currentIndex = levelIdx;
            }} else {{
                navContext = 'none';
            }}
            showDetail(currentFiles[globalIdx]);
        }}

        function showDetail(file) {{
            if (!file) return;
            history.pushState({{view: 'detail'}}, '');

            document.getElementById('filesSection').classList.remove('active');
            const detail = document.getElementById('detailView');
            detail.classList.add('active');

            document.getElementById('detailFileName').textContent = file.name;
            document.getElementById('detailIcon').innerHTML = fileIcon(file.category);
            const folderLabel = file.folder ? file.folder + ' \u00b7 ' : '';
            document.getElementById('detailFileMeta').textContent = folderLabel + catLabel(file.category) + ' \u00b7 ' + file.size;

            const preview = document.getElementById('previewArea');
            const isNative = googleNativeTypes.includes(file.category);
            const dlLink = downloadUrl(file);

            if (isNative) {{
                const embedBase = file.category === 'gsheet' ? 'https://docs.google.com/spreadsheets/d/' : file.category === 'gslides' ? 'https://docs.google.com/presentation/d/' : file.category === 'gdoc' ? 'https://docs.google.com/document/d/' : file.category === 'gform' ? 'https://docs.google.com/forms/d/' : 'https://docs.google.com/drawings/d/';
                preview.innerHTML = '<iframe src="' + embedBase + file.id + '/preview"></iframe>';
            }} else if (file.category === 'video') {{
                preview.innerHTML = '<iframe src="https://drive.google.com/file/d/' + file.id + '/preview" allow="autoplay"></iframe>';
            }} else if (file.category === 'audio') {{
                preview.innerHTML = '<iframe class="audio-frame" src="https://drive.google.com/file/d/' + file.id + '/preview"></iframe>';
            }} else if (file.category === 'image') {{
                preview.innerHTML = '<img src="https://lh3.googleusercontent.com/d/' + file.id + '" alt="' + file.name + '" loading="lazy">';
            }} else if (file.category === 'pdf') {{
                preview.innerHTML = '<iframe src="https://drive.google.com/file/d/' + file.id + '/preview"></iframe>';
            }} else {{
                preview.innerHTML = '<div class="no-preview">preview not available</div>';
            }}

            document.getElementById('downloadBtn').href = dlLink;
            document.getElementById('downloadBtn').textContent = isNative ? 'download as pdf' : 'download';

            // Show/hide prev/next nav
            const nav = document.getElementById('detailNav');
            if (navContext === 'folder' && levelFiles.length > 1) {{
                nav.style.display = 'flex';
                document.getElementById('prevBtn').classList.toggle('disabled', currentIndex <= 0);
                document.getElementById('nextBtn').classList.toggle('disabled', currentIndex >= levelFiles.length - 1);
                document.getElementById('navCounter').textContent = (currentIndex + 1) + ' / ' + levelFiles.length;
            }} else {{
                nav.style.display = 'none';
            }}
        }}

        function navFile(delta) {{
            const newIndex = currentIndex + delta;
            if (newIndex >= 0 && newIndex < levelFiles.length) {{
                currentIndex = newIndex;
                showDetail(levelFiles[newIndex]);
            }}
        }}

        function backToList() {{
            document.getElementById('detailView').classList.remove('active');
            document.getElementById('filesSection').classList.add('active');
            if (currentView === 'folder') {{
                renderFileList();
            }}
        }}

        window.addEventListener('popstate', function(e) {{
            const detail = document.getElementById('detailView');
            if (detail.classList.contains('active')) {{
                detail.classList.remove('active');
                document.getElementById('filesSection').classList.add('active');
                renderFileList();
            }} else if (e.state && e.state.view === 'folder') {{
                currentView = 'folder';
                currentFolder = e.state.folder || '';
                renderFileList();
            }} else {{
                currentView = 'root';
                currentFolder = '';
                renderFileList();
            }}
        }});

        if (sessionStorage.getItem('username')) {{
            showFiles();
        }}

        document.getElementById('password').addEventListener('keypress', function(event) {{
            if (event.key === 'Enter') {{
                login();
            }}
        }});
    </script>
</body>
</html>'''
    
    return html

def generate_site(users_data_file, users_config_file, output_dir):
    """Generate the static site."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Load data
    try:
        with open(users_data_file, 'r') as f:
            users_data = json.load(f)
    except FileNotFoundError:
        print(f"Error: {users_data_file} not found", file=sys.stderr)
        users_data = {}
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in {users_data_file}: {e}", file=sys.stderr)
        users_data = {}
    
    try:
        with open(users_config_file, 'r') as f:
            users_config = json.load(f)
    except FileNotFoundError:
        print(f"Error: {users_config_file} not found", file=sys.stderr)
        users_config = {}
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in {users_config_file}: {e}", file=sys.stderr)
        users_config = {}
    
    # Generate HTML
    html = generate_index_html(users_data, users_config)
    
    # Write index.html
    index_path = output_dir / 'index.html'
    with open(index_path, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"✓ Generated {index_path}", file=sys.stderr)

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python generate_site.py <users_data.json> <users_config.json> <output_dir>", file=sys.stderr)
        sys.exit(1)
    
    generate_site(sys.argv[1], sys.argv[2], sys.argv[3])
