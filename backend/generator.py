from __future__ import annotations

import asyncio
import logging
import time
from pathlib import Path
from typing import Callable

import numpy as np
from PIL import Image

from backend.config import settings
from backend.gpu_manager import empty_cache, get_gpu_info
from backend.model_downloader import ensure_model
from backend.prompt_engine import build_negative_prompt, build_prompt
from backend.schemas import GenerateImageRequest, ImageModel

logger = logging.getLogger(__name__)


class ImageGenerator:
    def __init__(self) -> None:
        self._pipeline = None
        self._loaded_model_key: str | None = None
        self._decode_vae = None

    async def generate(
        self, request: GenerateImageRequest, progress: Callable[[float], None]
    ) -> dict[str, str | int | float]:
        return await asyncio.to_thread(self._generate_sync, request, progress)

    def _select_model(self, requested: ImageModel) -> str:
        gpu = get_gpu_info(settings.low_vram_threshold_gb)
        if requested != ImageModel.auto:
            return requested.value
        if gpu.total_vram_gb and gpu.total_vram_gb < 6:
            return "sd15_tiny"
        if gpu.total_vram_gb and gpu.total_vram_gb < 10:
            return "sd15"
        return "sdxl"

    def _generate_sync(
        self, request: GenerateImageRequest, progress: Callable[[float], None]
    ) -> dict[str, str | int | float]:
        progress(0.05)
        model_key = self._select_model(request.model)
        width, height, steps = self._runtime_size(request, model_key)
        logger.info(
            "Preparing image generation: model=%s size=%sx%s steps=%s prompt=%r",
            model_key,
            width,
            height,
            steps,
            request.prompt[:120],
        )
        prompt = build_prompt(request.prompt, request.template)
        negative_prompt = build_negative_prompt(request.negative_prompt)
        fallback_reason: str | None = None
        image: Image.Image | None = None

        try:
            pipe = self._load_pipeline(model_key)
            progress(0.25)

            generator = None
            if request.seed is not None:
                import torch

                generator = torch.Generator(device=get_gpu_info().device).manual_seed(request.seed)

            for lora_path in request.lora_paths:
                path = Path(lora_path)
                if path.exists() and hasattr(pipe, "load_lora_weights"):
                    pipe.load_lora_weights(str(path))

            result = self._run_pipeline(
                pipe,
                prompt,
                negative_prompt,
                width,
                height,
                steps,
                self._runtime_guidance(request.guidance_scale, model_key),
                generator,
            )
            progress(0.85)
            image = result.images[0]

            if self._is_bad_image(image):
                logger.warning("Generated image was invalid/black; retrying once with safer settings")
                empty_cache()
                result = self._run_pipeline(pipe, prompt, negative_prompt, width, height, max(4, steps // 2), 1.0, generator)
                image = result.images[0]

            if self._is_bad_image(image):
                fallback_reason = "model returned black or invalid pixels"
        except Exception as exc:  # noqa: BLE001 - API job should return a visible artifact, not a dead UI.
            logger.exception("Image generation failed; creating visible fallback image")
            fallback_reason = str(exc)

        if image is None or fallback_reason:
            raise RuntimeError(f"Image generation did not produce valid pixels: {fallback_reason or 'unknown failure'}")

        progress(0.9)
        filename = f"image_{int(time.time())}_{request.seed or 'random'}.png"
        output_path = settings.outputs_dir / "images" / filename
        image.save(output_path)
        empty_cache()
        logger.info("Image generation completed: %s", output_path)
        return {
            "image_path": str(output_path),
            "model": model_key,
            "width": width,
            "height": height,
            "seed": request.seed or -1,
            "fallback": bool(fallback_reason),
            "fallback_reason": fallback_reason or "",
        }

    def _run_pipeline(self, pipe, prompt, negative_prompt, width, height, steps, guidance_scale, generator):
        if getattr(pipe, "_cinehuman_safe_vae", False):
            import torch

            latent_result = pipe(
                prompt=prompt,
                negative_prompt=negative_prompt,
                width=width,
                height=height,
                num_inference_steps=steps,
                guidance_scale=guidance_scale,
                generator=generator,
                output_type="latent",
            )
            latents = latent_result.images.detach().to("cpu", dtype=torch.float32)
            vae = self._decode_vae
            if vae is None:
                raise RuntimeError("Safe VAE decoder was not initialized")
            with torch.no_grad():
                decoded = vae.decode(latents / vae.config.scaling_factor, return_dict=False)[0]
            images = pipe.image_processor.postprocess(decoded, output_type="pil")
            return type("PipelineImageResult", (), {"images": images})()

        return pipe(
            prompt=prompt,
            negative_prompt=negative_prompt,
            width=width,
            height=height,
            num_inference_steps=steps,
            guidance_scale=guidance_scale,
            generator=generator,
        )

    @staticmethod
    def _is_bad_image(image: Image.Image) -> bool:
        data = np.asarray(image.convert("RGB"), dtype=np.float32)
        if not np.isfinite(data).all():
            return True
        return float(data.mean()) < 3.0 and float(data.std()) < 3.0

    def _runtime_size(self, request: GenerateImageRequest, model_key: str) -> tuple[int, int, int]:
        gpu = get_gpu_info(settings.low_vram_threshold_gb)
        width = request.width
        height = request.height
        steps = request.steps

        if model_key == "sd15_tiny":
            if height >= width:
                width, height = 256, 384
            else:
                width, height = 384, 256
            steps = min(steps, 12)
        elif model_key == "sd15":
            max_pixels = 512 * 768 if gpu.total_vram_gb >= 6 else 384 * 512
            pixels = width * height
            if pixels > max_pixels:
                scale = (max_pixels / pixels) ** 0.5
                width = max(320, int(width * scale) // 64 * 64)
                height = max(320, int(height * scale) // 64 * 64)
            steps = min(steps, 24 if gpu.total_vram_gb >= 6 else 12)
        elif model_key == "sdxl" and gpu.total_vram_gb and gpu.total_vram_gb < 14:
            max_pixels = 768 * 1024
            pixels = width * height
            if pixels > max_pixels:
                scale = (max_pixels / pixels) ** 0.5
                width = max(512, int(width * scale) // 64 * 64)
                height = max(512, int(height * scale) // 64 * 64)
            steps = min(steps, 30)

        return width, height, steps

    def _runtime_guidance(self, guidance_scale: float, model_key: str) -> float:
        if model_key == "sd15_tiny":
            return min(guidance_scale, 4.0)
        if model_key == "sd15":
            return min(guidance_scale, 6.5)
        return guidance_scale

    def _load_pipeline(self, model_key: str):
        if self._pipeline is not None and self._loaded_model_key == model_key:
            return self._pipeline

        import torch
        from diffusers import AutoPipelineForText2Image, StableDiffusionPipeline

        model_dir = ensure_model(model_key)
        logger.info("Loading pipeline from %s", model_dir)
        gpu = get_gpu_info(settings.low_vram_threshold_gb)
        dtype = torch.float32 if model_key == "sd15_tiny" else torch.float16 if gpu.device == "cuda" else torch.float32
        pipeline_cls = StableDiffusionPipeline if model_key in {"sd15", "sd15_tiny"} else AutoPipelineForText2Image
        use_safetensors = self._has_safetensors_weights(model_dir, model_key)
        kwargs = {"torch_dtype": dtype, "use_safetensors": use_safetensors}
        if model_key == "sd15_tiny":
            kwargs.update({"safety_checker": None, "requires_safety_checker": False})
        elif model_key == "sd15":
            from diffusers import AutoencoderKL

            self._decode_vae = AutoencoderKL.from_pretrained(
                str(model_dir / "vae"),
                torch_dtype=torch.float32,
                use_safetensors=self._component_has_safetensors(model_dir / "vae"),
            ).to("cpu")
            kwargs.update({"safety_checker": None, "requires_safety_checker": False})
            if self._has_fp16_variant(model_dir):
                kwargs["variant"] = "fp16"
        else:
            self._decode_vae = None
            if gpu.device == "cuda":
                kwargs.update({"variant": "fp16"})
        pipe = pipeline_cls.from_pretrained(str(model_dir), **kwargs)
        if model_key == "sd15":
            pipe._cinehuman_safe_vae = True

        if gpu.device == "cuda":
            try:
                pipe.enable_xformers_memory_efficient_attention()
            except Exception:
                logger.info("xFormers unavailable; continuing with default attention")
            pipe.enable_attention_slicing()
            if hasattr(pipe, "enable_vae_tiling"):
                pipe.enable_vae_tiling()
            if model_key == "sd15_tiny":
                pipe.to("cuda")
            elif gpu.total_vram_gb and gpu.total_vram_gb < 8 and hasattr(pipe, "enable_sequential_cpu_offload"):
                pipe.enable_sequential_cpu_offload()
            elif gpu.total_vram_gb and gpu.total_vram_gb < 10 and hasattr(pipe, "enable_model_cpu_offload"):
                pipe.enable_model_cpu_offload()
            else:
                pipe.to("cuda")
        elif not settings.allow_cpu:
            raise RuntimeError("CUDA GPU is required. Set CINEHUMAN_ALLOW_CPU=true to allow CPU mode.")

        self._pipeline = pipe
        self._loaded_model_key = model_key
        return pipe

    @staticmethod
    def _component_has_safetensors(component_dir: Path) -> bool:
        return any(component_dir.glob("*.safetensors"))

    def _has_safetensors_weights(self, model_dir: Path, model_key: str) -> bool:
        if model_key in {"sd15", "sd15_tiny"}:
            return self._component_has_safetensors(model_dir / "unet") and self._component_has_safetensors(model_dir / "vae")
        return True

    @staticmethod
    def _has_fp16_variant(model_dir: Path) -> bool:
        return (
            (model_dir / "unet" / "diffusion_pytorch_model.fp16.safetensors").exists()
            or (model_dir / "unet" / "diffusion_pytorch_model.fp16.bin").exists()
        )


image_generator = ImageGenerator()
