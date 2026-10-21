"""Explicit, opt-in extension catalog. Imported code is NOT sandboxed."""

from __future__ import annotations

import hashlib
import io
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from .operations import OperationError

ID = re.compile(r"^[a-z][a-z0-9_-]*(?:\.[a-z][a-z0-9_-]*){0,3}$")
LANGUAGES = {".py": "python", ".sh": "bash", ".go": "go", ".rs": "rust"}
RUNTIMES = {"python", "bash", "binary", "go", "rust"}
MAX_ARCHIVE = 8 * 1024 * 1024
MAX_ENTRIES = 64


def _config_file() -> Path:
    return Path(os.environ.get("XDG_CONFIG_HOME", str(Path.home() / ".config"))) / "shadowhunter" / "catalog.json"


def _extension_dir() -> Path:
    return Path(os.environ.get("XDG_DATA_HOME", str(Path.home() / ".local/share"))) / "shadowhunter-extensions"


def read_catalog() -> dict:
    path = _config_file()
    if not path.is_file():
        return {"schema": 1, "modules": {}, "dictionaries": {}}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError) as error:
        raise OperationError("Cannot read extension catalog: " + str(error)) from error
    if not isinstance(data, dict) or data.get("schema") != 1 or not all(
        isinstance(data.get(field), dict) for field in ("modules", "dictionaries")
    ):
        raise OperationError("Invalid extension catalog format.")
    return data


