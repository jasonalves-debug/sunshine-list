@echo off
cd /d "%~dp0"
start "Sunshine List server - close this window to stop" python -m http.server 8000
timeout /t 2 /nobreak >nul
start "" http://localhost:8000/sunshine_map.html
