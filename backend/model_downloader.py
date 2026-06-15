from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

from backend.config import settings

logger = logging.getLogger(__name__)


MODEL_REPOS: dict[str, str] = {
    "sdxl": "stabilityai/stable-diffusion-xl-base-1.0",
    "sd15": "runwayml/stable-diffusion-v1-5",
    "sd15_tiny": "nota-ai/bk-sdm-tiny",
    "juggernaut": "RunDiffusion/Juggernaut-XL-v9",
    "realvis": "SG161222/RealVisXL_V5.0",
    "dreamshaper": "Lykon/dreamshaper-xl-1-0",
    "animatediff": "guoyww/animatediff-motion-adapter-v1-5-2",
    "svd": "stabilityai/stable-video-diffusion-img2vid-xt",
    "gfpgan": "TencentARC/GFPGAN",
    "realesrgan": "ai-forever/Real-ESRGAN",
}

MODEL_ALLOW_PATTERNS: dict[str, list[str]] = {
    "sd15": [
        "model_index.json",
        "scheduler/*",
        "tokenizer/*",
        "feature_extractor/*",
        "text_encoder/config.json",
        "text_encoder/model.fp16.safetensors",
        "unet/config.json",
        "unet/diffusion_pytorch_model.fp16.safetensors",
        "unet/diffusion_pytorch_model.safetensors",
        "vae/config.json",
        "vae/diffusion_pytorch_model.fp16.safetensors",
        "vae/diffusion_pytorch_model.safetensors",
        "vae/diffusion_pytorch_model.bin",
    ],
    "sd15_tiny": [
        "model_index.json",
        "scheduler/*",
        "tokenizer/*",
        "feature_extractor/*",
        "text_encoder/config.json",
        "text_encoder/model.fp16.safetensors",
        "text_encoder/model.safetensors",
        "unet/config.json",
        "unet/diffusion_pytorch_model.fp16.bin",
        "unet/diffusion_pytorch_model.bin",
        "unet/diffusion_pytorch_model.fp16.safetensors",
        "unet/diffusion_pytorch_model.safetensors",
        "vae/config.json",
        "vae/diffusion_pytorch_model.fp16.bin",
        "vae/diffusion_pytorch_model.bin",
        "vae/diffusion_pytorch_model.fp16.safetensors",
        "vae/diffusion_pytorch_model.safetensors",
    ],
    "sdxl": [
        "model_index.json",
        "scheduler/*",
        "tokenizer/*",
        "tokenizer_2/*",
        "text_encoder/config.json",
        "text_encoder/model.fp16.safetensors",
        "text_encoder_2/config.json",
        "text_encoder_2/model.fp16.safetensors",
        "unet/config.json",
        "unet/diffusion_pytorch_model.fp16.safetensors",
        "vae/config.json",
        "vae/diffusion_pytorch_model.safetensors",
    ],
}

MODEL_REQUIRED_FILES: dict[str, list[str]] = {
    "sd15": [
        "model_index.json",
        "scheduler/scheduler_config.json",
        "tokenizer/tokenizer_config.json",
        "tokenizer/vocab.json",
        "text_encoder/config.json",
        "text_encoder/model.fp16.safetensors",
        "unet/config.json",
        "unet/diffusion_pytorch_model.fp16.safetensors",
        "vae/config.json",
        "vae/diffusion_pytorch_model.fp16.safetensors",
    ],
    "sd15_tiny": [
        "model_index.json",
        "scheduler/scheduler_config.json",
        "tokenizer/tokenizer_config.json",
        "tokenizer/vocab.json",
        "text_encoder/config.json",
        "unet/config.json",
        "vae/config.json",
    ],
    "sdxl": [
        "model_index.json",
        "scheduler/scheduler_config.json",
        "tokenizer/tokenizer_config.json",
        "tokenizer_2/tokenizer_config.json",
        "text_encoder/config.json",
        "text_encoder_2/config.json",
        "unet/config.json",
        "vae/config.json",
    ],
}


def model_path(key: str) -> Path:
    mapping = {
        "sdxl": settings.models_dir / "sdxl",
        "juggernaut": settings.models_dir / "juggernaut",
        "realvis": settings.models_dir / "realvis",
        "dreamshaper": settings.models_dir / "sdxl" / "dreamshaper",
        "sd15": settings.models_dir / "sdxl" / "sd15",
        "sd15_tiny": settings.models_dir / "sdxl" / "sd15_tiny",
        "animatediff": settings.models_dir / "animatediff",
        "gfpgan": settings.models_dir / "gfpgan",
        "realesrgan": settings.models_dir / "esrgan",
        "svd": settings.models_dir / "animatediff" / "svd",
    }
    return mapping[key]


