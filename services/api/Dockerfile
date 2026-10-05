FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app

COPY pyproject.toml /app/pyproject.toml
COPY app /app/app
RUN pip install --no-cache-dir .

RUN useradd --create-home --uid 10001 appuser && mkdir -p /data/metadata /data/objects && chown -R appuser:appuser /data

ENV MANUSCRIPT_METADATA_PATH=/data/metadata/manuscripts.sqlite3 \
    SCHOLARSHIP_METADATA_PATH=/data/metadata/scholarship.sqlite3 \
    LIVING_METADATA_PATH=/data/metadata/living.sqlite3 \
    OTTOMAN_METADATA_PATH=/data/metadata/ottoman.sqlite3 \
    ACADEMY_METADATA_PATH=/data/metadata/academy.sqlite3 \
    HERITAGE_METADATA_PATH=/data/metadata/heritage.sqlite3 \
    MUSEUM_METADATA_PATH=/data/metadata/museum.sqlite3 \
    ACCOUNT_METADATA_PATH=/data/metadata/accounts.sqlite3 \
    VISUAL_INDEX_PATH=/data/metadata/visual-index.sqlite3 \
    OBJECT_STORE_PATH=/data/objects
USER appuser

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers"]
