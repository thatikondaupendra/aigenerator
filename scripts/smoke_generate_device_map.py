from __future__ import annotations

import os
from pathlib import Path

os.environ.setdefault("HF_HOME", str(Path("models/hf-cache").resolve()))
os.environ.setdefault("HF_HUB_CACHE", str(Path("models/hf-cache/hub").resolve()))

import numpy as np
import torch
from diffusers import StableDiffusionPipeline


def main() -> int:
    model_dir = Path("models/sdxl/sd15")
    out_dir = Path("outputs/images")
    offload_dir = Path("models/offload")
    out_dir.mkdir(parents=True, exist_ok=True)
    offload_dir.mkdir(parents=True, exist_ok=True)

    pipe = StableDiffusionPipeline.from_pretrained(
        str(model_dir),
        torch_dtype=torch.float32,
        use_safetensors=True,
        safety_checker=None,
        requires_safety_checker=False,
        device_map="balanced",
        max_memory={0: "2800MiB", "cpu": "12000MiB"},
        offload_folder=str(offload_dir),
    )
    pipe.enable_attention_slicing()

    image = pipe(
        prompt="photo of a businessman in an office, realistic, detailed face",
        negative_prompt="black image, blank image, low quality, blurry, watermark, text",
        width=256,
        height=384,
        num_inference_steps=1,
        guidance_scale=4.0,
    ).images[0]
    path = out_dir / "smoke_test_device_map.png"
    image.save(path)
    arr = np.asarray(image.convert("RGB"))
    print(path)
    print("size", image.size, "mean", float(arr.mean()), "std", float(arr.std()), "min", int(arr.min()), "max", int(arr.max()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
