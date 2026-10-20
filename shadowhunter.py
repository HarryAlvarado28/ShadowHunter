#!/usr/bin/env python3
"""Backward-compatible direct launcher; use python3 -m shadowhunterkit."""

from shadowhunterkit.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
