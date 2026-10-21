"""Local evidence SHA-256: optional Go worker, bounded Python fallback."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from .operations import OperationError

MAX_FILES = 256
MAX_ENTRIES = 4096
MAX_FILE_BYTES = 16 << 20


def _digest(root: Path, relative: str) -> dict:
    item = root / relative
    try:
        info = item.lstat()
        if not item.is_file() or item.is_symlink() or info.st_size > MAX_FILE_BYTES:
            return {"path": relative, "error": "not a supported regular file (max 16 MiB)"}
        sha = hashlib.sha256()
        size = 0
        with item.open("rb") as stream:
            while chunk := stream.read(min(1 << 20, MAX_FILE_BYTES + 1 - size)):
                size += len(chunk)
                if size > MAX_FILE_BYTES:
                    return {"path": relative, "error": "file grew past size limit"}
                sha.update(chunk)
        return {"path": relative, "sha256": sha.hexdigest(), "size": size}
    except OSError as error:
        return {"path": relative, "error": str(error)}


def _python_hash(root: Path) -> dict:
    selected: list[str] = []
    skipped = 0
    entries = 0
    for current, directories, files in os.walk(root, followlinks=False):
        entries += 1
        for name in directories[:]:
            item = Path(current) / name
            entries += 1
            if item.is_symlink():
                directories.remove(name)
                skipped += 1
        for name in files:
            entries += 1
            item = Path(current) / name
            try:
                info = item.lstat()
            except OSError as error:
                raise OperationError(str(error)) from error
            if item.is_symlink() or not item.is_file() or info.st_size > MAX_FILE_BYTES:
                skipped += 1
                continue
            if len(selected) >= MAX_FILES:
                raise OperationError("Directory exceeds 256 eligible files.")
            selected.append(str(item.relative_to(root)))
        if entries > MAX_ENTRIES:
            raise OperationError("Directory exceeds 4096 entries.")
    with ThreadPoolExecutor(max_workers=4) as pool:
        found = sorted(pool.map(lambda relative: _digest(root, relative), selected),
                       key=lambda item: item["path"])
    return {
        "engine": "python", "directory": str(root),
        "files": found, "skipped": skipped,
    }


def hash_directory(target: str | None = None) -> dict:
    if not target:
        raise OperationError("Use run evidence.hash --target /path/to/local/directory.")
    root = Path(target).expanduser().absolute()
    if root.is_symlink() or not root.is_dir():
        raise OperationError("Evidence target must be an existing local directory, not a symlink.")
    worker = Path(__file__).resolve().parent.parent / "bin" / "shadowhunter-worker"
    if worker.is_file() and os.access(worker, os.X_OK):
        try:
            result = subprocess.run(
                [str(worker), "--dir", str(root), "--workers", "4"],
                capture_output=True, text=True, check=False, timeout=30,
            )
        except (OSError, subprocess.TimeoutExpired) as error:
            raise OperationError("Evidence worker failed: " + str(error)) from error
        if result.returncode:
            raise OperationError("Evidence worker: " + result.stderr.strip()[:240])
        try:
            report = json.loads(result.stdout)
        except json.JSONDecodeError as error:
            raise OperationError("Evidence worker returned malformed JSON.") from error
        if not isinstance(report, dict) or not isinstance(report.get("files"), list):
            raise OperationError("Evidence worker returned invalid data.")
        return report
    try:
        return _python_hash(root)
    except OSError as error:
        raise OperationError("Evidence hashing failed: " + str(error)) from error
