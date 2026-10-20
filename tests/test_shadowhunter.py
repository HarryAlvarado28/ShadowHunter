"""Only three fast checks for critical behavior; no network or root required."""

import tempfile
import unittest
from pathlib import Path

from shadowhunterkit import evidence, operations
from shadowhunterkit.workspace import WorkspaceError, WorkspaceStore


class CoreTests(unittest.TestCase):
    def test_private_session_persists(self):
        with tempfile.TemporaryDirectory() as directory:
            store = WorkspaceStore(Path(directory) / "sessions")
            item = store.create("audit")
            item["scope"] = ["example.org"]
            store.save(item)
            self.assertEqual(store.load("audit")["scope"], ["example.org"])
            with self.assertRaises(WorkspaceError):
                store.create("../escape")

    def test_domain_validation(self):
        self.assertEqual(operations.normalized_domain("Example.Org."), "example.org")
        with self.assertRaises(operations.OperationError):
            operations.normalized_domain("https://example.org/unsafe")

    def test_local_sha256(self):
        with tempfile.TemporaryDirectory() as directory:
            Path(directory, "proof.txt").write_text("hello", encoding="utf-8")
            report = evidence._python_hash(Path(directory))
            self.assertEqual(
                report["files"][0]["sha256"],
                "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824",
            )
            self.assertEqual(report["engine"], "python")


if __name__ == "__main__":
    unittest.main()
