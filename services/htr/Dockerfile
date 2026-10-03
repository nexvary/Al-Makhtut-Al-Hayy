FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /worker

COPY pyproject.toml /worker/pyproject.toml
COPY htr /worker/htr
RUN apt-get update && apt-get install -y --no-install-recommends libgl1 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir . kraken

RUN useradd --create-home --uid 10002 worker
USER worker

CMD ["python", "-c", "import htr; print('HTR image ready')"]
