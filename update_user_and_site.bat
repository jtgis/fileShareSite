@echo off
REM Simple script to add/update a user and regenerate the site
REM Usage: update_user_and_site.bat username password

if "%~2"=="" (
    echo Usage: update_user_and_site.bat username password
    echo Example: update_user_and_site.bat john mypassword123
    exit /b 1
)

set USERNAME=%~1
set PASSWORD=%~2

echo.
echo ========================================
echo Adding/Updating User
echo ========================================
cd scripts
python add_user.py %USERNAME% %PASSWORD%
if errorlevel 1 (
    echo ERROR: Failed to add user
    exit /b 1
)
cd ..

echo.
echo ========================================
echo Verifying users.json
echo ========================================
type data\users.json
echo.

echo.
echo ========================================
echo Regenerating Static Site
echo ========================================
python scripts\generate_site.py data\gdrive_files.json data\users.json docs\

echo.
echo ========================================
echo DONE! Now upload these files to GitHub:
echo ========================================
echo 1. Go to https://github.com/YOUR_USERNAME/fileShareSite
echo 2. Click "Upload files"  
echo 3. Drag and drop:
echo    - data\users.json
echo    - docs\index.html
echo 4. Commit changes
echo.
echo Your credentials are:
echo   Username: %USERNAME%
echo   Password: %PASSWORD%
echo.
pause
