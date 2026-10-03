from __future__ import annotations

import subprocess
from pathlib import Path


class KrakenRunError(RuntimeError):
    pass


def recognize_to_alto(
    image_path: Path,
    output_path: Path,
    *,
    model_path: Path,
    timeout_seconds: int = 600,
) -> Path:
    """Run Kraken without invoking a shell.

    Paths are supplied as argv elements to avoid shell injection. Production
    workers additionally constrain these paths to job/model directories.
    """
    if not image_path.is_file():
        raise FileNotFoundError(image_path)
    if not model_path.is_file():
        raise FileNotFoundError(model_path)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    command = [
        "kraken",
        "-i",
        str(image_path),
        str(output_path),
        "-f",
        "alto",
        "segment",
        "-bl",
        "ocr",
        "-m",
        str(model_path),
    ]
    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        timeout=timeout_seconds,
        check=False,
    )
    if result.returncode != 0:
        detail = result.stderr.strip()[-2000:]
        raise KrakenRunError(f"Kraken failed with exit code {result.returncode}: {detail}")
    if not output_path.is_file():
        raise KrakenRunError("Kraken completed without producing ALTO output")
    return output_path
