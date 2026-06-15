# CineHuman AI Studio

Full-stack local AI studio for cinematic photorealistic human image generation, enhancement, and short image-to-video motion using free and open-source model families.

## Hardware Targets

- Primary: NVIDIA RTX 3060 12GB
- Low VRAM: GPUs under 6GB automatically switch to SD1.5 mode
- CPU startup is allowed for API inspection, but real generation is impractically slow

## Stack

- Backend: Python 3.11, FastAPI, PyTorch, Diffusers, Transformers, Accelerate, xFormers
- Frontend: React, Vite, Tailwind CSS
- Image models: SDXL, JuggernautXL, RealVisXL, DreamShaper XL, SD1.5 fallback
- Motion: AnimateDiff image-to-video when installed, with an OpenCV cinematic motion fallback
- Enhancement: GFPGAN and Real-ESRGAN, with safe fallback behavior if weights are unavailable

## Quick Start on Windows

```powershell
powershell -ExecutionPolicy Bypass -File scripts\install_windows.ps1
powershell -ExecutionPolicy Bypass -File scripts\start_backend.ps1
powershell -ExecutionPolicy Bypass -File scripts\start_frontend.ps1
```

Open `http://localhost:5173`.

If the dependency install is interrupted, resume it with:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\continue_install_windows.ps1
```

To launch backend and frontend in separate PowerShell windows:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\run_project_windows.ps1
```

## Quick Start on Google Colab

Use a GPU runtime, clone or upload this project, then run these cells from the project root.

```bash
pip install -r requirements.txt
cd frontend && npm install && cd ..
```

Start the backend:

```bash
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

In another cell, start the frontend:

```bash
cd frontend
npm run dev -- --host 0.0.0.0 --port 5173
```

Open the Colab forwarded `5173-...colab.dev` URL. The frontend automatically calls the matching `8000-...colab.dev` backend URL. If the UI says the API is offline, open the matching backend health URL once in the browser:

```text
https://8000-<same-colab-host>/health
```

Do not set `VITE_API_BASE=http://localhost:8000` in Colab unless you are opening the frontend on the same machine. Browser requests need the forwarded Colab `8000-...` URL.

## Quick Start on Linux

```bash
chmod +x scripts/*.sh
scripts/install_linux.sh
scripts/start_backend.sh
scripts/start_frontend.sh
```

Open `http://localhost:5173`.

## Docker

Install NVIDIA Container Toolkit first, then run:

```bash
docker compose up --build
```

Backend: `http://localhost:8000`  
Frontend: `http://localhost:5173`

## Model Storage

Models are downloaded on first use from Hugging Face into:

```text
models/
  sdxl/
  juggernaut/
  realvis/
  animatediff/
  gfpgan/
  esrgan/
```

Some model repositories require accepting licenses on Hugging Face before download. If a download fails, log in with `huggingface-cli login`.

## API

### POST `/generate-image`

```json
{
  "prompt": "Ultra realistic Indian businessman in luxury office",
  "template": "cinematic_male",
  "model": "auto",
  "width": 1024,
  "height": 1792,
  "steps": 30,
  "guidance_scale": 6.5
}
```

### POST `/enhance-image`

```json
{
  "image_path": "outputs/images/image.png",
  "face_enhancer": "gfpgan",
  "upscale": 2
}
```

### POST `/generate-video`

```json
{
  "image_path": "outputs/images/image.png",
  "seconds": 5,
  "fps": 24,
  "prompt": "blinking eyes, breathing motion, slow camera pan, subtle hair movement"
}
```

### POST `/train-lora`

```json
{
  "dataset_dir": "datasets/character-a",
  "output_name": "character-a",
  "base_model": "sdxl",
  "rank": 16,
  "steps": 1000
}
```

### GET `/jobs/{id}`

Returns queue status, progress, result paths, or errors.

## VRAM Optimization

The backend enables CUDA fp16, attention slicing, xFormers when available, model CPU offload in low VRAM mode, and tiled VAE for supported pipelines.

`xformers` is optional on Windows. If it fails to install, the backend still runs with attention slicing and offload.

## Prompt Templates

- `cinematic_male`
- `kitchen_scene`
- `luxury_scene`

The default negative prompt filters low quality, blur, watermarks, text, logos, malformed anatomy, extra fingers, duplicate limbs, and distorted faces.

## LoRA Training

The API validates the dataset and prepares a training manifest. For long-running training, use:

```bash
python scripts/train_lora.py --dataset-dir datasets/character-a --output-dir lora/character-a --steps 1000
```

For production training, install the Diffusers example scripts or run this command from a Diffusers checkout that contains `train_text_to_image_lora_sdxl.py`.

## Notes

- First generation can take a long time because models download automatically.
- RTX 3060 12GB is best with SDXL at 1024px width and 1536-1792px height, 25-35 steps.
- For 4GB GPUs, use `model: "auto"` or `model: "sd15"` and reduce resolution.
