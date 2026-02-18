# File Share Site - GitHub + Google Drive Edition

A **static file sharing site** that combines **GitHub Pages** for hosting and **Google Drive** for file storage.

## 🎯 How It Works

1. **GitHub Actions** runs daily and syncs files from Google Drive
2. Generates a static HTML site with password-protected user folders
3. Deploys to **GitHub Pages** (free hosting)
4. Users view/download files hosted on Google Drive (no bandwidth charges)

## ✨ Features

- 🔐 Password-protected login (no Google accounts required)
- 🎥 Video previews (`.mp4`, `.webm`, `.m4v`, `.ogg`)
- 🎵 Audio player (`.mp3`, `.m4a`, `.wav`, `.flac`)
- 🖼️ Image gallery (`.jpg`, `.jpeg`, `.png`, `.gif`, `.webp`)
- 📄 PDF viewer (`.pdf`)
- 📥 Direct Google Drive download links for all files
- 📱 Mobile-responsive design
- ⚡ Zero server costs
- 🔄 Auto-updates daily

---

## 🚀 Setup Instructions

### 1. Set Up Google Drive Structure

Create this folder structure in your Google Drive:

```
My Drive/
  └── fileShareSite/          (root folder)
      └── users/
          ├── alice/          (user folders)
          │   ├── photo1.jpg
          │   └── video.mp4
          └── bob/
              └── document.pdf
```

- Each username becomes a folder (e.g., `alice`, `bob`)
- Put files in their respective folders
- The app detects any file type

### 2. Set Up Google Drive API

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a **new project**
3. Enable the **Google Drive API**:
   - APIs & Services → Library
   - Search for "Google Drive API"
   - Click "Enable"
4. Create a **Service Account**:
   - APIs & Services → Credentials
   - Create Credentials → Service Account
   - Fill in details (any name is fine)
   - Skip optional steps, click "Create"
5. **Create a key**:
   - In the Service Account, click on the "Keys" tab
   - Create → JSON
   - Download the JSON file (keep it safe!)

6. **Share Google Drive folder with the service account**:
   - Get the `client_email` from the JSON file (looks like: `something@something.iam.gserviceaccount.com`)
   - In Google Drive, right-click your `fileShareSite` folder → Share
   - Add the service account email as an editor

### 3. Get Your Google Drive Folder ID

1. Open your `fileShareSite` folder in Google Drive
2. The URL will look like: `https://drive.google.com/drive/folders/XXXXXXXXXXXXX`
3. Copy the ID (the `XXXXXXXXXXXXX` part)

### 4. Set Up GitHub Secrets

1. Go to your repository settings
2. Secrets and Variables → Actions
3. Create two secrets:

| Secret Name | Value |
|-------------|-------|
| `GOOGLE_DRIVE_CREDENTIALS` | Paste the entire contents of the JSON file from Google Cloud |
| `GDRIVE_ROOT_FOLDER_ID` | Paste the folder ID from the `fileShareSite` folder |

### 5. Enable GitHub Pages

1. Go to repository Settings → Pages
2. Set **Source** to `Deploy from a branch`
3. Set **Branch** to `gh-pages` → `/(root)`
4. Save

### 6. Add Your First User

```bash
# Clone the repo locally
git clone https://github.com/YOUR_GITHUB_USERNAME/your-repo.git
cd your-repo

# Install dependencies
pip install -r requirements.txt

# Add a user (username and password)
python scripts/add_user.py alice mypassword

# Commit and push
git add data/users.json
git commit -m "Add alice user"
git push origin main
```

The GitHub Action will automatically run and generate the site!

### 7. View Your Site

Once the GitHub Action completes:
- Your site will be available at: `https://YOUR_GITHUB_USERNAME.github.io/your-repo`
- Check the "Actions" tab to see the build status

---

## 📝 Managing Users

### Add a User

```bash
python scripts/add_user.py username password
git add data/users.json
git commit -m "Add username user"
git push origin main
```

### Remove a User

1. Open `data/users.json`
2. Remove the user's entry:
   ```json
   {
       "alice": { "password_hash": "..." },
       "bob": { "password_hash": "..." }
   }
   ```
3. Delete the user's folder from Google Drive
4. Commit and push

### Change a User's Password

```bash
python scripts/add_user.py username newpassword
git add data/users.json
git commit -m "Update username password"
git push origin main
```

---

## 🔄 Syncing Files

The site **updates automatically every day at 1 AM UTC**. 

To trigger an update manually:

1. Go to Actions tab
2. Click "Generate Static Site from Google Drive"
3. Click "Run workflow"

Or simply:
- Push to `main` (any change triggers a rebuild)
- Edit `data/users.json` and push

---

## 📱 Mobile Support

The site is fully mobile-responsive:
- Files display as stacked cards
- Images are optimized for mobile viewing
- Audio/video players work on all devices

---

## 🛡️ Security Notes

1. **Passwords are hashed** using SHA-256 in the browser (not sent to server)
2. **Google Drive token is never exposed** to users (only used on GitHub Actions)
3. **Static site** means no server to hack (GitHub Pages is extremely secure)
4. **Shareable links** to Google Drive are read-only for your users
5. Keep your repo **private** if you want to hide the list of users

---

## ❓ Troubleshooting

### Action fails with "Could not find 'users' folder"

- Make sure your Google Drive folder structure matches exactly:
  ```
  fileShareSite/
    └── users/
  ```
- Double-check the folder ID in secrets

### Files not appearing on site

1. Check the GitHub Actions log (Actions tab)
2. Make sure files are in user folders (e.g., `users/alice/photo.jpg`)
3. Wait for the daily auto-run or manually trigger the workflow

### Login doesn't work

- Check that the username exists in `data/users.json`
- Password is case-sensitive
- Clear browser cache and try again

### Images/videos don't load

- Make sure the files are in the correct folder in Google Drive
- File names should not have special characters
- Check that the service account has access to the files

---

## 🔧 Architecture

```
┌─────────────────────┐
│   Google Drive      │
│   (file storage)    │
└──────────┬──────────┘
           │
           │ (GitHub Actions syncs daily)
           ↓
┌─────────────────────┐
│  GitHub Actions     │
│  (runs sync script) │
└──────────┬──────────┘
           │
           │ (generates HTML)
           ↓
┌─────────────────────┐
│  GitHub Pages       │
│  (static website)   │
└──────────┬──────────┘
           │
           │ (users login)
           ↓
┌─────────────────────┐
│  User's Browser     │
│  (views files)      │
└─────────────────────┘
```

---

## 📄 File Structure

```
your-repo/
├── .github/
│   └── workflows/
│       └── generate-site.yml    (GitHub Actions workflow)
├── scripts/
│   ├── add_user.py              (add users locally)
│   ├── gdrive_sync.py           (sync from Google Drive)
│   └── generate_site.py         (generate static HTML)
├── data/
│   ├── users.json               (user credentials)
│   └── gdrive_files.json        (generated by sync)
├── docs/                        (generated static site)
│   └── index.html
├── requirements.txt             (Python dependencies)
└── README.md
```

---

## 🆘 Support

If you encounter issues:

1. Check the **Actions** tab for error logs
2. Verify your Google Drive structure
3. Ensure secrets are set correctly
4. Check that the service account has folder permissions

---

## 📜 License

MIT License - feel free to use and modify!
