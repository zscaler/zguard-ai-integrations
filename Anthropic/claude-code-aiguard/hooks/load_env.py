#!/usr/bin/env python3
"""
Load environment variables from .env file for AIGuard hooks.

This helper module loads environment variables from a .env file
when the hooks are executed by Claude Code.
"""

import os
from pathlib import Path


def load_env():
    """Load environment variables from .env file if it exists."""
    env_file = Path(__file__).parent.parent / ".env"

    if not env_file.exists():
        return  # No .env file, use system environment variables

    try:
        with open(env_file, "r") as f:
            for line in f:
                line = line.strip()

                # Skip empty lines and comments
                if not line or line.startswith("#"):
                    continue

                # Parse KEY=VALUE
                if "=" in line:
                    key, value = line.split("=", 1)
                    key = key.strip()
                    value = value.strip()

                    # Only set if not already in environment
                    if key and value and key not in os.environ:
                        os.environ[key] = value
    except Exception:
        pass  # Fail silently, use system environment variables


# Auto-load when imported
load_env()
