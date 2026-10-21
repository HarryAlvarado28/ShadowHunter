"""Pure input rules shared by the CLI, workspaces and modules.

No networking, filesystem access, subprocesses or global state here.
"""

from __future__ import annotations

import re


class WorkspaceError(ValueError):
    """Invalid workspace name or stored session."""


class OperationError(RuntimeError):
    """Invalid operation request or failed operation."""


SESSION_NAME = re.compile(r"^[a-z][a-z0-9_-]{0,39}$")
DOMAIN = re.compile(
    r"(?=.{1,253}$)(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+"
    r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?"
)
RUN_FLAGS = {"--target", "--dictionary"}


def check_session_name(name: str) -> str:
    """Return a safe single-component session identifier."""
    if not isinstance(name, str) or not SESSION_NAME.fullmatch(name):
        raise WorkspaceError(
            "Session name must start with a lowercase letter and contain "
            "up to 40 lowercase letters, numbers, underscores or hyphens."
        )
    return name


def normalized_domain(value: str | None) -> str:
    """Normalize a DNS name without performing network access."""
    domain = (value or "").strip().lower().rstrip(".")
    tld = domain.rsplit(".", 1)[-1]
    if not DOMAIN.fullmatch(domain) or not any(char.isalpha() for char in tld):
        raise OperationError("Provide a valid domain, e.g. example.org (no URL or path).")
    return domain


def parse_run_options(flags: list[str]) -> dict[str, str]:
    """Parse only explicit, nonempty --target/--dictionary pairs."""
    if len(flags) % 2:
        raise ValueError("Options require a value: --target NAME or --dictionary NAME.")
    options: dict[str, str] = {}
    for position in range(0, len(flags), 2):
        key, value = flags[position:position + 2]
        if key not in RUN_FLAGS or key in options or not value or value.startswith("--"):
            raise ValueError("Use --target VALUE or --dictionary NAME once each.")
        options[key] = value
    return options
