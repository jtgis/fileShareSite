#!/usr/bin/env python3
"""
Generate static HTML site from user data and file listings.
"""
import json
import sys
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
            <video controls style="width: 100%; max-width: 600px; margin: 10px 0;">
                <source src="{link}" type="video/mp4">
                Your browser does not support the video element.
            </video>
        </div>
        '''
    elif file['category'] == 'audio':
        return f'''
        <div class="file-item">
            <div class="file-info">
                <div class="file-name">{name}</div>
                <div class="file-size">{size}</div>
            </div>
            <audio controls style="width: 100%; max-width: 600px; margin: 10px 0;">
                <source src="{link}" type="audio/mpeg">
                Your browser does not support the audio element.
            </audio>
        </div>
        '''
    elif file['category'] == 'image':
        return f'''
        <div class="file-item">
            <div class="file-info">
                <div class="file-name">{name}</div>
                <div class="file-size">{size}</div>
            </div>
            <img src="{link}" alt="{name}" style="max-width: 600px; width: 100%; margin: 10px 0; border: 1px solid #ddd;" loading="lazy">
        </div>
        '''
    elif file['category'] == 'pdf':
        return f'''
        <div class="file-item">
            <div class="file-info">
                <div class="file-name">{name}</div>
                <div class="file-size">{size}</div>
            </div>
            <a href="{link}" target="_blank">Open PDF</a>
        </div>
        '''
    else:
        return f'''
        <div class="file-item">
            <div class="file-info">
                <div class="file-name">{name}</div>
                <div class="file-size">{size}</div>
            </div>
            <a href="{link}" download>Download</a>
        </div>
        '''

def generate_index_html(users_data, users_config):
    """Generate the main index.html with login and file views."""
    
    # Create password hash mapping for frontend
    user_hashes = {}
    for username, config in users_config.items():
        user_hashes[username] = config.get('password_hash', '')
    
    # Create file listings for each user
    user_files_html = {}
    for username, files in users_data.items():
        if isinstance(files, list):
            files_html = ''.join(render_file_card(f) for f in files)
        else:
            files_html = '<p class="no-files">No files available</p>'
        user_files_html[username] = files_html if files_html else '<p class="no-files">No files available</p>'
    
    user_hashes_json = json.dumps(user_hashes)
    user_files_json = json.dumps(user_files_html)
    
    # CSS as a separate string to avoid f-string hash issues
    css = """        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: Arial, sans-serif;
            background: #f5f5f5;
            padding: 20px;
        }

        .container {
            background: white;
            max-width: 900px;
            margin: 0 auto;
            padding: 30px;
            border: 1px solid #ddd;
        }

        .login-section {
            max-width: 400px;
            margin: 0 auto;
        }

        .login-section.hidden {
            display: none;
        }

        h1 {
            color: #333;
            margin-bottom: 20px;
            font-size: 24px;
        }

        .form-group {
            margin-bottom: 15px;
        }

        label {
            display: block;
            color: #333;
            margin-bottom: 5px;
            font-size: 14px;
        }

        input[type="text"],
        input[type="password"] {
            width: 100%;
            padding: 10px;
            border: 1px solid #ddd;
            font-size: 14px;
        }

        input[type="text"]:focus,
        input[type="password"]:focus {
            outline: none;
            border-color: #333;
        }

        button {
            width: 100%;
            padding: 10px;
            background: #333;
            color: white;
            border: none;
            font-size: 14px;
            cursor: pointer;
        }

        .error {
            color: red;
            font-size: 13px;
            margin-top: 10px;
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
            margin-bottom: 30px;
            padding-bottom: 15px;
            border-bottom: 1px solid #ddd;
        }

        .welcome-text {
            color: #333;
            font-size: 16px;
        }

        .logout-btn {
            width: auto;
            padding: 8px 16px;
            background: #666;
            font-size: 13px;
        }

        .files-list {
            list-style: none;
        }

        .file-item {
            padding: 20px 0;
            border-bottom: 1px solid #eee;
        }

        .file-item:last-child {
            border-bottom: none;
        }

        .file-info {
            margin-bottom: 10px;
        }

        .file-name {
            color: #333;
            font-weight: bold;
            font-size: 16px;
            margin-bottom: 5px;
        }

        .file-size {
            color: #666;
            font-size: 13px;
        }

        .no-files {
            color: #666;
            text-align: center;
            padding: 40px 20px;
        }

        a {
            color: #0066cc;
            text-decoration: none;
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
            <h1>Login</h1>
            
            <div class="form-group">
                <label>Username</label>
                <input type="text" id="username" autocomplete="username">
            </div>
            
            <div class="form-group">
                <label>Password</label>
                <input type="password" id="password" autocomplete="current-password">
            </div>
            
            <button onclick="login()">Login</button>
            <div class="error" id="loginError"></div>
        </div>

        <div class="files-section" id="filesSection">
            <div class="user-header">
                <div class="welcome-text">Welcome, <span id="displayName"></span></div>
                <button class="logout-btn" onclick="logout()">Logout</button>
            </div>
            
            <div class="files-list" id="filesGrid"></div>
        </div>
    </div>

    <script>
        const USER_HASHES = {user_hashes_json};
        const USER_FILES = {user_files_json};

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
                errorDiv.textContent = 'Please enter username and password';
                return;
            }}

            if (!(username in USER_HASHES)) {{
                errorDiv.textContent = 'Invalid username or password';
                return;
            }}

            const passwordHash = await sha256(password);
            if (passwordHash !== USER_HASHES[username]) {{
                errorDiv.textContent = 'Invalid username or password';
                return;
            }}

            sessionStorage.setItem('username', username);
            sessionStorage.setItem('displayName', username.charAt(0).toUpperCase() + username.slice(1));
            showFiles();
        }}

        function logout() {{
            sessionStorage.clear();
            document.getElementById('loginSection').classList.remove('hidden');
            document.getElementById('filesSection').classList.remove('active');
            document.getElementById('username').value = '';
            document.getElementById('password').value = '';
            document.getElementById('loginError').textContent = '';
        }}

        function showFiles() {{
            const username = sessionStorage.getItem('username');
            if (!username) return;

            document.getElementById('loginSection').classList.add('hidden');
            document.getElementById('filesSection').classList.add('active');
            document.getElementById('displayName').textContent = sessionStorage.getItem('displayName');

            const filesHtml = USER_FILES[username] || '<p class="no-files">No files available</p>';
            document.getElementById('filesGrid').innerHTML = filesHtml;
        }}

        // Check if already logged in
        if (sessionStorage.getItem('username')) {{
            showFiles();
        }}

        // Allow Enter key to submit login form
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
