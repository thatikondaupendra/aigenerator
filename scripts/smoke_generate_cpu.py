from __future__ import annotations

from pathlib import Path
import os

os.environ.setdefault("HF_HOME", str(Path("models/hf-cache").resolve()))
os.environ.setdefault("HF_HUB_CACHE", str(Path("models/hf-cache/hub").resolve()))

import numpy as np
import torch
from diffusers import StableDiffusionPipeline


def run() -> int:
    torch.set_num_threads(1)
    model_dir = Path("models/sdxl/sd15")
    out_dir = Path("outputs/images")
    out_dir.mkdir(parents=True, exist_ok=True)

    pipe = StableDiffusionPipeline.from_pretrained(
        str(model_dir),
        torch_dtype=torch.float32,
        use_safetensors=True,
        safety_checker=None,
        requires_safety_checker=False,
    ).to("cpu")
    pipe.enable_attention_slicing()

    image = pipe(
        prompt="photo of a businessman in an office, realistic, detailed face",
        negative_prompt="black image, blank image, low quality, blurry, watermark, text",
        width=128,
        height=128,
        num_inference_steps=1,
        guidance_scale=4.0,
    ).images[0]
    path = out_dir / "smoke_test_cpu.png"
    image.save(path)
    arr = np.asarray(image.convert("RGB"))
    print(path)
    print("size", image.size, "mean", float(arr.mean()), "std", float(arr.std()), "min", int(arr.min()), "max", int(arr.max()))
    return 0


def main() -> int:
    try:
        return run()
    except Exception:
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
