"""Minimal unit checks for two small, pure validation helpers."""

import unittest

from shadowhunterkit.operations import OperationError, normalized_domain
from shadowhunterkit.workspace import WorkspaceError, WorkspaceStore


class CoreTests(unittest.TestCase):
    def test_domain_name(self):
        self.assertEqual(normalized_domain("Example.Org."), "example.org")
        with self.assertRaises(OperationError):
            normalized_domain("https://example.org/path")

    def test_session_name(self):
        self.assertEqual(WorkspaceStore.check_name("audit_1"), "audit_1")
        with self.assertRaises(WorkspaceError):
            WorkspaceStore.check_name("../audit")


if __name__ == "__main__":
    unittest.main()
