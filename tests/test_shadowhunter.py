"""Tiny tests for pure core rules; no I/O, network or mocks required."""

import unittest

from shadowhunterkit.validation import (
    OperationError,
    WorkspaceError,
    check_session_name,
    normalized_domain,
    parse_run_options,
)


class CoreTests(unittest.TestCase):
    def test_identifiers(self):
        self.assertEqual(normalized_domain("Example.Org."), "example.org")
        self.assertEqual(check_session_name("audit_1"), "audit_1")
        with self.assertRaises(OperationError):
            normalized_domain("https://example.org/path")
        with self.assertRaises(WorkspaceError):
            check_session_name("../audit")

    def test_command_options(self):
        self.assertEqual(
            parse_run_options(["--target", "example.org", "--dictionary", "common"]),
            {"--target": "example.org", "--dictionary": "common"},
        )
        with self.assertRaises(ValueError):
            parse_run_options(["--target", "x", "--target", "y"])


if __name__ == "__main__":
    unittest.main()
