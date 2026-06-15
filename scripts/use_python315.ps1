$ErrorActionPreference = "Stop"
$PythonPath = "C:\Users\tupen\AppData\Local\Programs\Python\Python315\python.exe"

if (!(Test-Path $PythonPath)) {
  Write-Error "Python was not found at $PythonPath"
}

$env:CINEHUMAN_PYTHON = $PythonPath
Write-Host "Using Python: $env:CINEHUMAN_PYTHON"
& $env:CINEHUMAN_PYTHON --version
