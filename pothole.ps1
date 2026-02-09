# =================================================================
# Smart Pothole Detection & Mapping System - All-in-One Runner (Windows)
# =================================================================

Write-Host ">>> Initializing Smart Pothole Detection System..." -ForegroundColor Blue

# 1. Start the Backend API (FastAPI) in a new window
Write-Host "[1/2] Starting Backend Server..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit -Command .\venv\Scripts\python.exe backend/main.py" -WindowStyle Normal

# Wait a few seconds for the server to initialize
Start-Sleep -Seconds 4

# 2. Start the Pothole Detection Logic
Write-Host "[2/2] Starting Detection Engine (Simulation/Logic)..." -ForegroundColor Green
Write-Host "Starting Simulation..." -ForegroundColor Yellow
.\venv\Scripts\python.exe simulate_detection.py

Write-Host "=====================================================" -ForegroundColor Blue
Write-Host "SYSTEM ONLINE!"
Write-Host "Dashboard: http://localhost:8000"
Write-Host "3D Map:    http://localhost:8000/3d-map"
Write-Host "=====================================================" -ForegroundColor Blue
