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
        <div class="file-card video-card">
            <div class="file-header">
                <span class="file-icon">{icon}</span>
                <span class="file-name">{name}</span>
            </div>
            <iframe src="{link}" width="100%" height="200" frameborder="0" allowfullscreen style="border-radius: 8px; margin: 10px 0;"></iframe>
            <div class="file-size">{size}</div>
            <a href="{link}" target="_blank" class="file-link">Open in New Tab</a>
        </div>
        '''
    elif file['category'] == 'audio':
        return f'''
        <div class="file-card audio-card">
            <div class="file-header">
                <span class="file-icon">{icon}</span>
                <span class="file-name">{name}</span>
            </div>
            <div class="file-size">{size}</div>
            <audio controls style="width: 100%; margin: 10px 0;">
                <source src="{link}" type="audio/mpeg">
                Your browser does not support the audio element.
            </audio>
            <a href="{link}" download class="file-link">Download</a>
        </div>
        '''
    elif file['category'] == 'image':
        return f'''
        <div class="file-card image-card">
            <div class="file-header">
                <span class="file-icon">{icon}</span>
                <span class="file-name">{name}</span>
            </div>
            <img src="{link}" alt="{name}" class="file-image" loading="lazy">
            <div class="file-size">{size}</div>
            <a href="{link}" target="_blank" class="file-link">View Full Size</a>
        </div>
        '''
    elif file['category'] == 'pdf':
        return f'''
        <div class="file-card pdf-card">
            <div class="file-header">
                <span class="file-icon">{icon}</span>
                <span class="file-name">{name}</span>
            </div>
            <iframe src="{link}" width="100%" height="300" frameborder="0" style="border-radius: 8px; margin: 10px 0;"></iframe>
            <div class="file-size">{size}</div>
            <a href="{link}" target="_blank" class="file-link">Open in New Tab</a>
        </div>
        '''
    else:
        return f'''
        <div class="file-card other-card">
            <div class="file-header">
                <span class="file-icon">{icon}</span>
                <span class="file-name">{name}</span>
            </div>
            <div class="file-size">{size}</div>
            <a href="{link}" download class="file-link">Download</a>
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
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }

        .container {
            background: white;
            border-radius: 12px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
            max-width: 1200px;
            width: 100%;
            padding: 40px;
            animation: fadeIn 0.5s ease-in;
        }

        @keyframes fadeIn {
            from {
                opacity: 0;
                transform: translateY(10px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        .login-section {
            display: flex;
            flex-direction: column;
            gap: 20px;
            max-width: 400px;
            margin: 0 auto;
        }

        .login-section.hidden {
            display: none;
        }

        h1 {
            color: #333;
            margin-bottom: 30px;
            text-align: center;
            font-size: 28px;
        }

        .form-group {
            display: flex;
            flex-direction: column;
            gap: 8px;
        }

        label {
            color: #555;
            font-weight: 600;
            font-size: 14px;
        }

        input[type="text"],
        input[type="password"] {
            padding: 12px 16px;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            font-size: 16px;
            transition: border-color 0.3s;
        }

        input[type="text"]:focus,
        input[type="password"]:focus {
            outline: none;
            border-color: #667eea;
        }

        button {
            padding: 12px 24px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.2s, box-shadow 0.2s;
        }

        button:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 20px rgba(102, 126, 234, 0.4);
        }

        button:active {
            transform: translateY(0);
        }

        .error {
            color: #e74c3c;
            font-size: 14px;
            text-align: center;
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
            flex-wrap: wrap;
            gap: 15px;
        }

        .welcome-text {
            color: #333;
            font-size: 18px;
            font-weight: 600;
        }

        .logout-btn {
            padding: 8px 16px;
            background: #95a5a6;
            font-size: 14px;
        }

        .logout-btn:hover {
            box-shadow: 0 5px 15px rgba(149, 165, 166, 0.4);
        }

        .files-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }

        @media (max-width: 768px) {
            .files-grid {
                grid-template-columns: 1fr;
            }
            
            .container {
                padding: 20px;
            }
            
            h1 {
                font-size: 22px;
                margin-bottom: 20px;
            }
        }

        .file-card {
            background: #f8f9fa;
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            padding: 16px;
            transition: all 0.3s ease;
            display: flex;
            flex-direction: column;
            gap: 12px;
        }

        .file-card:hover {
            box-shadow: 0 8px 16px rgba(0, 0, 0, 0.1);
            border-color: #667eea;
            transform: translateY(-4px);
        }

        .file-header {
            display: flex;
            align-items: center;
            gap: 10px;
            word-break: break-word;
        }

        .file-icon {
            font-size: 24px;
            flex-shrink: 0;
        }

        .file-name {
            color: #333;
            font-weight: 600;
            font-size: 14px;
            flex: 1;
        }

        .file-size {
            color: #888;
            font-size: 12px;
        }

        .file-image {
            max-width: 100%;
            height: auto;
            border-radius: 4px;
            max-height: 200px;
            object-fit: cover;
        }

        .file-link {
            display: inline-block;
            padding: 8px 12px;
            background: #667eea;
            color: white;
            text-decoration: none;
            border-radius: 4px;
            font-size: 12px;
            text-align: center;
            transition: background 0.3s;
        }

        .file-link:hover {
            background: #764ba2;
        }

        audio {
            width: 100%;
            height: 32px;
        }

        .no-files {
            color: #888;
            text-align: center;
            padding: 40px 20px;
            font-style: italic;
        }

        .footer {
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #e0e0e0;
            text-align: center;
            color: #888;
            font-size: 12px;
        }

        .footer a {
            color: #667eea;
            text-decoration: none;
        }

        .footer a:hover {
            text-decoration: underline;
        }"""
    
    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>File Share Site</title>
    <style>
{css}
    </style>
</head>
<body>
    <div class="container">
        <div class="login-section" id="loginSection">
            <h1>📁 File Share Site</h1>
            
            <div class="form-group">
                <label for="username">Username</label>
                <input type="text" id="username" placeholder="Enter username" autocomplete="username">
            </div>
            
            <div class="form-group">
                <label for="password">Password</label>
                <input type="password" id="password" placeholder="Enter password" autocomplete="current-password">
            </div>
            
            <button onclick="login()">Login</button>
            <div class="error" id="loginError"></div>
        </div>

        <div class="files-section" id="filesSection">
            <div class="user-header">
                <div class="welcome-text">👋 Welcome, <span id="displayName"></span>!</div>
                <button class="logout-btn" onclick="logout()">Logout</button>
            </div>
            
            <div class="files-grid" id="filesGrid"></div>
            
            <div class="footer">
                <p>If you have any issues, please contact us at <a href="mailto:support@example.com">support@example.com</a></p>
            </div>
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
