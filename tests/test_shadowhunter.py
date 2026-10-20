"""Standard-library regression tests; no network or root access needed."""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from shadowhunterkit import cli, modules, operations
from shadowhunterkit.workspace import WorkspaceError, WorkspaceStore


class WorkspaceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.store = WorkspaceStore(Path(self.tmp.name) / "sessions")

    def test_create_persist_and_export_without_overwrite(self):
        data = self.store.create("audit_01")
        data["target"] = "example.org"
        self.store.save(data)
        self.assertEqual(self.store.load("audit_01")["target"], "example.org")
        self.assertEqual(self.store.list_names(), ["audit_01"])
        exported = Path(self.tmp.name) / "export.json"
        self.store.export("audit_01", exported)
        self.assertEqual(json.loads(exported.read_text())["target"], "example.org")
        with self.assertRaises(FileExistsError):
            self.store.export("audit_01", exported)

    def test_reject_path_traversal_and_duplicates(self):
        for name in ("../other", "BadName", "a/b", "", "x" * 41):
            with self.subTest(name=name), self.assertRaises(WorkspaceError):
                self.store.create(name)
        self.store.create("lab")
        with self.assertRaises(WorkspaceError):
            self.store.create("lab")

    def test_new_session_starts_with_isolated_context(self):
        self.store.create("alpha")
        self.store.create("beta")
        alpha = self.store.load("alpha")
        alpha["notes"].append({"at": "now", "text": "hello"})
        self.store.save(alpha)
        self.assertEqual(self.store.load("beta")["notes"], [])

    def test_default_lazily_created(self):
        data = self.store.load("default", create_default=True)
        self.assertEqual(data["schema"], 1)


class OperationTests(unittest.TestCase):
    def test_domain_validation(self):
        self.assertEqual(operations.normalized_domain("Example.Org."), "example.org")
        for target in ("https://example.org", "example.org/hello", "a", "foo..bar",
                       "127.0.0.1", "bad domain.test"):
            with self.subTest(target=target), self.assertRaises(operations.OperationError):
                operations.normalized_domain(target)

    def test_registry_unique_and_callable(self):
        self.assertIn("osint.certificates", modules.REGISTRY)
        self.assertTrue(all(callable(module.action) for module in modules.REGISTRY.values()))
        with self.assertRaises(operations.OperationError):
            modules.execute("missing", None)
        with self.assertRaises(operations.OperationError):
            modules.execute("osint.certificates", None)

    def test_certificates_deduplicates_and_limits_domain(self):
        class FakeResponse:
            def __enter__(self):
                return self
            def __exit__(self, *_):
                return None
            def read(self, _size):
                return json.dumps([
                    {"name_value": "*.Example.org\napi.example.org"},
                    {"name_value": "api.example.org\nattackerexample.org"},
                    {"name_value": "evil.test"},
                ]).encode()
        with patch("shadowhunterkit.operations.urlopen", return_value=FakeResponse()):
            report = operations.osint_certificates("example.org")
        self.assertEqual(report["names"], ["api.example.org", "example.org"])
        self.assertEqual(report["total_unique"], 2)

    def test_wifi_unavailable_is_actionable(self):
        with patch("shadowhunterkit.operations.shutil.which", return_value=None):
            with self.assertRaisesRegex(operations.OperationError, "nmcli"):
                operations.wifi_status()


class CLITests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.store = WorkspaceStore(Path(self.tmp.name) / "sessions")

    def test_session_context_and_recording(self):
        current, done = cli.run_tokens(["session", "new", "work"], "default", self.store)
        self.assertEqual(current, "work")
        self.assertFalse(done)
        cli.run_tokens(["target", "set", "example.org"], current, self.store)
        with patch("shadowhunterkit.modules.execute", return_value={"ok": True}):
            cli.run_tokens(["run", "osint.certificates"], current, self.store)
        saved = self.store.load("work")
        self.assertEqual(saved["target"], "example.org")
        self.assertEqual(saved["history"][0]["result"], {"ok": True})

    def test_error_recorded_but_other_session_safe(self):
        self.store.create("secure")
        with self.assertRaises(operations.OperationError):
            cli.run_tokens(["run", "osint.certificates"], "secure", self.store)
        self.assertEqual(self.store.load("secure")["history"][0]["status"], "error")

    def test_noninteractive_version(self):
        self.assertEqual(cli.main(["--version"]), 0)


if __name__ == "__main__":
    unittest.main()
