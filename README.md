# File Share Site

A static file-sharing site using **GitHub Pages** for hosting and **Google Drive** for storage. A GitHub Actions workflow syncs files daily, generates a password-protected static site, and deploys it automatically — no server required.

## Features

- Password-protected login (SHA-256, client-side — no Google accounts needed)
- In-browser preview for video, audio, images, and PDFs
- Direct download links via Google Drive
- Mobile-responsive layout
- Automatic daily updates via GitHub Actions
- Zero hosting costs

---

## Setup

### 1. Google Drive folder structure

```
My Drive/
  └── fileShareSite/
      └── users/
          ├── alice/
          │   ├── photo.jpg
          │   └── video.mp4
          └── bob/
              └── document.pdf
```

Each subfolder under `users/` corresponds to a site user.

### 2. Google Drive API

1. Create a project in the [Google Cloud Console](https://console.cloud.google.com/)
2. Enable the **Google Drive API** (APIs & Services → Library)
3. Create a **Service Account** (APIs & Services → Credentials → Create Credentials)
4. Generate a **JSON key** for the service account (Keys tab → Add Key → JSON)
5. Share your `fileShareSite` folder with the service account's `client_email` (as Editor)

### 3. GitHub configuration

**Secrets** (Settings → Secrets and Variables → Actions):

| Secret | Value |
|--------|-------|
| `GOOGLE_DRIVE_CREDENTIALS` | Full contents of the service account JSON key |
| `GDRIVE_ROOT_FOLDER_ID` | Folder ID from the `fileShareSite` URL |

**Pages** (Settings → Pages):
- Source: `Deploy from a branch`
- Branch: `gh-pages` / `/(root)`

### 4. Add users

```bash
pip install -r requirements.txt
python scripts/add_user.py <username> <password>
git add data/users.json && git commit -m "add user" && git push
```

The workflow will run automatically and the site will be available at your GitHub Pages URL.

---

## User Management

```bash
# Add or update a user
python scripts/add_user.py <username> <password>

# Remove a user — delete their entry from data/users.json
# and remove their folder from Google Drive
```

Commit and push `data/users.json` after any change.

---

## Syncing

The site rebuilds **daily at 1 AM UTC** and on every push to `main`.

To trigger manually: Actions tab → "Generate Static Site from Google Drive" → Run workflow.

---

## Local Testing

```bash
pip install -r requirements.txt

# Test Drive sync
export GDRIVE_ROOT_FOLDER_ID='your_folder_id'
GOOGLE_DRIVE_CREDENTIALS=$(cat credentials.json) python scripts/gdrive_sync.py

# Generate the site
python scripts/generate_site.py data/gdrive_files.json data/users.json docs/

# Open docs/index.html in a browser
```

> Never commit `credentials.json` to the repository. Use GitHub Secrets for CI.

---

## Security

- Passwords are hashed client-side (SHA-256) — plaintext is never stored or transmitted
- The Google Drive service account key is only used in GitHub Actions
- Static hosting on GitHub Pages eliminates server-side attack surface
- Drive share links are read-only
- Keep the repository private to hide the user list

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| "Could not find 'users' folder" | Verify the `fileShareSite/users/` structure in Drive and check the folder ID |
| "GOOGLE_DRIVE_CREDENTIALS not set" | Ensure the secret exists and contains the full JSON key |
| Files not appearing | Check Actions logs; confirm files are inside a user folder |
| Login not working | Verify username in `data/users.json`; passwords are case-sensitive |
| Media not loading | Check Drive folder permissions and avoid special characters in filenames |

---

## Project Structure

```
├── .github/workflows/generate-site.yml   # CI workflow
├── scripts/
│   ├── add_user.py                        # User management
│   ├── gdrive_sync.py                     # Drive sync
│   └── generate_site.py                   # Site generator
├── data/
│   ├── users.json                         # Credentials (hashed)
│   └── gdrive_files.json                  # Synced file metadata
├── docs/
│   └── index.html                         # Generated site
└── requirements.txt
```

---

## License

MIT
