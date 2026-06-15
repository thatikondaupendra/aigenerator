from __future__ import annotations

import asyncio
import logging
import uuid
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any

from backend.schemas import JobInfo, JobStatus

logger = logging.getLogger(__name__)
JobCallable = Callable[[Callable[[float], None]], Awaitable[dict[str, Any]]]


@dataclass
class JobRecord:
    id: str
    type: str
    status: JobStatus
    task: JobCallable
    progress: float = 0.0
    result: dict[str, Any] | None = None
    error: str | None = None
    event: asyncio.Event = field(default_factory=asyncio.Event)


class JobQueue:
    def __init__(self) -> None:
        self._jobs: dict[str, JobRecord] = {}
        self._queue: asyncio.Queue[str] = asyncio.Queue()
        self._worker: asyncio.Task[None] | None = None
        self._lock = asyncio.Lock()

    async def start(self) -> None:
        if self._worker is None or self._worker.done():
            self._worker = asyncio.create_task(self._run(), name="cinehuman-job-worker")

    async def stop(self) -> None:
        if self._worker:
            self._worker.cancel()
            try:
                await self._worker
            except asyncio.CancelledError:
                pass

    async def enqueue(self, job_type: str, task: JobCallable) -> JobRecord:
        async with self._lock:
            job_id = uuid.uuid4().hex
            record = JobRecord(id=job_id, type=job_type, status=JobStatus.queued, task=task)
            self._jobs[job_id] = record
            await self._queue.put(job_id)
            return record

    def get(self, job_id: str) -> JobInfo | None:
        record = self._jobs.get(job_id)
        if record is None:
            return None
        return JobInfo(
            id=record.id,
            type=record.type,
            status=record.status,
            progress=record.progress,
            result=record.result,
            error=record.error,
        )

    async def _run(self) -> None:
        while True:
            job_id = await self._queue.get()
            record = self._jobs[job_id]
            record.status = JobStatus.running
            record.progress = 0.01
            try:
                logger.info("Starting job %s (%s)", record.id, record.type)
                record.result = await record.task(lambda value: self._set_progress(record, value))
                record.progress = 1.0
                record.status = JobStatus.completed
                logger.info("Completed job %s", record.id)
            except Exception as exc:  # noqa: BLE001 - API boundary should report any worker failure.
                logger.exception("Job %s failed", record.id)
                record.error = str(exc)
                record.status = JobStatus.failed
            finally:
                record.event.set()
                self._queue.task_done()

    @staticmethod
    def _set_progress(record: JobRecord, value: float) -> None:
        record.progress = max(0.0, min(1.0, value))


job_queue = JobQueue()
