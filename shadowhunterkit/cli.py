"""Terminal-first, dependency-free ShadowHunter command interface."""

from __future__ import annotations

import json
import ipaddress
import platform
import shlex
import shutil
import sys
from pathlib import Path

from . import __version__, catalog, modules
from .operations import OperationError, normalized_domain
from .workspace import WorkspaceError, WorkspaceStore, timestamp

QUICK_ACTIONS = ("system.info", "network.interfaces", "wifi.status", "osint.certificates")

BANNER = """
  ╔════════════════════════════════════════╗
  ║  🛡️ SHADOWHUNTER  /  Security Workbench  ║
  ╚════════════════════════════════════════╝
  OSINT · Network · Wireless · Workspaces
  [1] System  [2] Network  [3] Wi-Fi  [4] OSINT
  [m] Modules [h] Help     [0] Exit
"""

HELP = """Commands:
  modules                             List available modules
  run ID [--target VALUE] [--dictionary NAME]   Run an explicit module
  module add PATH | add URL --sha256 HASH | remove ID | list
  dictionary add PATH [NAME] | remove NAME | list
  target set DOMAIN | show | clear    Store the current research target
  scope add ASSET | remove ASSET | list   Declare assets for an assessment
  session new NAME | use NAME | list | show
  session export FILE                 Export current workspace (private JSON)
  note add TEXT | list                Keep concise field notes
  history                             Recent module executions
  tab                                 Command to resume in another terminal tab
  doctor                              Check local runtime and optional tooling
  1 | 2 | 3 | 4                      Quick menu actions
  m | h | 0                          Modules, help or exit
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
        "go_compiler_optional": bool(shutil.which("go")),
        "evidence_engine": "go" if (
            Path(__file__).resolve().parent.parent / "bin" / "shadowhunter-worker"
        ).is_file() else "python",
        "session_directory": str(store.root),
        "runtime_dependencies": "Python standard library only",
    })


def run_tokens(tokens: list[str], current: str, store: WorkspaceStore) -> tuple[str, bool]:
    """Process a command and return (active_workspace, should_exit)."""
    if not tokens:
        return current, False
    command, *rest = tokens
    if command in ("0",):
        return current, True
    if command in ("1", "2", "3", "4"):
        if rest:
            raise ValueError("Quick actions do not take arguments; use run MODULE --target NAME.")
        return run_tokens(["run", QUICK_ACTIONS[int(command) - 1]], current, store)
    if command == "m":
        return run_tokens(["modules"], current, store)
    if command == "h":
        return run_tokens(["help"], current, store)
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
    elif command == "module":
        if rest == ["list"]:
            entries = catalog.read_catalog()["modules"]
            for name, meta in sorted(entries.items()):
                print(f"  {name:25} {meta['runtime']:8} {meta['source']}")
            if not entries:
                print("No community modules registered.")
        elif len(rest) == 2 and rest[0] == "remove":
            catalog.remove_module(rest[1])
            print("Module unregistered (original source preserved).")
        elif len(rest) == 2 and rest[0] == "add":
            meta = catalog.add_local(rest[1])
            print("Registered:", meta["id"], "|", meta["runtime"])
            print("Community code runs with your user permissions; review its source first.")
        elif len(rest) == 4 and rest[0] == "add" and rest[2] == "--sha256":
            meta = catalog.add_remote(rest[1], rest[3])
            print("Downloaded and registered verified archive:", meta["id"])
            print("Review its source before running; extensions are NOT sandboxed.")
        else:
            raise ValueError("Usage: module add PATH | add URL --sha256 HASH | remove ID | list")
    elif command == "dictionary":
        if rest == ["list"]:
            entries = catalog.read_catalog()["dictionaries"]
            for name, item in sorted(entries.items()):
                print(f"  {name:20} {item['type']:10} {item['path']}")
            if not entries:
                print("No dictionaries indexed.")
        elif len(rest) == 2 and rest[0] == "remove":
            catalog.remove_dictionary(rest[1])
            print("Dictionary reference removed; files preserved.")
        elif len(rest) in (2, 3) and rest[0] == "add":
            item = catalog.add_dictionary(rest[1], rest[2] if len(rest) == 3 else None)
            print("Dictionary indexed:", item["path"])
        else:
            raise ValueError("Usage: dictionary add PATH [NAME] | remove NAME | list")
    elif command == "run":
        if not rest:
            raise ValueError("Usage: run ID [--target VALUE] [--dictionary NAME]")
        module_id, *flags = rest
        if len(flags) % 2:
            raise ValueError("Options must have values: --target VALUE --dictionary NAME")
        args = {}
        for pos in range(0, len(flags), 2):
            if flags[pos] not in ("--target", "--dictionary") or flags[pos] in args:
                raise ValueError("Only --target and --dictionary are supported.")
            args[flags[pos]] = flags[pos + 1]
        data = store.load(current, create_default=True)
        target = args.get("--target", data["target"])
        try:
            result = modules.execute(module_id, target, args.get("--dictionary"))
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
    elif command == "scope":
        if not rest:
            raise ValueError("Usage: scope add ASSET | remove ASSET | list")
        action, *args = rest
        data = store.load(current, create_default=True)
        if action == "list" and not args:
            print("Declared scope:", ", ".join(data["scope"]) or "(empty)")
        elif action in ("add", "remove") and len(args) == 1:
            value = args[0].strip().lower()
            try:
                try:
                    value = str(ipaddress.ip_network(value, strict=False))
                except ValueError:
                    value = normalized_domain(value)
            except OperationError as error:
                raise ValueError("Provide a domain, IP address or CIDR range.") from error
            if action == "add" and value not in data["scope"]:
                data["scope"].append(value)
                data["scope"].sort()
                store.save(data)
            elif action == "remove":
                data["scope"] = [asset for asset in data["scope"] if asset != value]
                store.save(data)
            print("Declared scope:", ", ".join(data["scope"]) or "(empty)")
        else:
            raise ValueError("Usage: scope add ASSET | remove ASSET | list")
        print("Reminder: scope declarations do not replace written authorization.")
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
