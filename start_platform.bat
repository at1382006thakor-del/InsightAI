@echo off
title InsightAI BI Platform Launcher
echo ===================================================
echo   InsightAI BI Platform Launcher
echo ===================================================
echo.
echo Launching Uvicorn Backend API in a separate window...
start "InsightAI Backend API" cmd /k ".\venv\Scripts\python.exe backend/run.py"

echo.
echo Launching Vite React Frontend in a separate window...
start "InsightAI Frontend" cmd /k "cd frontend && npm.cmd run dev"

echo.
echo Waiting 3 seconds for servers to initialize...
timeout /t 3 /nobreak >nul

echo.
echo Launching default web browser to http://localhost:5173...
start http://localhost:5173

echo.
echo ===================================================
echo   System running. Close the terminal windows to exit.
echo ===================================================
pause
