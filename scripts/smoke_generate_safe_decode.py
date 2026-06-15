from __future__ import annotations

from pathlib import Path
import os

os.environ.setdefault("HF_HOME", str(Path("models/hf-cache").resolve()))
os.environ.setdefault("HF_HUB_CACHE", str(Path("models/hf-cache/hub").resolve()))

import numpy as np
import torch
from diffusers import AutoencoderKL, StableDiffusionPipeline


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
    pipe.enable_attention_slicing()
    if hasattr(pipe, "enable_vae_slicing"):
        pipe.enable_vae_slicing()
    if torch.cuda.is_available() and hasattr(pipe, "enable_model_cpu_offload"):
        pipe.enable_model_cpu_offload()

    latent_result = pipe(
        prompt="photo of a businessman in an office, realistic, detailed face",
        negative_prompt="black image, blank image, low quality, blurry, watermark, text",
        width=384,
        height=512,
        num_inference_steps=4,
        guidance_scale=5.0,
        output_type="latent",
    )
    latents = latent_result.images.detach().to("cpu", dtype=torch.float32)
    print("latents", float(torch.nan_to_num(latents).mean()), float(torch.nan_to_num(latents).std()), bool(torch.isnan(latents).any()))

    vae = AutoencoderKL.from_pretrained(
        str(model_dir / "vae"),
        torch_dtype=torch.float32,
        use_safetensors=True,
    ).to("cpu")
    with torch.no_grad():
        decoded = vae.decode(latents / vae.config.scaling_factor, return_dict=False)[0]
    print("decoded", float(torch.nan_to_num(decoded).mean()), float(torch.nan_to_num(decoded).std()), bool(torch.isnan(decoded).any()))
    image = pipe.image_processor.postprocess(decoded, output_type="pil")[0]
    path = out_dir / "smoke_test_safe_decode.png"
    image.save(path)
    arr = np.asarray(image.convert("RGB"))
    print(path)
    print("size", image.size, "mean", float(arr.mean()), "std", float(arr.std()), "min", int(arr.min()), "max", int(arr.max()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
