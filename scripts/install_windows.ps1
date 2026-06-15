$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
Set-Location ..

$PythonArgs = @()
if ($env:CINEHUMAN_PYTHON) {
  if (!(Test-Path $env:CINEHUMAN_PYTHON)) {
    Write-Error "CINEHUMAN_PYTHON points to a missing file: $env:CINEHUMAN_PYTHON"
  }
  $PythonExe = $env:CINEHUMAN_PYTHON
} else {
  $Python = Get-Command py -ErrorAction SilentlyContinue
  if ($Python) {
    $PythonExe = "py"
    $PythonArgs = @("-3.11")
  } else {
    $Python = Get-Command python -ErrorAction SilentlyContinue
    if (!$Python -or $Python.Source -like "*WindowsApps*") {
      Write-Error "Python 3.11 is not installed or not on PATH. Set CINEHUMAN_PYTHON to your python.exe path, or install Python 3.11 from python.org."
    }
    $PythonExe = "python"
  }
}

& $PythonExe @PythonArgs --version

if (!(Test-Path ".venv")) {
  & $PythonExe @PythonArgs -m venv .venv
}

.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\pip.exe install -r requirements-torch-cu121.txt
.\.venv\Scripts\pip.exe install -r requirements.txt
try {
  .\.venv\Scripts\pip.exe install -r requirements-optional.txt
} catch {
  Write-Warning "Optional xformers install failed. The app will still run with attention slicing and offload."
}

Push-Location frontend
npm.cmd install
Pop-Location

Write-Host "Install complete. Start backend with scripts\start_backend.ps1 and frontend with scripts\start_frontend.ps1"
