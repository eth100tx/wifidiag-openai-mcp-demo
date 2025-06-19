@echo off
echo.
echo ========================================
echo  MCP-ChatGPT Bridge - Quick Start
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python from https://python.org
    pause
    exit /b 1
)

echo Python found: 
python --version

REM Check if .env file exists
if not exist ".env" (
    echo.
    echo WARNING: .env file not found
    echo Please copy .env.template to .env and add your OpenAI API key
    echo.
    pause
)

REM Install dependencies
echo.
echo Installing dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)

REM Test MCP server
echo.
echo Testing MCP server...
timeout /t 2 >nul
python -c "import wifi_diagnostics_mcp; print('MCP server imports successfully')" 2>nul
if errorlevel 1 (
    echo WARNING: MCP server may have issues
)

REM Start the application
echo.
echo Starting MCP-ChatGPT Bridge...
echo.
python mcp_chatgpt_client.py

echo.
echo Application closed.
pause