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
from backend.model_downloader import ensure_model
from backend.schemas import EnhanceImageRequest

logger = logging.getLogger(__name__)


class ImageEnhancer:
    async def enhance(
        self, request: EnhanceImageRequest, progress: Callable[[float], None]
    ) -> dict[str, str | int]:
        return await asyncio.to_thread(self._enhance_sync, request, progress)

    def _enhance_sync(
        self, request: EnhanceImageRequest, progress: Callable[[float], None]
    ) -> dict[str, str | int]:
        image_path = Path(request.image_path)
        if not image_path.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")

        progress(0.1)
        image = self._run_face_restore(image_path, request.face_enhancer)
        progress(0.55)
        image = self._run_upscale(image, request.upscale)
        progress(0.9)

        filename = f"enhanced_{int(time.time())}.png"
        output_path = settings.outputs_dir / "enhanced" / filename
        Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB)).save(output_path)
        return {"image_path": str(output_path), "upscale": request.upscale}

    def _run_face_restore(self, image_path: Path, face_enhancer: str) -> np.ndarray:
        image = cv2.imread(str(image_path), cv2.IMREAD_COLOR)
        if image is None:
            raise ValueError(f"Unable to read image: {image_path}")

        if face_enhancer.lower() != "gfpgan":
            logger.info("CodeFormer requested, using GFPGAN fallback unless CodeFormer is installed separately")

        try:
            ensure_model("gfpgan")
            from gfpgan import GFPGANer

            model_file = next((settings.models_dir / "gfpgan").glob("**/*.pth"), None)
            if model_file is None:
                logger.warning("GFPGAN weights not found after download; returning original face image")
                return image
            restorer = GFPGANer(
                model_path=str(model_file),
                upscale=1,
                arch="clean",
                channel_multiplier=2,
                bg_upsampler=None,
            )
            _, _, restored = restorer.enhance(image, has_aligned=False, only_center_face=False, paste_back=True)
            return restored
        except Exception as exc:  # noqa: BLE001
            logger.warning("Face enhancement unavailable: %s", exc)
            return image

    def _run_upscale(self, image: np.ndarray, scale: int) -> np.ndarray:
        if scale <= 1:
            return image
        try:
            ensure_model("realesrgan")
            from basicsr.archs.rrdbnet_arch import RRDBNet
            from realesrgan import RealESRGANer

            model_file = next((settings.models_dir / "esrgan").glob("**/*.pth"), None)
            if model_file is None:
                raise FileNotFoundError("Real-ESRGAN .pth weights were not found")
            model = RRDBNet(num_in_ch=3, num_out_ch=3, num_feat=64, num_block=23, num_grow_ch=32, scale=scale)
            upsampler = RealESRGANer(scale=scale, model_path=str(model_file), model=model, tile=256, tile_pad=10)
            output, _ = upsampler.enhance(image, outscale=scale)
            return output
        except Exception as exc:  # noqa: BLE001
            logger.warning("Real-ESRGAN unavailable, using OpenCV upscale: %s", exc)
            height, width = image.shape[:2]
            return cv2.resize(image, (width * scale, height * scale), interpolation=cv2.INTER_CUBIC)


image_enhancer = ImageEnhancer()
