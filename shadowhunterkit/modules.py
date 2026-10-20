"""Explicit module registry: IDs, categories, intent and callable functions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from . import operations


@dataclass(frozen=True)
class Module:
    id: str
    category: str
    description: str
    action: Callable[[str | None], dict]
    needs_target: bool = False


REGISTRY = {
    module.id: module for module in (
        Module("system.info", "System", "Local host and runtime overview",
               operations.system_info),
        Module("network.interfaces", "Network", "Interfaces and local traffic counters",
               operations.network_interfaces),
        Module("wifi.status", "Wireless", "Cached access point data via nmcli",
               operations.wifi_status),
        Module("osint.certificates", "OSINT", "Public certificate-transparency lookup",
               operations.osint_certificates, needs_target=True),
    )
}


def list_modules() -> list[Module]:
    return sorted(REGISTRY.values(), key=lambda module: (module.category, module.id))


def execute(module_id: str, target: str | None) -> dict:
    module = REGISTRY.get(module_id)
    if module is None:
        raise operations.OperationError(
            "Unknown module: " + module_id + ". Use 'modules' to list available IDs."
        )
    if module.needs_target and not target:
        raise operations.OperationError(
            "This module needs a target. Use 'target set DOMAIN' or 'run "
            + module.id + " --target DOMAIN'."
        )
    return module.action(target)
