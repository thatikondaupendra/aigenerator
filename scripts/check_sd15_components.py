from __future__ import annotations

import os
from pathlib import Path

os.environ.setdefault("HF_HOME", str(Path("models/hf-cache").resolve()))
os.environ.setdefault("HF_HUB_CACHE", str(Path("models/hf-cache/hub").resolve()))

import torch
from diffusers import AutoencoderKL, UNet2DConditionModel
from transformers import CLIPTextModel, CLIPTokenizer


def main() -> int:
    root = Path("models/sdxl/sd15")
    print("tokenizer")
    CLIPTokenizer.from_pretrained(root / "tokenizer")
    print("text_encoder")
    CLIPTextModel.from_pretrained(root / "text_encoder", torch_dtype=torch.float32, use_safetensors=True)
    print("vae")
    AutoencoderKL.from_pretrained(root / "vae", torch_dtype=torch.float32, use_safetensors=True)
    print("unet")
    UNet2DConditionModel.from_pretrained(root / "unet", torch_dtype=torch.float32, use_safetensors=True)
    print("all components ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
