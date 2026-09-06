@echo off
REM One-click: start the SmartHire app + public share tunnel.
REM Copy the https://....trycloudflare.com link printed in the "SmartHire Tunnel" window.
cd /d "%~dp0"
set MANAGER_PASSWORD=smarthire2026
start "SmartHire App" cmd /k .venv\Scripts\python.exe run.py
timeout /t 6 /nobreak >nul
start "SmartHire Tunnel" cmd /k C:\Users\GP3-shruti\AppData\Local\Microsoft\WinGet\Packages\Cloudflare.cloudflared_Microsoft.Winget.Source_8wekyb3d8bbwe\cloudflared.exe tunnel --url http://localhost:8000 --protocol quic --edge-ip-version 4 --no-autoupdate
echo.
echo Two windows opened. Keep BOTH open while people are testing.
echo The share link is the https://....trycloudflare.com line in the "SmartHire Tunnel" window.
