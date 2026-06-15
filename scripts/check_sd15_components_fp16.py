from __future__ import annotations

import os
from pathlib import Path

os.environ.setdefault("HF_HOME", str(Path("models/hf-cache").resolve()))
os.environ.setdefault("HF_HUB_CACHE", str(Path("models/hf-cache/hub").resolve()))

import torch
from diffusers import UNet2DConditionModel


def main() -> int:
    root = Path("models/sdxl/sd15")
    print("unet fp16")
    UNet2DConditionModel.from_pretrained(
        root / "unet",
        torch_dtype=torch.float16,
        variant="fp16",
        use_safetensors=True,
    )
    print("unet fp16 ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
