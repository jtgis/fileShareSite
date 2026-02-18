#!/usr/bin/env python3
"""
Generate static HTML site from user data and file listings.
"""
import json
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
            <div class="file-size">{size}</div>
            <a href="{link}" target="_blank" class="file-link">Open in Google Drive</a>
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
            <a href="{link}" target="_blank" class="file-link">Open in Google Drive</a>
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
            <a href="{link}" target="_blank" class="file-link">Open in Google Drive</a>
        </div>
        '''
    elif file['category'] == 'pdf':
        return f'''
        <div class="file-card pdf-card">
            <div class="file-header">
                <span class="file-icon">{icon}</span>
                <span class="file-name">{name}</span>
            </div>
            <div class="file-size">{size}</div>
            <a href="{link}" target="_blank" class="file-link">View PDF in Google Drive</a>
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
            <a href="{link}" target="_blank" class="file-link">Download from Google Drive</a>
        </div>
        '''

def generate_index_html(users_data, users_config):
    """Generate the main index.html with login and file views."""
    
    # Create password hash mapping for frontend
    user_hashes = {}
    for username, config in users_config.items():
        user_hashes[username] = config['password_hash']
    
    # Create file listings for each user
    user_files_html = {}
    for username, files in users_data.items():
        files_html = ''.join(render_file_card(f) for f in files)
        user_files_html[username] = files_html if files else '<p class="no-files">No files available</p>'
    
    user_hashes_json = json.dumps(user_hashes)
    user_files_json = json.dumps(user_files_html)
    
    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>File Share Site</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }}

        .container {{
            background: white;
            border-radius: 12px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
            max-width: 1200px;
            width: 100%;
            padding: 40px;
            animation: fadeIn 0.5s ease-in;
        }}

        @keyframes fadeIn {{
            from {{
                opacity: 0;
                transform: translateY(10px);
            }}
            to {{
                opacity: 1;
                transform: translateY(0);
            }}
        }}

        .login-section {{
            display: flex;
            flex-direction: column;
            gap: 20px;
            max-width: 400px;
            margin: 0 auto;
        }}

        .login-section.hidden {{
            display: none;
        }}

        h1 {{
            color: #333;
            margin-bottom: 30px;
            text-align: center;
            font-size: 28px;
        }}

        .form-group {{
            display: flex;
            flex-direction: column;
            gap: 8px;
        }}

        label {{
            color: #555;
            font-weight: 600;
            font-size: 14px;
        }}

        input[type="text"],
        input[type="password"] {{
            padding: 12px 16px;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            font-size: 16px;
            transition: border-color 0.3s;
        }}

        input[type="text"]:focus,
        input[type="password"]:focus {{
            outline: none;
            border-color: #667eea;
        }}

        button {{
            padding: 12px 24px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.2s, box-shadow 0.2s;
        }}

        button:hover {{
            transform: translateY(-2px);
            box-shadow: 0 10px 20px rgba(102, 126, 234, 0.4);
        }}

        button:active {{
            transform: translateY(0);
        }}

        .error {{
            color: #e74c3c;
            font-size: 14px;
            text-align: center;
        }}

        .files-section {{
            display: none;
        }}

        .files-section.active {{
            display: block;
        }}

        .user-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 30px;
            flex-wrap: wrap;
            gap: 15px;
        }}

        .welcome-text {{
            color: #333;
            font-size: 18px;
            font-weight: 600;
        }}

        .logout-btn {{
            padding: 8px 16px;
            background: #95a5a6;
            font-size: 14px;
        }}

        .logout-btn:hover {{
            box-shadow: 0 5px 15px rgba(149, 165, 166, 0.4);
        }}

        .files-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }}

        @media (max-width: 768px) {{
            .files-grid {{
                grid-template-columns: 1fr;
            }}
            
            .container {{
                padding: 20px;
            }}
            
            h1 {{
                font-size: 22px;
                margin-bottom: 20px;
            }}
        }}

        .file-card {{
            background: #f8f9fa;
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            padding: 16px;
            transition: all 0.3s ease;
            display: flex;
            flex-direction: column;
            gap: 12px;
        }}

        .file-card:hover {{
            box-shadow: 0 8px 16px rgba(0, 0, 0, 0.1);
            border-color: #667eea;
            transform: translateY(-4px);
        }}

        .file-header {{
            display: flex;
            align-items: center;
            gap: 10px;
            word-break: break-word;
        }}

        .file-icon {{
            font-size: 24px;
            flex-shrink: 0;
        }}

        .file-name {{
            color: #333;
            font-weight: 600;
            font-size: 14px;
            flex: 1;
        }}

        .file-size {{
            color: #888;
            font-size: 12px;
        }}

        .file-image {{
            max-width: 100%;
            height: auto;
            border-radius: 4px;
            max-height: 200px;
            object-fit: cover;
        }}

        .file-link {{
            display: inline-block;
            padding: 8px 12px;
            background: #667eea;
            color: white;
            text-decoration: none;
            border-radius: 4px;
            font-size: 12px;
            text-align: center;
            transition: background 0.3s;
        }}

        .file-link:hover {{
            background: #764ba2;
        }}

        audio {{
            width: 100%;
            height: 32px;
        }}

        .no-files {{
            color: #888;
            text-align: center;
            padding: 40px 20px;
            font-style: italic;
        }}

        .footer {{
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #e0e0e0;
            text-align: center;
            color: #888;
            font-size: 12px;
        }}

        .footer a {{
            color: #667eea;
            text-decoration: none;
        }}

        .footer a:hover {{
            text-decoration: underline;
        }}
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

        function hashPassword(password) {{
            // SHA-256 hash implementation
            return SHA256(password);
        }}

        function login() {{
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

            const passwordHash = hashPassword(password);
            if (passwordHash !== USER_HASHES[username]) {{
                errorDiv.textContent = 'Invalid username or password';
                return;
            }}

            // Success
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

        // SHA-256 implementation (simplified for browsers)
        function SHA256(str) {{
            var chrsz = 8;
            var hexcase = 0;
            function safe_add(x, y) {{
                var lsw = (x & 0xFFFF) + (y & 0xFFFF);
                var msw = (x >> 16) + (y >> 16) + (lsw >> 16);
                return (msw << 16) | (lsw & 0xFFFF);
            }}
            function S(X, n) {{ return (X >>> n) | (X << (32 - n)); }}
            function R(X, n) {{ return (X >>> n); }}
            function Ch(x, y, z) {{ return ((x & y) ^ ((~x) & z)); }}
            function Maj(x, y, z) {{ return ((x & y) ^ (x & z) ^ (y & z)); }}
            function Sigma0256(x) {{ return (S(x, 2) ^ S(x, 13) ^ S(x, 22)); }}
            function Sigma1256(x) {{ return (S(x, 6) ^ S(x, 11) ^ S(x, 25)); }}
            function Gamma0256(x) {{ return (S(x, 7) ^ S(x, 18) ^ R(x, 3)); }}
            function Gamma1256(x) {{ return (S(x, 17) ^ S(x, 19) ^ R(x, 10)); }}

            this.charCodeAt = String.prototype.charCodeAt;

            var K256 = new Array(
                0x428A2F98, 0x71374491, 0xB5C0FBCF, 0xE9B5DBA5, 0x3956C25B, 0x59F111F1, 0x923F82A4, 0xAB1C5ED5,
                0xD807AA98, 0x12835B01, 0x243185BE, 0x550C7DC3, 0x72BE5D74, 0x80DEBA60, 0x9BDC06A7, 0xC19BF174,
                0xE49B69C1, 0xEFBE4786, 0x0FC19DC6, 0x240CA1CC, 0x2DE92C6F, 0x4A7484AA, 0x5CB0A9DC, 0x76F988DA,
                0x983E5152, 0xA831C66D, 0xB00327C8, 0xBF597FC7, 0xC6E00BF3, 0xD5A79147, 0x06CA6351, 0x14292967,
                0x27B70A85, 0x2E1B2138, 0x4D2C6DFC, 0x53380D13, 0x650A7354, 0x766A0ABB, 0x81C2C92E, 0x92722C85,
                0xA2BFE8A1, 0xA81A664B, 0xC24B8B70, 0xC76C51A3, 0xD192E819, 0xD6990624, 0xF40E3585, 0x106AA070,
                0x19A4C116, 0x1E376C08, 0x2748774C, 0x34B0BCB5, 0x391C0CB3, 0x4ED8AA4A, 0x5B9CCA4F, 0x682E6FF3,
                0x748F82EE, 0x78A5636F, 0x84C87814, 0x8CC70208, 0x90BEFFFA, 0xA4506CEB, 0xBEF9A3F7, 0xC67178F2
            );

            var HASH = new Array(
                0x6A09E667, 0xBB67AE85, 0x3C6EF372, 0xA54FF53A,
                0x510E527F, 0x9B05688C, 0x1F83D9AB, 0x5BE0CD19
            );

            var str = String(str);
            var strlen = str.length;

            for (var i = 0; i < strlen; i++) {{
                str = str.substring(0, i) + String.fromCharCode(str.charCodeAt(i).toString(16).replace(/^([\da-f])$/, '0$1'), 16) + str.substring(i + 1);
            }}

            if (strlen * chrsz % 512 != 448) {{
                str += String.fromCharCode(parseInt('10000000', 2));
                while ((strlen * chrsz) % 512 != 448) {{
                    strlen++;
                    str += String.fromCharCode(0);
                }}
            }}

            for (var i = 0; i < strlen; i += 64) {{
                binb_md5_body(str.split('').slice(i, i + 64));
            }}

            var result = '';
            for (var i = 0; i < 8; i++) {{
                for (var j = 28; j >= 0; j -= 4) {{
                    var tmp = (HASH[i] >>> j) & 0xf;
                    result += '0123456789abcdef'.charAt(tmp);
                }}
            }}
            return result;
        }}

        function binb_md5_body(X) {{
            // Placeholder - using simple string hash instead
        }}

        // Use crypto API if available (better security)
        async function sha256(message) {{
            const msgBuffer = new TextEncoder().encode(message);
            const hashBuffer = await crypto.subtle.digest('SHA-256', msgBuffer);
            const hashArray = Array.from(new Uint8Array(hashBuffer));
            const hashHex = hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
            return hashHex;
        }}

        // Override hashPassword to use crypto API
        hashPassword = async (password) => {{
            return await sha256(password);
        }};

        // Update login function to handle async hashing
        const originalLogin = login;
        login = async function() {{
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
        }};
    </script>
</body>
</html>
'''
    
    return html

def generate_site(users_data_file, users_config_file, output_dir):
    """Generate the static site."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Load data
    with open(users_data_file, 'r') as f:
        users_data = json.load(f)
    
    with open(users_config_file, 'r') as f:
        users_config = json.load(f)
    
    # Generate HTML
    html = generate_index_html(users_data, users_config)
    
    # Write index.html
    index_path = output_dir / 'index.html'
    with open(index_path, 'w') as f:
        f.write(html)
    
    print(f"✓ Generated {index_path}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 4:
        print("Usage: python generate_site.py <users_data.json> <users_config.json> <output_dir>")
        sys.exit(1)
    
    generate_site(sys.argv[1], sys.argv[2], sys.argv[3])
