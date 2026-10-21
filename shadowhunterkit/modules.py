"""Explicit module registry: IDs, categories, intent and callable functions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from . import catalog, evidence, operations


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
        Module("compute.info", "System", "CPU, RAM and GPU adapter capabilities",
               operations.compute_info),
        Module("network.interfaces", "Network", "Interfaces and local traffic counters",
               operations.network_interfaces),
        Module("wifi.status", "Wireless", "Cached access point data via nmcli",
               operations.wifi_status),
        Module("osint.certificates", "OSINT", "Public certificate-transparency lookup",
               operations.osint_certificates, needs_target=True),
        Module("evidence.hash", "Evidence", "Concurrent SHA-256 for local files (Go/Python)",
               evidence.hash_directory, needs_target=True),
    )
}


def list_modules() -> list[Module]:
    registered = list(REGISTRY.values())
    for item in catalog.read_catalog()["modules"].values():
        registered.append(Module(
            item["id"], item["category"], item["description"],
            lambda target, identifier=item["id"]: catalog.run_external(identifier, target),
        ))
    return sorted(registered, key=lambda module: (module.category, module.id))


def execute(module_id: str, target: str | None, dictionary: str | None = None) -> dict:
    module = REGISTRY.get(module_id)
    if module is None and module_id in catalog.read_catalog()["modules"]:
        return catalog.run_external(module_id, target, dictionary)
    if module is None:
        raise operations.OperationError(
            "Unknown module: " + module_id + ". Use 'modules' to list available IDs."
        )
    if module.needs_target and not target:
        raise operations.OperationError(
            "This module needs a target. Use 'target set VALUE' or 'run "
            + module.id + " --target DOMAIN'."
        )
    if dictionary:
        raise operations.OperationError("Dictionary selection is supported by extensions only.")
    return module.action(target)
