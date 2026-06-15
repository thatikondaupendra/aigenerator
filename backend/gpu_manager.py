from __future__ import annotations

import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class GPUInfo:
    available: bool
    name: str
    total_vram_gb: float
    low_vram: bool
    device: str
    dtype: str


def get_gpu_info(low_vram_threshold_gb: float = 6.0) -> GPUInfo:
    try:
        import torch

        if not torch.cuda.is_available():
            return GPUInfo(False, "CPU", 0.0, True, "cpu", "float32")
        props = torch.cuda.get_device_properties(0)
        total_gb = props.total_memory / (1024**3)
        return GPUInfo(
            available=True,
            name=props.name,
            total_vram_gb=round(total_gb, 2),
            low_vram=total_gb < low_vram_threshold_gb,
            device="cuda",
            dtype="float16",
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("Could not inspect GPU: %s", exc)
        return GPUInfo(False, "CPU", 0.0, True, "cpu", "float32")


def empty_cache() -> None:
    try:
        import torch

        if torch.cuda.is_available():
            torch.cuda.empty_cache()
    except Exception:
        logger.debug("Unable to clear CUDA cache", exc_info=True)
