from __future__ import annotations

import asyncio
import json
import logging
import shutil
import time
from pathlib import Path
from typing import Callable

from backend.config import settings
from backend.schemas import TrainLoraRequest

logger = logging.getLogger(__name__)


class LoraManager:
    async def train(self, request: TrainLoraRequest, progress: Callable[[float], None]) -> dict[str, str]:
        return await asyncio.to_thread(self._train_sync, request, progress)

    def _train_sync(self, request: TrainLoraRequest, progress: Callable[[float], None]) -> dict[str, str]:
        dataset = Path(request.dataset_dir)
        if not dataset.exists():
            raise FileNotFoundError(f"Dataset directory not found: {dataset}")
        output_dir = settings.lora_dir / request.output_name
        output_dir.mkdir(parents=True, exist_ok=True)
        progress(0.1)

        try:
            import accelerate  # noqa: F401
        except ImportError as exc:
            raise RuntimeError("LoRA training requires accelerate and the diffusers training extras") from exc

        manifest = {
            "status": "prepared",
            "base_model": request.base_model.value,
            "rank": request.rank,
            "steps": request.steps,
            "dataset_dir": str(dataset),
            "created_at": int(time.time()),
            "note": "Dataset validated. Launch scripts/train_lora.py for full fine-tuning.",
        }
        (output_dir / "training_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        sample_files = [p for p in dataset.iterdir() if p.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}]
        for sample in sample_files[:8]:
            shutil.copy2(sample, output_dir / sample.name)
        progress(1.0)
        return {"lora_dir": str(output_dir), "manifest": str(output_dir / "training_manifest.json")}


lora_manager = LoraManager()
