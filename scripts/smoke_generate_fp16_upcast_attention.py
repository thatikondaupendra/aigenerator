from __future__ import annotations

import os
from pathlib import Path

os.environ.setdefault("HF_HOME", str(Path("models/hf-cache").resolve()))
os.environ.setdefault("HF_HUB_CACHE", str(Path("models/hf-cache/hub").resolve()))

import numpy as np
import torch
from diffusers import DPMSolverMultistepScheduler, StableDiffusionPipeline


def main() -> int:
    model_dir = Path("models/sdxl/sd15")
    out_dir = Path("outputs/images")
    out_dir.mkdir(parents=True, exist_ok=True)

    pipe = StableDiffusionPipeline.from_pretrained(
        str(model_dir),
        torch_dtype=torch.float16,
        variant="fp16",
        use_safetensors=True,
        safety_checker=None,
        requires_safety_checker=False,
    )
    pipe.scheduler = DPMSolverMultistepScheduler.from_config(pipe.scheduler.config)
    pipe.unet.config.upcast_attention = True
    pipe.enable_attention_slicing()
    if hasattr(pipe, "enable_vae_slicing"):
        pipe.enable_vae_slicing()
    if torch.cuda.is_available() and hasattr(pipe, "enable_model_cpu_offload"):
        pipe.enable_model_cpu_offload()

    image = pipe(
        prompt="photo of a businessman in an office, realistic, detailed face",
        negative_prompt="black image, blank image, low quality, blurry, watermark, text",
        width=384,
        height=512,
        num_inference_steps=4,
        guidance_scale=4.0,
    ).images[0]
    path = out_dir / "smoke_test_fp16_upcast_attention.png"
    image.save(path)
    arr = np.asarray(image.convert("RGB"))
    print(path)
    print("size", image.size, "mean", float(arr.mean()), "std", float(arr.std()), "min", int(arr.min()), "max", int(arr.max()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
