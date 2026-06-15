# CineHuman AI Studio - Setup & Troubleshooting Guide

## Quick Start (Windows)

### Option 1: All-in-One Script (Recommended)
```powershell
powershell -ExecutionPolicy Bypass -File scripts\launch_all.ps1
```
This will:
- Verify environment setup
- Start backend on port 8000
- Start frontend on port 5173
- Auto-open browser

### Option 2: Manual Start
```powershell
# Terminal 1 - Backend
powershell -ExecutionPolicy Bypass -File scripts\start_backend.ps1

# Terminal 2 - Frontend
powershell -ExecutionPolicy Bypass -File scripts\start_frontend.ps1
```

### Option 3: Docker
```bash
docker compose up --build
```

## Quick Start (Linux/Mac)

```bash
chmod +x scripts/*.sh
scripts/install_linux.sh
scripts/start_backend.sh &
scripts/start_frontend.sh &
```

Open `http://localhost:5173`

## Troubleshooting

### Black Screen Issue
**Symptoms**: Frontend loads but displays only black area

**Solutions**:
1. Clear browser cache: `Ctrl+Shift+Delete` → Clear all
2. Hard refresh: `Ctrl+Shift+R`
3. Check backend connection:
   ```powershell
   powershell -ExecutionPolicy Bypass -File scripts\check_backend.ps1
   ```
4. Check browser console for errors: `F12` → Console tab
5. Verify backend is running: `http://localhost:8000/health`

### API Connection Errors
**Symptoms**: "Generation failed: API error" or "Network error"

**Solutions**:
1. Ensure backend is running:
   ```powershell
   curl http://localhost:8000/health
   ```
2. Check port 8000 is not in use:
   ```powershell
   netstat -ano | findstr :8000
   ```
3. Verify CORS is enabled (should be by default)
4. Check firewall isn't blocking connections

### GPU Not Detected
**Symptoms**: Slow generation or CPU-only mode

**Solutions**:
1. Check GPU status:
   ```powershell
   powershell -ExecutionPolicy Bypass -File scripts\check_gpu.ps1
   ```
2. Verify CUDA/cuDNN installation
3. Ensure NVIDIA drivers are up-to-date
4. Check VRAM usage:
   ```powershell
   nvidia-smi
   ```
5. For low VRAM (<6GB), SD1.5 mode auto-activates

### Model Download Failures
**Symptoms**: "Model download failed" or hung on download

**Solutions**:
1. Ensure internet connection
2. Check Hugging Face token if private models:
   ```bash
   huggingface-cli login
   ```
3. Manual download to models/ directory
4. Check disk space (models are 5-20GB each)
5. Restart backend to retry downloads

### Frontend Build Issues
**Symptoms**: Blank page or console errors

**Solutions**:
1. Reinstall dependencies:
   ```powershell
   cd frontend
   rm node_modules
   npm install
   ```
2. Clear npm cache:
   ```powershell
   npm cache clean --force
   ```
3. Check Node version (requires >=18):
   ```powershell
   node --version
   ```

### Memory/Out of Memory
**Symptoms**: Generation stops abruptly or "CUDA out of memory"

**Solutions**:
1. Reduce image resolution (max 2048x2048)
2. Reduce steps (default 16-30)
3. Enable low VRAM mode by setting env var:
   ```powershell
   $env:CINEHUMAN_ALLOW_CPU = "false"
   ```
4. Close other GPU applications
5. Check GPU memory:
   ```powershell
   nvidia-smi
   ```

## Health Checks

### Backend Health
```bash
curl http://localhost:8000/health
```

### Model Status
```bash
curl http://localhost:8000/models/status
```

### API Documentation
Visit `http://localhost:8000/docs` (Swagger UI)

## Environment Variables

```powershell
# GPU Settings
$env:CUDA_VISIBLE_DEVICES = "0"           # GPU device ID
$env:NVIDIA_VISIBLE_DEVICES = "all"       # All available GPUs
$env:CINEHUMAN_ALLOW_CPU = "false"        # Disallow CPU mode

# API Settings
$env:CINEHUMAN_HOST = "0.0.0.0"           # API host
$env:CINEHUMAN_PORT = "8000"              # API port

# Model Storage
$env:HF_HOME = "models/hf-cache"          # Hugging Face cache
$env:HF_HUB_CACHE = "models/hf-cache/hub"
```

## Project Structure

```
cinematic/
├── backend/              # FastAPI backend
│   ├── main.py          # Entry point
│   ├── generator.py     # Image generation
│   ├── video_generator.py
│   ├── enhancer.py      # Image enhancement
│   ├── gpu_manager.py   # GPU utilities
│   └── ...
├── frontend/            # React + Vite frontend
│   ├── src/
│   │   ├── main.jsx     # App component
│   │   └── styles.css
│   ├── index.html
│   └── vite.config.js
├── models/              # Model storage
│   ├── hf-cache/        # Downloaded models
│   ├── sdxl/
│   ├── juggernaut/
│   └── ...
├── outputs/             # Generated content
│   ├── images/
│   ├── videos/
│   └── enhanced/
└── scripts/             # Helper scripts
    ├── install_windows.ps1
    ├── start_backend.ps1
    ├── start_frontend.ps1
    ├── launch_all.ps1
    └── check_backend.ps1
```

## Ports

- **Frontend**: `http://localhost:5173`
- **Backend API**: `http://localhost:8000`
- **API Docs**: `http://localhost:8000/docs`
- **Health Check**: `http://localhost:8000/health`

## Performance Tips

1. **First generation is slow** - models are downloading and compiling
2. **Use appropriate resolution** - 512x640 is fast, 1024x1792 is quality
3. **Reduce steps** - 16-20 is good, 30+ is for high quality
4. **Reuse models** - same model stays in memory for faster subsequent uses
5. **Enable xFormers** - automatic if available, saves memory

## Common Errors & Fixes

| Error | Cause | Fix |
|-------|-------|-----|
| "Module not found" | Missing dependencies | `npm install` / `pip install -r requirements.txt` |
| "CUDA out of memory" | Image too large | Reduce resolution or use low VRAM mode |
| "Cannot connect to API" | Backend not running | Start backend with `start_backend.ps1` |
| "Black screen" | CSS not loading | Clear cache and hard refresh (Ctrl+Shift+R) |
| "Model download failed" | Network issue | Check internet, restart backend |
| "Port already in use" | Another app using port | Kill process or change port |

## Advanced Debugging

### Backend Logs
```powershell
# Run with verbose output
$pythonPath = ".\.venv\Scripts\python.exe"
& $pythonPath -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --log-level debug
```

### Frontend Logs
```powershell
# Open DevTools
# Browser: F12 or Ctrl+Shift+I
# Check Console tab for errors
```

### Check System Resources
```powershell
# GPU
nvidia-smi -l 1

# CPU & Memory
Get-Process | Sort-Object Memory -Descending | Select-Object -First 10

# Disk Space
Get-Volume
```

## Getting Help

1. Check logs in terminal output
2. Run health checks: `scripts\check_backend.ps1`
3. Review this troubleshooting guide
4. Check project README.md
5. Enable debug logging in terminal

---

**Last Updated**: 2026-06-14
**Backend**: FastAPI, Python 3.11+
**Frontend**: React 18+, Vite, Tailwind CSS
