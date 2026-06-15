$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
Set-Location ..
$env:CUDA_VISIBLE_DEVICES = "0"
$env:NVIDIA_VISIBLE_DEVICES = "all"
$env:NVIDIA_DRIVER_CAPABILITIES = "compute,utility"
$env:HF_HOME = "E:\jlcpro\cinematic\models\hf-cache"
$env:HF_HUB_CACHE = "E:\jlcpro\cinematic\models\hf-cache\hub"
Remove-Item Env:\TRANSFORMERS_CACHE -ErrorAction SilentlyContinue
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
