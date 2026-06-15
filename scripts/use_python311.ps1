$ErrorActionPreference = "Stop"
$PythonPath = "C:\Users\tupen\AppData\Local\Programs\Python\Python311\python.exe"

if (!(Test-Path $PythonPath)) {
  Write-Error "Python 3.11 was not found at $PythonPath"
}

$env:CINEHUMAN_PYTHON = $PythonPath
Write-Host "Using Python: $env:CINEHUMAN_PYTHON"
& $env:CINEHUMAN_PYTHON --version
