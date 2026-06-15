$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
Set-Location ..

if (!(Test-Path ".venv\Scripts\python.exe")) {
  Write-Error ".venv was not found. Run scripts\install_windows.ps1 first."
}

Write-Host "Installing CUDA PyTorch. This can take a long time on slower connections..."
.\.venv\Scripts\python.exe -m pip install --no-input --progress-bar on -r requirements-torch-cu121.txt

Write-Host "Installing backend libraries..."
.\.venv\Scripts\python.exe -m pip install --no-input --progress-bar on -r requirements.txt

Write-Host "Installing optional xformers..."
try {
  .\.venv\Scripts\python.exe -m pip install --no-input --progress-bar on -r requirements-optional.txt
} catch {
  Write-Warning "Optional xformers install failed. Continuing."
}

Write-Host "Installing frontend libraries..."
Push-Location frontend
npm.cmd install
Pop-Location

Write-Host "Install complete."
