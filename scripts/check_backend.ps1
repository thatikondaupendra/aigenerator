#!/usr/bin/env powershell
<#
.DESCRIPTION
Backend health check and diagnostics
Verify backend is working correctly
#>

$ErrorActionPreference = "Stop"
$backendUrl = "http://localhost:8000"

function Write-Success { Write-Host "✓ $args" -ForegroundColor Green }
function Write-Error-Custom { Write-Host "✗ $args" -ForegroundColor Red }
function Write-Info { Write-Host "ℹ $args" -ForegroundColor Cyan }

Write-Info "CineHuman Backend Health Check"
Write-Info "Testing $backendUrl..."
Write-Info ""

# Test health endpoint
Write-Info "1. Testing /health endpoint..."
try {
    $response = Invoke-WebRequest "$backendUrl/health" -ErrorAction Stop
    $data = $response.Content | ConvertFrom-Json
    Write-Success "Health check passed"
    Write-Info "Status: $($data.status)"
    Write-Info "GPU Info:"
    $data.gpu | Get-Member -MemberType NoteProperty | ForEach-Object {
        Write-Info "  - $($_.Name): $($data.gpu."$($_.Name)")"
    }
} catch {
    Write-Error-Custom "Health check failed: $_"
    Write-Error-Custom "Backend might not be running. Start with: scripts\start_backend.ps1"
    exit 1
}

Write-Info ""
Write-Info "2. Testing /models/status endpoint..."
try {
    $response = Invoke-WebRequest "$backendUrl/models/status" -ErrorAction Stop
    $data = $response.Content | ConvertFrom-Json
    Write-Success "Models status retrieved"
    $data.models | Get-Member -MemberType NoteProperty | ForEach-Object {
        $modelName = $_.Name
        $model = $data.models.$modelName
        $status = if ($model.download_complete) { "✓" } else { "✗" }
        Write-Info "  $status $modelName ($($model.file_count) files, $($model.size_mb)MB)"
    }
} catch {
    Write-Error-Custom "Models status failed: $_"
}

Write-Info ""
Write-Info "3. Testing API endpoints..."
try {
    $response = Invoke-WebRequest "$backendUrl/docs" -ErrorAction Stop
    Write-Success "Swagger API docs available at $backendUrl/docs"
} catch {
    Write-Error-Custom "API docs not accessible: $_"
}

Write-Success ""
Write-Success "Backend is operational!"
Write-Info "Frontend: http://localhost:5173"
Write-Info "Backend: http://localhost:8000"