def ensure_model(key: str) -> Path:
    if key not in MODEL_REPOS:
        raise ValueError(f"Unknown model key: {key}")
    destination = model_path(key)
    destination.mkdir(parents=True, exist_ok=True)
    marker = destination / ".download-complete"
    if marker.exists() and _required_files_exist(key, destination):
        return destination
    if marker.exists():
        logger.warning("Model marker exists but required files are missing for %s; repairing download", key)
        marker.unlink()

    if key == "sd15_tiny" and not _required_files_exist(key, destination):
        missing = _missing_required_files(key, destination)
        raise RuntimeError(
            "Low-VRAM model sd15_tiny is incomplete. Missing files: "
            + ", ".join(missing)
            + ". Download the missing model files first; generation was not started."
        )

    try:
        from huggingface_hub import snapshot_download
    except ImportError as exc:
        raise RuntimeError("huggingface_hub is required for automatic model downloads") from exc

    logger.info("Downloading %s from %s into %s", key, MODEL_REPOS[key], destination)
    os.environ.setdefault("HF_HOME", str(settings.hf_home))
    kwargs = {
        "repo_id": MODEL_REPOS[key],
        "local_dir": destination,
    }
    if key in MODEL_ALLOW_PATTERNS:
        kwargs["allow_patterns"] = MODEL_ALLOW_PATTERNS[key]
    snapshot_download(
        **kwargs,
    )
    marker.write_text(MODEL_REPOS[key], encoding="utf-8")
    return destination


def _required_files_exist(key: str, destination: Path) -> bool:
    required = MODEL_REQUIRED_FILES.get(key)
    if not required:
        return True
    if not all((destination / relative_path).exists() for relative_path in required):
        return False
    if key == "sd15_tiny":
        return (
            _any_exists(
                destination,
                [
                    "text_encoder/model.fp16.safetensors",
                    "text_encoder/model.safetensors",
                    "text_encoder/pytorch_model.fp16.bin",
                    "text_encoder/pytorch_model.bin",
                ],
            )
            and _any_exists(
                destination,
                [
                    "unet/diffusion_pytorch_model.fp16.safetensors",
                    "unet/diffusion_pytorch_model.safetensors",
                    "unet/diffusion_pytorch_model.fp16.bin",
                    "unet/diffusion_pytorch_model.bin",
                ],
            )
            and _any_exists(
                destination,
                [
                    "vae/diffusion_pytorch_model.fp16.safetensors",
                    "vae/diffusion_pytorch_model.safetensors",
                    "vae/diffusion_pytorch_model.fp16.bin",
                    "vae/diffusion_pytorch_model.bin",
                ],
            )
        )
    return True


def _missing_required_files(key: str, destination: Path) -> list[str]:
    required = MODEL_REQUIRED_FILES.get(key, [])
    missing = [relative_path for relative_path in required if not (destination / relative_path).exists()]
    if key == "sd15_tiny":
        groups = {
            "text encoder weights": [
                "text_encoder/model.fp16.safetensors",
                "text_encoder/model.safetensors",
                "text_encoder/pytorch_model.fp16.bin",
                "text_encoder/pytorch_model.bin",
            ],
            "unet weights": [
                "unet/diffusion_pytorch_model.fp16.safetensors",
                "unet/diffusion_pytorch_model.safetensors",
                "unet/diffusion_pytorch_model.fp16.bin",
                "unet/diffusion_pytorch_model.bin",
            ],
            "vae weights": [
                "vae/diffusion_pytorch_model.fp16.safetensors",
                "vae/diffusion_pytorch_model.safetensors",
                "vae/diffusion_pytorch_model.fp16.bin",
                "vae/diffusion_pytorch_model.bin",
            ],
        }
        missing.extend(name for name, options in groups.items() if not _any_exists(destination, options))
    return missing


def _any_exists(destination: Path, relative_paths: list[str]) -> bool:
    return any((destination / relative_path).exists() for relative_path in relative_paths)


def model_status() -> dict[str, dict[str, Any]]:
    status: dict[str, dict[str, Any]] = {}
    for key in MODEL_REPOS:
        path = model_path(key)
        files = [item for item in path.rglob("*") if item.is_file()] if path.exists() else []
        lock_files = [str(item) for item in path.rglob("*.lock")] if path.exists() else []
        status[key] = {
            "path": str(path),
            "exists": path.exists(),
            "download_complete": (path / ".download-complete").exists(),
            "file_count": len(files),
            "size_mb": round(sum(item.stat().st_size for item in files) / (1024 * 1024), 2),
            "lock_count": len(lock_files),
            "locks": lock_files[:10],
        }
    return status
