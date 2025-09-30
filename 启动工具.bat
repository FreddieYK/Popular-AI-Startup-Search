@echo off
chcp 65001 > nul
echo Starting AI Startup News Monitoring System...
echo.

echo [1/4] Checking and installing backend dependencies...
cd backend
if not exist ".venv" (
    echo Creating virtual environment...
    python -m venv .venv
)
call .venv\Scripts\activate
pip install -r requirements.txt
if %ERRORLEVEL% NEQ 0 (
    echo Backend dependency installation failed!
    pause
    exit /b 1
)
echo Backend dependencies installed successfully!
echo.

echo [2/4] Starting backend service...
start "AI-News-Monitor-Backend" cmd /k "cd /d %cd% && .venv\Scripts\activate && python main.py"
echo Backend service is starting, waiting 8 seconds...
timeout /t 8 > nul
echo.

echo [3/4] Checking and installing frontend dependencies...
cd ..\frontend
call npm install
if %ERRORLEVEL% NEQ 0 (
    echo Frontend dependency installation failed!
    pause
    exit /b 1
)
echo Frontend dependencies installed successfully!
echo.

echo [4/4] Starting frontend service...
start "AI-News-Monitor-Frontend" cmd /k "cd /d %cd% && npm run dev"
echo Frontend service is starting, waiting 5 seconds...
timeout /t 5 > nul
echo.

echo Opening browser...
timeout /t 3 > nul
start http://localhost:5173

echo.
echo ===================================
echo    AI Startup News Monitor Started!
echo ===================================
echo Frontend: http://localhost:5173
echo Backend: http://localhost:8004
echo API Docs: http://localhost:8004/api/docs
echo.
echo Press any key to close this window...
pause > nul