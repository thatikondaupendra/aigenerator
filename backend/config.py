from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]

os.environ.setdefault("CUDA_VISIBLE_DEVICES", "0")
os.environ.setdefault("NVIDIA_VISIBLE_DEVICES", "all")
os.environ.setdefault("NVIDIA_DRIVER_CAPABILITIES", "compute,utility")


@dataclass(frozen=True)
class Settings:
    app_name: str = "CineHuman AI Studio"
    models_dir: Path = ROOT_DIR / "models"
    outputs_dir: Path = ROOT_DIR / "outputs"
    lora_dir: Path = ROOT_DIR / "lora"
    workflows_dir: Path = ROOT_DIR / "workflows"
    hf_home: Path = ROOT_DIR / "models" / "hf-cache"
    default_width: int = 1024
    default_height: int = 1792
    default_steps: int = 30
    default_guidance_scale: float = 6.5
    max_image_size: int = 2048
    low_vram_threshold_gb: float = 6.0
    api_host: str = os.getenv("CINEHUMAN_HOST", "0.0.0.0")
    api_port: int = int(os.getenv("CINEHUMAN_PORT", "8000"))
    allow_cpu: bool = os.getenv("CINEHUMAN_ALLOW_CPU", "true").lower() == "true"


settings = Settings()

os.environ.setdefault("HF_HOME", str(settings.hf_home))
os.environ.setdefault("HF_HUB_CACHE", str(settings.hf_home / "hub"))
os.environ.setdefault("DIFFUSERS_CACHE", str(settings.hf_home / "diffusers"))


def ensure_directories() -> None:
    for directory in (
        settings.hf_home,
        settings.hf_home / "hub",
        settings.hf_home / "transformers",
        settings.hf_home / "diffusers",
        settings.models_dir / "sdxl",
        settings.models_dir / "juggernaut",
        settings.models_dir / "realvis",
        settings.models_dir / "animatediff",
        settings.models_dir / "gfpgan",
        settings.models_dir / "esrgan",
        settings.outputs_dir / "images",
        settings.outputs_dir / "enhanced",
        settings.outputs_dir / "videos",
        settings.lora_dir,
        settings.workflows_dir,
    ):
        directory.mkdir(parents=True, exist_ok=True)
