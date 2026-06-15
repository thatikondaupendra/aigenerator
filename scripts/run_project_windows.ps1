$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
Set-Location ..

if (!(Test-Path ".venv\Scripts\python.exe")) {
  Write-Error ".venv is missing. Run scripts\continue_install_windows.ps1 first."
}

Write-Host "Starting CineHuman backend on http://127.0.0.1:8000"
Start-Process powershell.exe -ArgumentList @(
  "-NoExit",
  "-ExecutionPolicy", "Bypass",
  "-Command",
  "cd 'E:\jlcpro\cinematic'; `$env:CUDA_VISIBLE_DEVICES='0'; `$env:NVIDIA_VISIBLE_DEVICES='all'; `$env:NVIDIA_DRIVER_CAPABILITIES='compute,utility'; `$env:HF_HOME='E:\jlcpro\cinematic\models\hf-cache'; `$env:HF_HUB_CACHE='E:\jlcpro\cinematic\models\hf-cache\hub'; Remove-Item Env:\TRANSFORMERS_CACHE -ErrorAction SilentlyContinue; .\.venv\Scripts\python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8000"
)

Write-Host "Starting CineHuman frontend on http://localhost:5173"
Start-Process powershell.exe -ArgumentList @(
  "-NoExit",
  "-ExecutionPolicy", "Bypass",
  "-Command",
  "cd 'E:\jlcpro\cinematic\frontend'; npm.cmd run dev"
)

Write-Host "Open http://localhost:5173 after both windows finish starting."
