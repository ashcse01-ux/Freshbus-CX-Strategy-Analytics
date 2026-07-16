@echo off
cd /d "%~dp0backend"
call ..\freshbus_analytics\Scripts\activate.bat
:loop
echo Starting Freshbus Backend Server...
python -m uvicorn main:app --host 0.0.0.0 --port 8000
echo.
echo [WARNING] Server stopped. Restarting in 5 seconds...
timeout /t 5
goto loop
