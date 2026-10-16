import os
import signal
import socket

import structlog
from django.core.management.base import BaseCommand
from django.db import connection, reset_queries

from apps.orchestration.handlers import HANDLERS
from apps.orchestration.queue import JobQueue
from apps.orchestration.worker import Worker

POLL_SECONDS = 5

logger = structlog.get_logger("worker")


class Command(BaseCommand):
    help = "Process jobs from the queue until stopped (SIGTERM or Ctrl+C)."

    def handle(self, *args, **options):
        worker_id = f"{socket.gethostname()}-{os.getpid()}"
        worker = Worker(JobQueue(worker_id), HANDLERS)
        self.stopping = False
        signal.signal(signal.SIGTERM, self._stop)
        signal.signal(signal.SIGINT, self._stop)

        connection.ensure_connection()
        with connection.cursor() as cursor:
            cursor.execute("LISTEN jobs")
        logger.info("worker_started", worker_id=worker_id)

        while not self.stopping:
            # DEBUG keeps every query in memory; a process that never ends must clear it.
            reset_queries()
            if worker.run_once():
                continue
            # Sleep until the trigger announces a new job, or until the poll timeout.
            for _ in connection.connection.notifies(timeout=POLL_SECONDS, stop_after=1):
                pass

        logger.info("worker_stopped", worker_id=worker_id)

    def _stop(self, *args):
        # Finish the current batch, then exit (at most POLL_SECONDS later).
        self.stopping = True
