import structlog

from .queue import JobQueue

logger = structlog.get_logger("worker")


class Worker:
    def __init__(self, queue: JobQueue, handlers: dict, batch_size: int = 10):
        self.queue = queue
        self.handlers = handlers
        self.batch_size = batch_size

    def run_once(self) -> int:
        """Claim a batch and run it. Returns how many jobs were claimed."""
        jobs = self.queue.claim(limit=self.batch_size)
        for job in jobs:
            self._run(job)
        return len(jobs)

    def _run(self, job):
        structlog.contextvars.bind_contextvars(
            correlation_id=job.correlation_id,
            job_id=job.id,
            application_id=str(job.application_id) if job.application_id else None,
            worker_id=self.queue.worker_id,
        )
        try:
            self.handlers[job.kind](job)
        except Exception as error:
            # A failing job must never stop the worker: it is retried later or marked dead.
            logger.exception("job_failed", kind=job.kind, attempts=job.attempts)
            self.queue.fail(job, repr(error))
        else:
            self.queue.complete(job)
        finally:
            structlog.contextvars.clear_contextvars()
