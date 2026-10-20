"""Conservative, read-only operations. No shell expansion or hidden scans."""

from __future__ import annotations

import json
import platform
import re
import shutil
import socket
import subprocess
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen


class OperationError(RuntimeError):
    pass


def system_info(_target: str | None = None) -> dict:
    return {
        "platform": platform.platform(),
        "python": platform.python_version(),
        "hostname": socket.gethostname(),
        "architecture": platform.machine(),
    }


def network_interfaces(_target: str | None = None) -> dict:
    try:
        names = sorted(name for _idx, name in socket.if_nameindex())
    except OSError as error:
        raise OperationError("Cannot list local network interfaces: " + str(error)) from error
    counters = {}
    dev = Path("/proc/net/dev")
    try:
        if dev.is_file():
            for line in dev.read_text(encoding="ascii").splitlines()[2:]:
                if ":" not in line:
                    continue
                name, stats = line.rsplit(":", 1)
                values = stats.split()
                if len(values) >= 9:
                    counters[name.strip()] = {
                        "rx_bytes": int(values[0]), "tx_bytes": int(values[8]),
                    }
    except (OSError, ValueError):
        pass
    return {
        "interfaces": [
            {"name": name, **counters.get(name, {})} for name in names
        ],
        "note": "Local counters only; not packet capture or network discovery.",
    }


def wifi_status(_target: str | None = None) -> dict:
    if not shutil.which("nmcli"):
        raise OperationError(
            "nmcli is unavailable. Wi-Fi status needs NetworkManager; "
            "no package is installed automatically."
        )
    try:
        command = [
            "nmcli", "-t", "-f", "IN-USE,SSID,SIGNAL,SECURITY",
            "device", "wifi", "list", "--rescan", "no",
        ]
        done = subprocess.run(
            command, capture_output=True, text=True, timeout=8, check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        raise OperationError("Cannot read cached Wi-Fi information: " + str(error)) from error
    if done.returncode:
        raise OperationError("NetworkManager could not read cached Wi-Fi status: "
                             + done.stderr.strip()[:240])
    return {
        "cached_access_points": done.stdout.splitlines()[:40],
        "note": "Cached NetworkManager listing; no active rescan, injection or connection.",
    }


DOMAIN_PATTERN = re.compile(
    r"(?=.{1,253}$)(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+"
    r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?"
)


def normalized_domain(value: str | None) -> str:
    domain = (value or "").strip().lower().rstrip(".")
    if not DOMAIN_PATTERN.fullmatch(domain):
        raise OperationError("Provide a valid domain, e.g. example.org (no URL or path).")
    return domain


def osint_certificates(target: str | None = None) -> dict:
    domain = normalized_domain(target)
    url = "https://crt.sh/?q=" + quote("%." + domain, safe="") + "&output=json"
    request = Request(url, headers={"User-Agent": "ShadowHunter/0.2 (+public CT research)"})
    try:
        with urlopen(request, timeout=10) as response:
            body = response.read(1_048_577)
    except (HTTPError, URLError, TimeoutError, OSError) as error:
        raise OperationError("Certificate transparency lookup failed: " + str(error)) from error
    if len(body) > 1_048_576:
        raise OperationError("Certificate response exceeds the 1 MiB safety limit.")
    try:
        entries = json.loads(body)
    except (ValueError, UnicodeError) as error:
        raise OperationError("Certificate service returned invalid JSON.") from error
    if not isinstance(entries, list):
        raise OperationError("Unexpected certificate service response.")
    found: set[str] = set()
    for item in entries:
        if not isinstance(item, dict):
            continue
        raw = item.get("name_value", "")
        if not isinstance(raw, str):
            continue
        for candidate in raw.splitlines():
            name = candidate.lower().strip().removeprefix("*.")
            if name == domain or name.endswith("." + domain):
                if DOMAIN_PATTERN.fullmatch(name):
                    found.add(name)
    return {
        "domain": domain,
        "source": "crt.sh public certificate-transparency records",
        "names": sorted(found)[:100],
        "total_unique": len(found),
        "limited": len(found) > 100,
        "note": "Public certificate metadata is not proof that a host is active.",
    }
