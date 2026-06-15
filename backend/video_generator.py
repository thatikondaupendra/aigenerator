from __future__ import annotations

import asyncio
import logging
import time
from pathlib import Path
from typing import Callable

import cv2
import numpy as np
from PIL import Image

from backend.config import settings
from backend.gpu_manager import get_gpu_info
from backend.model_downloader import ensure_model
from backend.prompt_engine import build_negative_prompt
from backend.schemas import GenerateVideoRequest

logger = logging.getLogger(__name__)


class VideoGenerator:
    async def generate(
        self, request: GenerateVideoRequest, progress: Callable[[float], None]
    ) -> dict[str, str | int]:
        return await asyncio.to_thread(self._generate_sync, request, progress)

    def _generate_sync(
        self, request: GenerateVideoRequest, progress: Callable[[float], None]
    ) -> dict[str, str | int]:
        image_path = Path(request.image_path)
        if not image_path.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")
        progress(0.08)
        try:
            return self._animatediff(request, image_path, progress)
        except Exception as exc:  # noqa: BLE001
            logger.warning("AnimateDiff generation unavailable, using cinematic motion renderer: %s", exc)
            return self._fallback_motion_video(request, image_path, progress)

    def _animatediff(
        self, request: GenerateVideoRequest, image_path: Path, progress: Callable[[float], None]
    ) -> dict[str, str | int]:
        import torch
        from diffusers import AnimateDiffImgToVideoPipeline, MotionAdapter
        from diffusers.utils import export_to_video

        adapter_dir = ensure_model("animatediff")
        base_dir = ensure_model("sd15")
        gpu = get_gpu_info()
        dtype = torch.float16 if gpu.device == "cuda" else torch.float32
        adapter = MotionAdapter.from_pretrained(str(adapter_dir), torch_dtype=dtype)
        pipe = AnimateDiffImgToVideoPipeline.from_pretrained(
            str(base_dir), motion_adapter=adapter, torch_dtype=dtype
        )
        if gpu.device == "cuda":
            pipe.to("cuda")
            pipe.enable_attention_slicing()
            if hasattr(pipe, "enable_model_cpu_offload") and gpu.low_vram:
                pipe.enable_model_cpu_offload()

        for lora_path in request.motion_lora_paths:
            path = Path(lora_path)
            if path.exists() and hasattr(pipe, "load_lora_weights"):
                pipe.load_lora_weights(str(path))

        image = Image.open(image_path).convert("RGB")
        frames_count = request.seconds * request.fps
        generator = None
        if request.seed is not None:
            generator = torch.Generator(device=gpu.device).manual_seed(request.seed)
        result = pipe(
            prompt=request.prompt,
            negative_prompt=build_negative_prompt(request.negative_prompt),
            image=image,
            num_frames=min(frames_count, 48),
            guidance_scale=7.0,
            generator=generator,
        )
        progress(0.85)
        output_path = settings.outputs_dir / "videos" / f"video_{int(time.time())}.mp4"
        export_to_video(result.frames[0], str(output_path), fps=request.fps)
        return {"video_path": str(output_path), "fps": request.fps, "seconds": request.seconds}

    def _fallback_motion_video(
        self, request: GenerateVideoRequest, image_path: Path, progress: Callable[[float], None]
    ) -> dict[str, str | int]:
        image = cv2.imread(str(image_path), cv2.IMREAD_COLOR)
        if image is None:
            raise ValueError(f"Unable to read image: {image_path}")
        height, width = image.shape[:2]
        frames_count = request.seconds * request.fps
        output_path = settings.outputs_dir / "videos" / f"video_{int(time.time())}.mp4"
        writer = cv2.VideoWriter(
            str(output_path),
            cv2.VideoWriter_fourcc(*"mp4v"),
            request.fps,
            (width, height),
        )
        for index in range(frames_count):
            t = index / max(1, frames_count - 1)
            zoom = 1.0 + 0.025 * np.sin(t * np.pi)
            pan = int((t - 0.5) * width * 0.025)
            matrix = cv2.getRotationMatrix2D((width / 2 + pan, height / 2), 0, zoom)
            frame = cv2.warpAffine(image, matrix, (width, height), borderMode=cv2.BORDER_REFLECT)
            brightness = 1.0 + 0.015 * np.sin(t * np.pi * 4)
            frame = np.clip(frame.astype(np.float32) * brightness, 0, 255).astype(np.uint8)
            writer.write(frame)
            progress(0.1 + 0.8 * (index + 1) / frames_count)
        writer.release()
        return {"video_path": str(output_path), "fps": request.fps, "seconds": request.seconds}


video_generator = VideoGenerator()