def _save(data: dict) -> None:
    path = _config_file()
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    fd, temp = tempfile.mkstemp(prefix=".catalog-", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(data, stream, indent=2, ensure_ascii=False)
            stream.write("\n")
        os.chmod(temp, 0o600)
        os.replace(temp, path)
    finally:
        if os.path.exists(temp):
            os.unlink(temp)


def _manifest(folder: Path) -> dict:
    manifest_file = folder / "shadowhunter.module.json"
    if manifest_file.is_file():
        try:
            item = json.loads(manifest_file.read_text(encoding="utf-8"))
        except (ValueError, OSError) as error:
            raise OperationError("Invalid module manifest: " + str(error)) from error
    else:
        files = [p for p in folder.iterdir() if p.is_file() and p.suffix in LANGUAGES]
        if len(files) != 1:
            raise OperationError(
                "Module directory requires shadowhunter.module.json "
                "(or a single .py, .sh, .go or .rs source)."
            )
        item = {"schema": 1, "id": "external." + files[0].stem.replace("-", "_"),
                "category": "Community", "description": "Local extension",
                "entrypoint": files[0].name, "runtime": LANGUAGES[files[0].suffix]}
    if not isinstance(item, dict) or item.get("schema") != 1:
        raise OperationError("Module manifest must have schema=1.")
    identifier = item.get("id")
    if not isinstance(identifier, str) or not ID.fullmatch(identifier) or len(identifier) > 80:
        raise OperationError("Invalid module ID in manifest.")
    if item.get("runtime") not in RUNTIMES:
        raise OperationError("Runtime must be python, bash, go, rust or binary.")
    entry = item.get("entrypoint")
    if not isinstance(entry, str) or "/" in entry or "\\" in entry or entry in (".", ".."):
        raise OperationError("Entry point must be a filename at the module root.")
    executable = folder / entry
    if executable.is_symlink() or not executable.is_file():
        raise OperationError("Module entry point does not exist or is a symlink.")
    for key in ("category", "description"):
        if not isinstance(item.get(key), str) or not (1 <= len(item[key]) <= 120):
            raise OperationError("Invalid module " + key + ".")
    return {key: item[key] for key in
            ("id", "category", "description", "entrypoint", "runtime")}


def _prepare(path: Path, metadata: dict) -> Path:
    entry = path / metadata["entrypoint"]
    runtime = metadata["runtime"]
    if runtime in ("python", "bash"):
        return entry
    if runtime == "binary":
        if not os.access(entry, os.X_OK):
            raise OperationError("Binary entrypoint is not executable.")
        return entry
    compiler = shutil.which("go" if runtime == "go" else "rustc")
    if not compiler:
        raise OperationError(runtime + " compiler is required only to import this source module.")
    build_dir = _extension_dir() / "build"
    build_dir.mkdir(parents=True, exist_ok=True)
    output = build_dir / (metadata["id"] + "-runner")
    args = ([compiler, "build", "-o", str(output), str(entry)] if runtime == "go"
            else [compiler, str(entry), "-o", str(output)])
    try:
        done = subprocess.run(args, cwd=path, timeout=90, text=True,
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    except (OSError, subprocess.TimeoutExpired) as error:
        raise OperationError("Compilation failed: " + str(error)) from error
    if done.returncode:
        raise OperationError("Module compilation failed: " + done.stderr[-500:])
    output.chmod(0o700)
    return output


def add_local(path_value: str) -> dict:
    source = Path(path_value).expanduser().resolve(strict=True)
    if source.is_file():
        if source.suffix not in LANGUAGES:
            raise OperationError("Single files must be .py, .sh, .go or .rs.")
        folder = source.parent
        # A single source can be imported without a manifest.
        meta = {"id": "external." + source.stem.replace("-", "_"),
                "category": "Community", "description": "Local extension",
                "entrypoint": source.name, "runtime": LANGUAGES[source.suffix]}
        if not ID.fullmatch(meta["id"]):
            raise OperationError("Invalid module filename; use an explicit manifest.")
    elif source.is_dir():
        folder = source
        meta = _manifest(folder)
    else:
        raise OperationError("Module source must be a local file or directory.")
    data = read_catalog()
    if meta["id"] in data["modules"]:
        raise OperationError("Already registered: " + meta["id"] + ". Remove it first.")
    runner = _prepare(folder, meta)
    data["modules"][meta["id"]] = {
        **meta, "source": str(folder), "runner": str(runner),
    }
    _save(data)
    return data["modules"][meta["id"]]


def add_remote(url: str, digest: str) -> dict:
    parsed = urlparse(url)
    if parsed.scheme != "https" or not parsed.netloc or parsed.username or parsed.password:
        raise OperationError("Remote modules require an HTTPS ZIP URL.")
    if not re.fullmatch(r"[0-9a-fA-F]{64}", digest):
        raise OperationError("Supply an expected SHA-256 checksum (64 hex characters).")
    try:
        with urlopen(Request(url, headers={"User-Agent": "ShadowHunter/0.2"}), timeout=15) as response:
            content = response.read(MAX_ARCHIVE + 1)
    except (OSError, TimeoutError, ValueError) as error:
        raise OperationError("Remote module download failed: " + str(error)) from error
    if len(content) > MAX_ARCHIVE or hashlib.sha256(content).hexdigest() != digest.lower():
        raise OperationError("Archive too large or SHA-256 mismatch; nothing was installed.")
    try:
        archive = zipfile.ZipFile(io.BytesIO(content))
    except (zipfile.BadZipFile, ValueError) as error:
        raise OperationError("Expected a valid ZIP archive.") from error
    with archive:
        items = archive.infolist()
        if len(items) > MAX_ENTRIES or sum(i.file_size for i in items) > MAX_ARCHIVE:
            raise OperationError("Archive exceeds file-count or uncompressed-size limit.")
        with tempfile.TemporaryDirectory(prefix="shadowhunter-import-") as tmp:
            staging = Path(tmp)
            for item in items:
                name = item.filename
                parts = Path(name).parts
                mode = (item.external_attr >> 16) & 0o170000
                if (name.startswith("/") or "\\" in name or not parts or
                    any(part in ("..", ".") for part in parts) or
                    mode == stat.S_IFLNK):
                    raise OperationError("Unsafe archive entry.")
                destination = staging.joinpath(*parts)
                if not destination.resolve().is_relative_to(staging.resolve()):
                    raise OperationError("Archive path escapes its destination.")
                if item.is_dir():
                    destination.mkdir(parents=True, exist_ok=True)
                else:
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    with archive.open(item) as reader, destination.open("wb") as writer:
                        shutil.copyfileobj(reader, writer)
            meta = _manifest(staging)
            managed = _extension_dir() / meta["id"]
            if managed.exists() or managed.is_symlink():
                raise OperationError("Module already downloaded; remove it first.")
            managed.parent.mkdir(parents=True, exist_ok=True)
            shutil.copytree(staging, managed, symlinks=False)
            try:
                return add_local(str(managed))
            except Exception:
                shutil.rmtree(managed)
                raise


def remove_module(identifier: str) -> None:
    data = read_catalog()
    if identifier not in data["modules"]:
        raise OperationError("Module not found: " + identifier)
    # Never delete user-provided source files or external binaries.
    del data["modules"][identifier]
    _save(data)


def add_dictionary(path_value: str, name: str | None = None) -> dict:
    path = Path(path_value).expanduser().resolve(strict=True)
    if not (path.is_file() or path.is_dir()):
        raise OperationError("Dictionary must reference a regular file or directory.")
    name = name or path.stem.lower().replace("-", "_")
    if not ID.fullmatch(name) or "." in name:
        raise OperationError("Use a simple lowercase dictionary name.")
    data = read_catalog()
    data["dictionaries"][name] = {"path": str(path), "type": "directory" if path.is_dir() else "file"}
    _save(data)
    return data["dictionaries"][name]


def remove_dictionary(name: str) -> None:
    data = read_catalog()
    if name not in data["dictionaries"]:
        raise OperationError("Unknown dictionary: " + name)
    del data["dictionaries"][name]
    _save(data)


def run_external(identifier: str, target: str | None, dictionary: str | None = None) -> dict:
    data = read_catalog()
    module = data["modules"].get(identifier)
    if not module:
        raise OperationError("Unknown extension: " + identifier)
    runtime = module["runtime"]
    runner = Path(module["runner"])
    source = Path(module["source"])
    if not runner.is_file() or not source.is_dir():
        raise OperationError("Extension source or executable is missing; reimport it.")
    if runtime == "python":
        argv = [sys.executable, str(runner)]
    elif runtime == "bash":
        argv = ["bash", str(runner)]
    else:
        argv = [str(runner)]
    env = os.environ.copy()
    env["SHADOWHUNTER_TARGET"] = target or ""
    if dictionary:
        item = data["dictionaries"].get(dictionary)
        if not item or not Path(item["path"]).exists():
            raise OperationError("Dictionary is not registered or is missing: " + dictionary)
        env["SHADOWHUNTER_DICTIONARY"] = item["path"]
    try:
        done = subprocess.run(argv, cwd=source, env=env, stdin=subprocess.DEVNULL,
                              capture_output=True, timeout=20, check=False, text=True)
    except (OSError, subprocess.TimeoutExpired) as error:
        raise OperationError("Extension failed: " + str(error)) from error
    if done.returncode:
        raise OperationError("Extension returned code " + str(done.returncode) + ": " + done.stderr[-300:])
    if len(done.stdout) > 65536:
        raise OperationError("Extension output exceeds 64 KiB.")
    try:
        result = json.loads(done.stdout)
        if isinstance(result, dict):
            return result
    except ValueError:
        pass
    return {"module": identifier, "stdout": done.stdout[:65536]}
