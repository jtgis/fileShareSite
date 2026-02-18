#!/usr/bin/env python3
"""
Add a user to the file share site.
Usage: python add_user.py <username> <password>
"""
import json
import sys
import hashlib
import os
from pathlib import Path

def hash_password(password):
    """Hash a password using SHA-256 (simple approach for static site)."""
    return hashlib.sha256(password.encode()).hexdigest()

def add_user(username, password):
    """Add or update a user in users.json."""
    users_file = Path(__file__).parent.parent / "data" / "users.json"
    
    # Load existing users
    if users_file.exists():
        with open(users_file, 'r') as f:
            users = json.load(f)
    else:
        users = {}
    
    # Add/update user
    users[username] = {
        "password_hash": hash_password(password),
        "display_name": username.capitalize()
    }
    
    # Save
    users_file.parent.mkdir(parents=True, exist_ok=True)
    with open(users_file, 'w') as f:
        json.dump(users, f, indent=2)
    
    print(f"✓ User '{username}' added successfully")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python add_user.py <username> <password>")
        sys.exit(1)
    
    username = sys.argv[1]
    password = sys.argv[2]
    
    add_user(username, password)
