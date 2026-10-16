"""What the worker does for each kind of job. For now it only logs."""

import structlog

logger = structlog.get_logger("jobs")


def advance(job):
    logger.info("advance_requested")


HANDLERS = {"advance": advance}
