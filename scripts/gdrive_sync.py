#!/usr/bin/env python3
"""
Sync files from Google Drive and fetch metadata.
Requires GOOGLE_DRIVE_TOKEN env var with a refresh token.
"""
import json
import os
from google.auth.transport.requests import Request
from google.oauth2.service_account import Credentials
from google.auth.oauthlib.flow import InstalledAppFlow
from google_auth_oauthlib.flow import Flow
import pickle
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

# For GitHub Actions, we'll use a simpler approach with gdown or direct API
# This script fetches file metadata from Google Drive

def get_gdrive_client():
    """
    Initialize Google Drive API client.
    Expects GOOGLE_DRIVE_CREDENTIALS env var with service account JSON
    or GOOGLE_DRIVE_REFRESH_TOKEN for OAuth.
    """
    if "GOOGLE_DRIVE_CREDENTIALS" in os.environ:
        # Service account (for GitHub Actions)
        creds_json = json.loads(os.environ["GOOGLE_DRIVE_CREDENTIALS"])
        credentials = Credentials.from_service_account_info(creds_json)
    else:
        raise ValueError("GOOGLE_DRIVE_CREDENTIALS environment variable not set")
    
    return build('drive', 'v3', credentials=credentials)

def find_folder_by_name(service, parent_id, folder_name):
    """Find a folder by name in Google Drive."""
    query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and '{parent_id}' in parents and trashed=false"
    results = service.files().list(
        q=query,
        spaces='drive',
        fields='files(id, name)',
        pageSize=1
    ).execute()
    
    files = results.get('files', [])
    return files[0]['id'] if files else None

def list_files_in_folder(service, folder_id):
    """List all files in a Google Drive folder (non-recursive)."""
    query = f"'{folder_id}' in parents and trashed=false"
    results = service.files().list(
        q=query,
        spaces='drive',
        fields='files(id, name, mimeType, size, webViewLink)',
        pageSize=1000
    ).execute()
    
    return results.get('files', [])

def get_shareable_link(service, file_id):
    """Get a shareable link for a file."""
    try:
        service.permissions().create(
            fileId=file_id,
            body={'role': 'reader', 'type': 'anyone'}
        ).execute()
    except:
        pass  # Already shared or error
    
    file = service.files().get(fileId=file_id, fields='webViewLink').execute()
    return file.get('webViewLink', '')

def sync_users_from_gdrive(root_folder_id):
    """
    Fetch user folders and files from Google Drive.
    Returns: {username: [files]}
    """
    service = get_gdrive_client()
    
    # Find the users folder
    users_folder_id = find_folder_by_name(service, root_folder_id, 'users')
    if not users_folder_id:
        raise ValueError(f"Could not find 'users' folder in parent {root_folder_id}")
    
    # List all user folders
    user_folders = list_files_in_folder(service, users_folder_id)
    
    users_data = {}
    
    for user_folder in user_folders:
        if user_folder['mimeType'] != 'application/vnd.google-apps.folder':
            continue
        
        username = user_folder['name'].lower()
        
        # List files in user folder
        files = list_files_in_folder(service, user_folder['id'])
        
        user_files = []
        for file in files:
            if file['mimeType'] == 'application/vnd.google-apps.folder':
                continue
            
            # Get file size and extension
            size = int(file.get('size', 0))
            name = file['name']
            ext = name.rsplit('.', 1)[-1].lower() if '.' in name else ''
            
            # Determine file category
            category = get_file_category(ext)
            
            # Get shareable link
            link = get_shareable_link(service, file['id'])
            
            user_files.append({
                'name': name,
                'id': file['id'],
                'size': format_bytes(size),
                'ext': ext,
                'category': category,
                'link': link
            })
        
        users_data[username] = sorted(user_files, key=lambda f: f['name'])
    
    return users_data

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
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024.0:
            return f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} PB"

if __name__ == "__main__":
    # For testing: set GOOGLE_DRIVE_CREDENTIALS and GDRIVE_ROOT_FOLDER_ID
    root_folder_id = os.environ.get('GDRIVE_ROOT_FOLDER_ID')
    if not root_folder_id:
        print("Error: GDRIVE_ROOT_FOLDER_ID environment variable not set")
        exit(1)
    
    try:
        users_data = sync_users_from_gdrive(root_folder_id)
        print(json.dumps(users_data, indent=2))
    except Exception as e:
        print(f"Error: {e}")
        exit(1)
