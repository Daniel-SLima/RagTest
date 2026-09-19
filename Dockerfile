FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    HOME=/home/app \
    XDG_CACHE_HOME=/app/.cache \
    HF_HOME=/app/.cache/huggingface \
    HF_HUB_DISABLE_XET=1

WORKDIR /app

# Fixed UID/GID keeps writable Docker volumes predictable across hosts.
RUN addgroup --gid 10001 app \
    && adduser --uid 10001 --gid 10001 --disabled-password --gecos "" app \
    && mkdir -p /app/.cache/fastembed /app/.cache/huggingface \
    && chown -R app:app /app/.cache /home/app

COPY pyproject.toml README.md ./
COPY app ./app

RUN pip install --no-cache-dir .

USER app

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
