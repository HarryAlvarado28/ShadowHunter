"""Private, dependency-free, disk-backed workspaces (not shared process RAM)."""

from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from .validation import SESSION_NAME, WorkspaceError, check_session_name

HISTORY_LIMIT = 100


def timestamp() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class WorkspaceStore:
    def __init__(self, root: Path | None = None):
        state = os.environ.get("XDG_STATE_HOME")
        self.root = Path(root) if root else (
            Path(state) if state else Path.home() / ".local" / "state"
        ) / "shadowhunter" / "sessions"

    @staticmethod
    def check_name(name: str) -> str:
        return check_session_name(name)

    def _path(self, name: str) -> Path:
        return self.root / (self.check_name(name) + ".json")

    @staticmethod
    def _blank(name: str) -> dict:
        return {
            "schema": 1, "name": name, "created_at": timestamp(),
            "target": None, "scope": [], "notes": [], "history": [],
        }

    def exists(self, name: str) -> bool:
        return self._path(name).is_file()

    def create(self, name: str) -> dict:
        path = self._path(name)
        if path.exists():
            raise WorkspaceError("Session already exists: " + name)
        data = self._blank(name)
        self._write(path, data, exclusive=True)
        return data

    def load(self, name: str, create_default: bool = False) -> dict:
        path = self._path(name)
        if not path.exists():
            if create_default and name == "default":
                try:
                    return self.create(name)
                except WorkspaceError:
                    if not path.exists():
                        raise
            else:
                raise WorkspaceError("Unknown session: " + name)
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as error:
            raise WorkspaceError("Cannot read session " + name + ": " + str(error)) from error
        if not isinstance(data, dict) or data.get("schema") != 1 or data.get("name") != name:
            raise WorkspaceError("Unsupported or damaged workspace: " + name)
        return data

    def save(self, data: dict) -> None:
        name = self.check_name(data["name"])
        if data.get("schema") != 1:
            raise WorkspaceError("Unsupported workspace schema")
        data["history"] = data.get("history", [])[-HISTORY_LIMIT:]
        self._write(self._path(name), data)

    def list_names(self) -> list[str]:
        if not self.root.exists():
            return []
        return sorted(p.stem for p in self.root.glob("*.json") if SESSION_NAME.fullmatch(p.stem))

    def export(self, name: str, path: Path) -> Path:
        """Export to a new path only; refuse overwrites and use 0600 permissions."""
        document = json.dumps(self.load(name), ensure_ascii=False, indent=2) + "\n"
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            stream.write(document)
        return path

    def _write(self, path: Path, data: dict, exclusive: bool = False) -> None:
        path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        os.chmod(path.parent, 0o700)
        if exclusive:
            payload = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
            fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            with os.fdopen(fd, "w", encoding="utf-8") as stream:
                stream.write(payload)
            return
        fd, tmp = tempfile.mkstemp(prefix=".session-", dir=path.parent)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as stream:
                json.dump(data, stream, ensure_ascii=False, indent=2)
                stream.write("\n")
                stream.flush()
                os.fsync(stream.fileno())
            os.chmod(tmp, 0o600)
            os.replace(tmp, path)
        finally:
            if os.path.exists(tmp):
                os.unlink(tmp)
