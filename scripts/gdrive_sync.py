#!/usr/bin/env python3
"""
Sync files from Google Drive and fetch metadata.
Requires GOOGLE_DRIVE_CREDENTIALS env var with service account JSON.
"""
import json
import os
import sys
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

def get_gdrive_client():
    """
    Initialize Google Drive API client.
    Expects GOOGLE_DRIVE_CREDENTIALS env var with service account JSON.
    """
    if "GOOGLE_DRIVE_CREDENTIALS" not in os.environ:
        raise ValueError("GOOGLE_DRIVE_CREDENTIALS environment variable not set")
    
    try:
        creds_json = json.loads(os.environ["GOOGLE_DRIVE_CREDENTIALS"])
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in GOOGLE_DRIVE_CREDENTIALS: {e}", file=sys.stderr)
        raise
    
    try:
        credentials = Credentials.from_service_account_info(
            creds_json,
            scopes=['https://www.googleapis.com/auth/drive.readonly']
        )
    except Exception as e:
        print(f"Error: Failed to create credentials: {e}", file=sys.stderr)
        raise
    
    try:
        service = build('drive', 'v3', credentials=credentials)
        print("✓ Google Drive API client initialized", file=sys.stderr)
        return service
    except Exception as e:
        print(f"Error: Failed to build Drive service: {e}", file=sys.stderr)
        raise

def find_folder_by_name(service, parent_id, folder_name):
    """Find a folder by name in Google Drive."""
    try:
        query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and '{parent_id}' in parents and trashed=false"
        results = service.files().list(
            q=query,
            spaces='drive',
            fields='files(id, name)',
            pageSize=1
        ).execute()
        
        files = results.get('files', [])
        if files:
            print(f"✓ Found folder '{folder_name}'", file=sys.stderr)
            return files[0]['id']
        return None
    except Exception as e:
        print(f"Error searching for folder '{folder_name}': {e}", file=sys.stderr)
        raise

def list_files_in_folder(service, folder_id):
    """List all files in a Google Drive folder (non-recursive)."""
    try:
        query = f"'{folder_id}' in parents and trashed=false"
        results = service.files().list(
            q=query,
            spaces='drive',
            fields='files(id, name, mimeType, size, webViewLink)',
            pageSize=1000
        ).execute()
        
        return results.get('files', [])
    except Exception as e:
        print(f"Error listing files in folder {folder_id}: {e}", file=sys.stderr)
        raise

def get_shareable_link(service, file_id, category='other'):
    """Get a shareable link for a file."""
    try:
        # Make the file publicly accessible
        try:
            service.permissions().create(
                fileId=file_id,
                body={'role': 'reader', 'type': 'anyone'},
                fields='id'
            ).execute()
            print(f"✓ Made file {file_id} public", file=sys.stderr)
        except Exception as e:
            print(f"Note: Could not set permissions for {file_id}: {e}", file=sys.stderr)
        
        # Return direct links that work without login
        if category in ['image', 'audio']:
            # Direct download/view link
            return f"https://drive.google.com/uc?export=view&id={file_id}"
        elif category in ['video', 'pdf']:
            # Embeddable preview link
            return f"https://drive.google.com/file/d/{file_id}/preview"
        else:
            # Direct download for other files
            return f"https://drive.google.com/uc?export=download&id={file_id}"
            
    except Exception as e:
        print(f"Error getting shareable link for {file_id}: {e}", file=sys.stderr)
        return f"https://drive.google.com/file/d/{file_id}/view"

def get_file_category(ext):
    """Categorize file by extension."""
    video_exts = {'mp4', 'webm', 'ogg', 'm4v', 'avi', 'mov', 'mkv'}
    audio_exts = {'mp3', 'wav', 'ogg', 'flac', 'm4a', 'aac', 'wma'}
    image_exts = {'jpg', 'jpeg', 'png', 'gif', 'webp', 'bmp', 'svg'}
    pdf_exts = {'pdf'}
    
    ext = ext.lower()
    if ext in video_exts:
        return 'video'
    elif ext in audio_exts:
        return 'audio'
    elif ext in image_exts:
        return 'image'
    elif ext in pdf_exts:
        return 'pdf'
    return 'other'

def format_bytes(size):
    """Format bytes to human-readable size."""
    try:
        size = int(size)
    except (ValueError, TypeError):
        return "0 B"
    
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024.0:
            return f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} PB"

def sync_users_from_gdrive(root_folder_id):
    """
    Fetch user folders and files from Google Drive.
    Returns: {username: [files]}
    """
    try:
        service = get_gdrive_client()
    except Exception as e:
        print(f"Error: Failed to initialize Google Drive client: {e}", file=sys.stderr)
        raise
    
    print(f"✓ Looking for users folder in {root_folder_id}", file=sys.stderr)
    
    # Find the users folder
    users_folder_id = find_folder_by_name(service, root_folder_id, 'users')
    if not users_folder_id:
        raise ValueError(f"Could not find 'users' folder in parent {root_folder_id}")
    
    # List all user folders
    print(f"✓ Syncing user folders...", file=sys.stderr)
    user_folders = list_files_in_folder(service, users_folder_id)
    
    users_data = {}
    
    for user_folder in user_folders:
        if user_folder['mimeType'] != 'application/vnd.google-apps.folder':
            continue
        
        username = user_folder['name'].lower()
        print(f"✓ Processing user folder: {username}", file=sys.stderr)
        
        # List files in user folder
        files = list_files_in_folder(service, user_folder['id'])
        
        user_files = []
        for file in files:
            # Skip folders
            if file['mimeType'] == 'application/vnd.google-apps.folder':
                continue
            
            # Get file size and extension
            size = int(file.get('size', 0))
            name = file['name']
            ext = name.rsplit('.', 1)[-1].lower() if '.' in name else ''
            
            # Determine file category
            category = get_file_category(ext)
            
            # Get shareable link with proper format for category
            link = get_shareable_link(service, file['id'], category)
            
            user_files.append({
                'name': name,
                'id': file['id'],
                'size': format_bytes(size),
                'ext': ext,
                'category': category,
                'link': link
            })
        
        users_data[username] = sorted(user_files, key=lambda f: f['name'])
        print(f"  ✓ Found {len(user_files)} files for {username}", file=sys.stderr)
    
    print(f"✓ Sync complete: {len(users_data)} users", file=sys.stderr)
    return users_data

if __name__ == "__main__":
    root_folder_id = os.environ.get('GDRIVE_ROOT_FOLDER_ID')
    if not root_folder_id:
        print("Error: GDRIVE_ROOT_FOLDER_ID environment variable not set", file=sys.stderr)
        sys.exit(1)
    
    try:
        users_data = sync_users_from_gdrive(root_folder_id)
        # Output JSON to stdout
        print(json.dumps(users_data, indent=2))
    except Exception as e:
        print(f"Fatal error: {e}", file=sys.stderr)
        sys.exit(1)
