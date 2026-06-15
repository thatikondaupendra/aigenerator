#!/usr/bin/env powershell
<#
.DESCRIPTION
CineHuman AI Studio - All-in-One Startup and Debug Script
This script handles:
- Environment setup
- Dependency verification
- Backend startup
- Frontend startup
- Error diagnostics
#>

$ErrorActionPreference = "Stop"
$WarningPreference = "Continue"

# Color output
function Write-Success { Write-Host "✓ $args" -ForegroundColor Green }
function Write-Error-Custom { Write-Host "✗ $args" -ForegroundColor Red }
function Write-Info { Write-Host "ℹ $args" -ForegroundColor Cyan }
function Write-Warn { Write-Host "⚠ $args" -ForegroundColor Yellow }

# Get script directory
$scriptDir = Split-Path -Parent -Path $MyInvocation.MyCommand.Definition
$projectRoot = Split-Path -Parent -Path $scriptDir

Write-Info "CineHuman AI Studio - Setup & Launch"
Write-Info "Project root: $projectRoot"

# Check Python
Write-Info "Checking Python..."
$pythonPath = "$projectRoot\.venv\Scripts\python.exe"
if (-not (Test-Path $pythonPath)) {
    Write-Error-Custom "Virtual environment not found at $pythonPath"
    Write-Info "Run scripts\install_windows.ps1 first"
    exit 1
}
Write-Success "Python environment found"

# Check Node
Write-Info "Checking Node.js..."
$nodeVersion = & node --version 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Success "Node.js $nodeVersion found"
} else {
    Write-Error-Custom "Node.js not found. Install from https://nodejs.org/"
    exit 1
}

# Check frontend dependencies
Write-Info "Checking frontend dependencies..."
$packageJsonPath = "$projectRoot\frontend\package.json"
$nodeModulesPath = "$projectRoot\frontend\node_modules"
if (-not (Test-Path $nodeModulesPath)) {
    Write-Warn "Frontend dependencies not installed. Installing..."
    Push-Location "$projectRoot\frontend"
    & npm install
    if ($LASTEXITCODE -ne 0) {
        Write-Error-Custom "Failed to install frontend dependencies"
        Pop-Location
        exit 1
    }
    Pop-Location
    Write-Success "Frontend dependencies installed"
} else {
    Write-Success "Frontend dependencies ready"
}

# Set environment variables
Write-Info "Setting environment variables..."
$env:CUDA_VISIBLE_DEVICES = "0"
$env:NVIDIA_VISIBLE_DEVICES = "all"
$env:NVIDIA_DRIVER_CAPABILITIES = "compute,utility"
$env:HF_HOME = "$projectRoot\models\hf-cache"
$env:HF_HUB_CACHE = "$projectRoot\models\hf-cache\hub"
$env:CINEHUMAN_HOST = "0.0.0.0"
$env:CINEHUMAN_PORT = "8000"
Write-Success "Environment variables set"

# Create output directories
Write-Info "Creating output directories..."
@(
    "$projectRoot\outputs\images",
    "$projectRoot\outputs\videos",
    "$projectRoot\outputs\enhanced",
    "$projectRoot\models\hf-cache\hub",
    "$projectRoot\models\hf-cache\transformers",
    "$projectRoot\models\hf-cache\diffusers"
) | ForEach-Object {
    if (-not (Test-Path $_)) {
        New-Item -ItemType Directory -Path $_ -Force | Out-Null
    }
}
Write-Success "Output directories ready"

# Start services
Write-Info "Starting services..."
Write-Info "Backend will run on http://localhost:8000"
Write-Info "Frontend will run on http://localhost:5173"
Write-Warn "Opening new PowerShell windows for each service..."
Write-Warn "Press Ctrl+C in each window to stop the services"

# Backend window
Write-Info "Starting backend..."
$backendScript = @"
`$ErrorActionPreference = 'Stop'
Set-Location '$projectRoot'
`$env:CUDA_VISIBLE_DEVICES = '0'
`$env:NVIDIA_VISIBLE_DEVICES = 'all'
`$env:NVIDIA_DRIVER_CAPABILITIES = 'compute,utility'
`$env:HF_HOME = '$projectRoot\models\hf-cache'
`$env:HF_HUB_CACHE = '$projectRoot\models\hf-cache\hub'
`$env:CINEHUMAN_HOST = '0.0.0.0'
`$env:CINEHUMAN_PORT = '8000'

Write-Host 'Starting CineHuman Backend...' -ForegroundColor Cyan
Write-Host 'API will be available at http://localhost:8000' -ForegroundColor Green
Write-Host 'Health check: http://localhost:8000/health' -ForegroundColor Green
Write-Host 'API docs: http://localhost:8000/docs' -ForegroundColor Green
Write-Host ''
'$pythonPath' -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
"@

Start-Process powershell -ArgumentList "-NoExit", "-Command", $backendScript -WindowStyle Normal

Start-Sleep -Seconds 2

# Frontend window
Write-Info "Starting frontend..."
$frontendScript = @"
`$ErrorActionPreference = 'Stop'
Set-Location '$projectRoot\frontend'

Write-Host 'Starting CineHuman Frontend...' -ForegroundColor Cyan
Write-Host 'Frontend will be available at http://localhost:5173' -ForegroundColor Green
Write-Host ''
npm run dev
"@

Start-Process powershell -ArgumentList "-NoExit", "-Command", $frontendScript -WindowStyle Normal

Write-Success "Services started in new windows"
Write-Info ""
Write-Info "Opening browser..."
Start-Sleep -Seconds 3
Start-Process "http://localhost:5173"

Write-Success ""
Write-Success "CineHuman AI Studio is running!"
Write-Info "Frontend: http://localhost:5173"
Write-Info "Backend: http://localhost:8000"
Write-Info "API Docs: http://localhost:8000/docs"
Write-Warn "Press Ctrl+C in the service windows to stop"
