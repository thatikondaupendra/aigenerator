# CineHuman AI Studio - Quick Reference

## 🚀 Quick Start
```powershell
powershell -ExecutionPolicy Bypass -File scripts\launch_all.ps1
```
Opens browser to http://localhost:5173

## 📍 Access Points
| Component | URL | Purpose |
|-----------|-----|---------|
| Frontend | http://localhost:5173 | Image generation UI |
| Backend | http://localhost:8000 | API server |
| API Docs | http://localhost:8000/docs | Swagger documentation |
| Health Check | http://localhost:8000/health | Server status |

## ⚙️ Environment Variables
```powershell
$env:CINEHUMAN_HOST = "0.0.0.0"
$env:CINEHUMAN_PORT = "8000"
$env:HF_HOME = "models/hf-cache"
$env:CUDA_VISIBLE_DEVICES = "0"
```

## 🔧 Manual Start
```powershell
# Terminal 1 - Backend
scripts\start_backend.ps1

# Terminal 2 - Frontend  
scripts\start_frontend.ps1
```

## 📊 Health Checks
```powershell
# Backend running?
curl http://localhost:8000/health

# Frontend running?
curl http://localhost:5173

# Check backend diagnostics
powershell -ExecutionPolicy Bypass -File scripts\check_backend.ps1
```

## 🐳 Docker
```bash
# Build and start
docker compose up --build

# Stop
docker compose down

# View logs
docker compose logs -f
```

## 🎨 Features
- ✅ Photorealistic image generation (SDXL, Juggernaut, RealVis, SD1.5)
- ✅ Image enhancement (GFPGAN, Real-ESRGAN)
- ✅ Image-to-video (AnimateDiff or OpenCV fallback)
- ✅ LoRA fine-tuning support
- ✅ Auto GPU detection with fallback
- ✅ Web UI with real-time job tracking

## 💡 Common Issues

| Issue | Fix |
|-------|-----|
| Black screen | Hard refresh: Ctrl+Shift+R |
| API connection error | Check backend: `curl http://localhost:8000/health` |
| Port in use | `netstat -ano \| findstr :8000` then kill process |
| GPU not detected | Run `nvidia-smi` to verify CUDA |
| Out of memory | Reduce resolution or steps |
| Models stuck downloading | Kill process and restart backend |

## 📝 Key Commands

```powershell
# Install dependencies (if missing)
npm install --legacy-peer-deps

# Build frontend
npm run build

# Clean everything
Remove-Item -Path .venv, node_modules, dist -Recurse

# Check Python version
python --version
# Should be 3.11+

# Check Node version
node --version
# Should be 18+
```

## 🔍 Advanced Debugging

```powershell
# Backend with debug logging
$pythonPath = ".\.venv\Scripts\python.exe"
& $pythonPath -m uvicorn backend.main:app --log-level debug

# Frontend with sourcemaps
npm run dev

# GPU monitoring
nvidia-smi -l 1  # Refresh every second

# Check processes
Get-Process python, node | Format-Table Name, Memory
```

## 📚 Documentation Files
- `README.md` - Project overview
- `TROUBLESHOOTING.md` - Common issues & fixes (200+ lines)
- `PROJECT_STATUS.md` - Complete fix summary
- `THIS FILE` - Quick reference

## 🎯 Workflow Example

1. **Start services**
   ```powershell
   scripts\launch_all.ps1
   ```

2. **Open UI**
   - Browser auto-opens to http://localhost:5173

3. **Generate image**
   - Enter prompt
   - Select template/model
   - Click "Generate Image"
   - Wait for completion

4. **Enhance image**
   - Click "Enhance" button
   - Wait for upscaling

5. **Create video**
   - Click "Video" button
   - Download MP4 from jobs panel

## 🏁 Performance Tips
- First run is slow (model loading + compilation)
- 512x640 = fast (~30s on RTX 3060)
- 1024x1792 = quality (~2min on RTX 3060)
- Lower steps = faster (16 is minimum)
- Same model stays in memory = faster reuse

## ⚡ One-Liners

```powershell
# Check if everything works
curl http://localhost:8000/health; curl http://localhost:5173

# Kill all Python processes
Get-Process python | Stop-Process -Force

# Kill all Node processes
Get-Process node | Stop-Process -Force

# View backend logs live
Get-Content -Path "*.log" -Tail 50 -Wait
```

## 🆘 Emergency Fixes

```powershell
# Clear everything and start fresh
Remove-Item -Path ".venv", "node_modules", "dist" -Recurse -Force
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
cd frontend && npm install
cd ..

# Then restart
scripts\launch_all.ps1
```

---

**For detailed help, see**: `TROUBLESHOOTING.md`  
**For complete fixes**, see: `PROJECT_STATUS.md`
