from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from backend.config import ensure_directories, settings
from backend.enhancer import image_enhancer
from backend.generator import image_generator
from backend.gpu_manager import get_gpu_info
from backend.job_queue import job_queue
from backend.lora_manager import lora_manager
from backend.model_downloader import model_status
from backend.schemas import (
    EnhanceImageRequest,
    GenerateImageRequest,
    GenerateVideoRequest,
    JobCreated,
    JobInfo,
    TrainLoraRequest,
)
from backend.video_generator import video_generator

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    ensure_directories()
    await job_queue.start()
    logger.info("GPU profile: %s", get_gpu_info(settings.low_vram_threshold_gb))
    yield
    await job_queue.stop()


app = FastAPI(title=settings.app_name, version="1.0.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    logger.warning("Validation error: %s", exc)
    return JSONResponse(
        status_code=422,
        content={"detail": str(exc)}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    logger.exception("Unhandled exception: %s", exc)
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal server error: {str(exc)}"}
    )

app.mount("/outputs", StaticFiles(directory=str(settings.outputs_dir)), name="outputs")


@app.get("/health")
async def health() -> dict[str, object]:
    return {"status": "ok", "gpu": get_gpu_info(settings.low_vram_threshold_gb).__dict__}


@app.get("/models/status")
async def models_status() -> dict[str, object]:
    return {"models": model_status()}


@app.post("/generate-image", response_model=JobCreated)
async def generate_image(request: GenerateImageRequest) -> JobCreated:
    record = await job_queue.enqueue("generate-image", lambda progress: image_generator.generate(request, progress))
    return JobCreated(id=record.id, status=record.status)


@app.post("/enhance-image", response_model=JobCreated)
async def enhance_image(request: EnhanceImageRequest) -> JobCreated:
    record = await job_queue.enqueue("enhance-image", lambda progress: image_enhancer.enhance(request, progress))
    return JobCreated(id=record.id, status=record.status)


@app.post("/generate-video", response_model=JobCreated)
async def generate_video(request: GenerateVideoRequest) -> JobCreated:
    record = await job_queue.enqueue("generate-video", lambda progress: video_generator.generate(request, progress))
    return JobCreated(id=record.id, status=record.status)


@app.post("/train-lora", response_model=JobCreated)
async def train_lora(request: TrainLoraRequest) -> JobCreated:
    record = await job_queue.enqueue("train-lora", lambda progress: lora_manager.train(request, progress))
    return JobCreated(id=record.id, status=record.status)


@app.get("/jobs/{job_id}", response_model=JobInfo)
async def get_job(job_id: str) -> JobInfo:
    job = job_queue.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return job
