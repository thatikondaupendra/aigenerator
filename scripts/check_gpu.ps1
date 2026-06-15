$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
Set-Location ..

$env:CUDA_VISIBLE_DEVICES = "0"
$env:NVIDIA_VISIBLE_DEVICES = "all"
$env:NVIDIA_DRIVER_CAPABILITIES = "compute,utility"
.\.venv\Scripts\python.exe -c "import torch; print('CUDA available:', torch.cuda.is_available()); print('Device count:', torch.cuda.device_count()); print('Device 0:', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'none')"
nvidia-smi
