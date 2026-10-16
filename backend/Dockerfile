FROM python:3.14-slim

# Don't write .pyc files and flush logs immediately (unbuffered).
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Which requirements file to install: requirements.txt (production) by default,
# requirements-dev.txt for local development (adds pytest, ruff...).
ARG REQUIREMENTS=requirements.txt

# Dependencies go before the code: if only the code changes,
# Docker reuses this layer and skips reinstalling.
COPY requirements.txt requirements-dev.txt ./
RUN pip install --no-cache-dir -r ${REQUIREMENTS}

COPY . .

# Don't run as root inside the container.
RUN useradd --create-home --uid 1000 app
USER app

EXPOSE 8000

# Access logs come from CorrelationIdMiddleware (JSON), not from uvicorn.
CMD ["uvicorn", "config.asgi:application", "--host", "0.0.0.0", "--port", "8000", "--no-access-log"]
