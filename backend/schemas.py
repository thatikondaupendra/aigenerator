from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class JobStatus(str, Enum):
    queued = "queued"
    running = "running"
    completed = "completed"
    failed = "failed"


class ImageModel(str, Enum):
    auto = "auto"
    sdxl = "sdxl"
    juggernaut = "juggernaut"
    realvis = "realvis"
    dreamshaper = "dreamshaper"
    sd15 = "sd15"
    sd15_tiny = "sd15_tiny"


class GenerateImageRequest(BaseModel):
    prompt: str = Field(..., min_length=3)
    negative_prompt: str | None = None
    template: str | None = Field(default="cinematic_male")
    model: ImageModel = ImageModel.auto
    width: int = Field(default=512, ge=384, le=2048)
    height: int = Field(default=640, ge=384, le=2048)
    steps: int = Field(default=16, ge=1, le=80)
    guidance_scale: float = Field(default=4.0, ge=1.0, le=20.0)
    seed: int | None = None
    lora_paths: list[str] = Field(default_factory=list)
    ip_adapter_image: str | None = None
    instant_id_image: str | None = None


class EnhanceImageRequest(BaseModel):
    image_path: str = Field(..., min_length=1)
    face_enhancer: str = Field(default="gfpgan")
    upscale: int = Field(default=2, ge=1, le=4)


class GenerateVideoRequest(BaseModel):
    image_path: str = Field(..., min_length=1)
    prompt: str = Field(default="subtle breathing motion, blinking eyes, slow cinematic camera pan")
    negative_prompt: str | None = None
    seconds: int = Field(default=5, ge=1, le=10)
    fps: int = Field(default=24, ge=8, le=30)
    motion_lora_paths: list[str] = Field(default_factory=list)
    seed: int | None = None


class TrainLoraRequest(BaseModel):
    dataset_dir: str = Field(..., min_length=1)
    output_name: str = Field(..., min_length=1)
    base_model: ImageModel = ImageModel.sdxl
    rank: int = Field(default=16, ge=4, le=128)
    steps: int = Field(default=1000, ge=100, le=10000)


class JobCreated(BaseModel):
    id: str
    status: JobStatus


class JobInfo(BaseModel):
    id: str
    type: str
    status: JobStatus
    progress: float = 0.0
    result: dict[str, Any] | None = None
    error: str | None = None
