"""Terminal-first, dependency-free ShadowHunter command interface."""

from __future__ import annotations

import json
import os
import platform
import shlex
import shutil
import sys
from pathlib import Path

from . import __version__, modules
from .operations import OperationError
from .workspace import WorkspaceError, WorkspaceStore, timestamp

BANNER = """
  ╔════════════════════════════════════════╗
  ║  🛡️ SHADOWHUNTER  /  Security Workbench  ║
  ╚════════════════════════════════════════╝
  OSINT · Network · Wireless · Workspaces
"""

HELP = """Commands:
  modules                             List available modules
  run MODULE [--target DOMAIN]        Execute an explicit operation
  target set DOMAIN | show | clear    Store the current research target
  session new NAME | use NAME | list | show
  session export FILE                 Export current workspace (private JSON)
  note add TEXT | list                Keep concise field notes
  history                             Recent module executions
  tab                                 Command to resume in another terminal tab
  doctor                              Check local runtime and optional tooling
  help | exit                         Show help or quit

Examples:
  run system.info
  target set example.org
  run osint.certificates
  session new assessment
  tab

Use only systems and data you own or are authorized to assess.
Sessions persist on disk, not as shared process RAM.
"""


def show_modules() -> None:
    print("\n  Available modules\n")
    for module in modules.list_modules():
        needs = " [target]" if module.needs_target else ""
        print(f"  {module.id:23} {module.category:9} {module.description}{needs}")
    print()


def print_report(report: dict) -> None:
    print(json.dumps(report, ensure_ascii=False, indent=2))


def doctor(store: WorkspaceStore) -> None:
    print_report({
        "version": __version__,
        "python": platform.python_version(),
        "python_supported": sys.version_info >= (3, 11),
        "os": platform.system(),
        "nmcli_available": bool(shutil.which("nmcli")),
        "go_optional": bool(shutil.which("go")),
        "session_directory": str(store.root),
        "runtime_dependencies": "Python standard library only",
    })


def run_tokens(tokens: list[str], current: str, store: WorkspaceStore) -> tuple[str, bool]:
    """Process a command and return (active_workspace, should_exit)."""
    if not tokens:
        return current, False
    command, *rest = tokens
    if command in ("help", "-h", "--help", "?"):
        print(HELP)
    elif command in ("modules", "list"):
        if rest:
            raise ValueError("Usage: modules")
        show_modules()
    elif command == "doctor":
        if rest:
            raise ValueError("Usage: doctor")
        doctor(store)
    elif command == "run":
        if not rest:
            raise ValueError("Usage: run MODULE [--target DOMAIN]")
        module_id, *flags = rest
        if not flags:
            override = None
        elif len(flags) == 2 and flags[0] == "--target":
            override = flags[1]
        else:
            raise ValueError("Usage: run MODULE [--target DOMAIN]")
        data = store.load(current, create_default=True)
        target = override if override is not None else data["target"]
        try:
            result = modules.execute(module_id, target)
        except OperationError as error:
            data["history"].append({
                "at": timestamp(), "module": module_id, "target": target,
                "status": "error", "message": str(error)[:240],
            })
            store.save(data)
            raise
        data["history"].append({
            "at": timestamp(), "module": module_id, "target": target,
            "status": "ok", "result": result,
        })
        store.save(data)
        print_report(result)
    elif command == "target":
        if not rest or rest[0] == "show":
            if len(rest) > 1:
                raise ValueError("Usage: target show")
            data = store.load(current, create_default=True)
            print("Target:", data["target"] or "(not set)")
        elif rest[0] in ("set", "clear"):
            if rest[0] == "set" and len(rest) != 2:
                raise ValueError("Usage: target set DOMAIN")
            if rest[0] == "clear" and len(rest) != 1:
                raise ValueError("Usage: target clear")
            data = store.load(current, create_default=True)
            data["target"] = rest[1] if rest[0] == "set" else None
            store.save(data)
            print("Target:", data["target"] or "(cleared)")
        else:
            raise ValueError("Usage: target set DOMAIN | show | clear")
    elif command == "session":
        if not rest:
            raise ValueError("Usage: session new NAME | use NAME | list | show | export FILE")
        action, *args = rest
        if action == "list" and not args:
            names = store.list_names()
            print("Sessions:", ", ".join(names) if names else "(none)")
        elif action == "show" and not args:
            print_report(store.load(current, create_default=True))
        elif action == "new" and len(args) == 1:
            store.create(args[0])
            current = args[0]
            print("Created and selected session:", current)
        elif action == "use" and len(args) == 1:
            store.load(args[0], create_default=True)
            current = args[0]
            print("Active session:", current)
        elif action == "export" and len(args) == 1:
            path = store.export(current, Path(args[0]))
            print("Exported private session:", path)
        else:
            raise ValueError("Usage: session new NAME | use NAME | list | show | export FILE")
    elif command == "note":
        if rest == ["list"]:
            data = store.load(current, create_default=True)
            for item in data["notes"]:
                print(f"  {item['at']}  {item['text']}")
            if not data["notes"]:
                print("No notes yet.")
        elif len(rest) >= 2 and rest[0] == "add":
            data = store.load(current, create_default=True)
            note = " ".join(rest[1:]).strip()
            if not note or len(note) > 2000:
                raise ValueError("Notes must contain 1-2000 characters.")
            data["notes"].append({"at": timestamp(), "text": note})
            data["notes"] = data["notes"][-100:]
            store.save(data)
            print("Note saved in session:", current)
        else:
            raise ValueError("Usage: note add TEXT | note list")
    elif command == "history":
        if rest:
            raise ValueError("Usage: history")
        data = store.load(current, create_default=True)
        for item in data["history"][-20:]:
            print(f"  {item['at']}  {item['status']:5} {item['module']}")
        if not data["history"]:
            print("No executions recorded.")
    elif command == "tab":
        if rest:
            raise ValueError("Usage: tab")
        print("In a new terminal tab, execute:")
        print("  shadowhunter --session " + shlex.quote(current) + " shell")
        print("Workspace data is reloaded on each command; no shared RAM process.")
    elif command in ("exit", "quit"):
        if rest:
            raise ValueError("Usage: exit")
        return current, True
    else:
        raise ValueError("Unknown command: " + command + ". Type 'help'.")
    return current, False


def shell(store: WorkspaceStore, current: str) -> int:
    store.load(current, create_default=True)
    print(BANNER)
    print("Active session:", current, "| type 'help' for commands.")
    while True:
        try:
            raw = input(f"\nshadowhunter:{current} > ")
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye. Session saved.")
            return 0
        try:
            tokens = shlex.split(raw)
            current, stop = run_tokens(tokens, current, store)
            if stop:
                print("Goodbye. Session saved.")
                return 0
        except (ValueError, WorkspaceError, OperationError, OSError) as error:
            print("✗", error, file=sys.stderr)


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args == ["--version"]:
        print(__version__)
        return 0
    session = "default"
    if args[:1] == ["--session"]:
        if len(args) < 3:
            print("Usage: shadowhunter --session NAME [shell|COMMAND]", file=sys.stderr)
            return 2
        session, args = args[1], args[2:]
    store = WorkspaceStore()
    try:
        store.check_name(session)
        if not args or args == ["shell"]:
            if not sys.stdin.isatty():
                print(HELP)
                return 0
            return shell(store, session)
        _current, _stop = run_tokens(args, session, store)
        return 0
    except (ValueError, WorkspaceError, OperationError, OSError) as error:
        print("✗", error, file=sys.stderr)
        return 2
