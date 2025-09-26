#!/usr/bin/env python3
"""Utility to update the Raspberry Pi base URL across project files.

Usage
-----
python set_pi_server_url.py 192.168.1.42
python set_pi_server_url.py http://192.168.1.42:6000
python set_pi_server_url.py https://my-tunnel.example.com

The script touches the following files:
- windows_ai_controller.py (default PI_BASE_URL constant)
- frontend/vite.config.js (fallback define for __PI_API__)
Optionally, when a `.env` file exists in `frontend/`, the script will
update or append `VITE_PI_API_BASE`.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
WINDOWS_CONTROLLER = ROOT / "windows_ai_controller.py"
VITE_CONFIG = ROOT / "frontend" / "vite.config.js"
FRONTEND_ENV = ROOT / "frontend" / ".env"

PI_ASSIGN_PATTERN = re.compile(
    r'(self\.PI_BASE_URL\s*=\s*")([^"]+)(")',
    re.MULTILINE,
)
VITE_DEFINE_PATTERN = re.compile(
    r'(env\.VITE_PI_API_BASE\s*\|\|\s*")([^"]+)(")',
    re.MULTILINE,
)


def normalise_url(raw: str) -> str:
    value = raw.strip()
    if not value:
        raise ValueError("Pi URL/IP cannot be empty")

    if "://" not in value:
        # Split out port if supplied
        if ":" in value:
            host, port = value.rsplit(":", 1)
            if not port.isdigit():
                raise ValueError("Invalid port specified in Pi address")
            value = f"http://{host}:{port}"
        else:
            value = f"http://{value}:5000"

    # Remove trailing slash for consistency
    value = value.rstrip("/")
    return value


def replace_in_file(path: Path, pattern: re.Pattern[str], new_value: str) -> int:
    if not path.exists():
        raise FileNotFoundError(f"Expected file not found: {path}")

    original = path.read_text(encoding="utf-8")

    def _insert(match):
        return match.group(1) + new_value + match.group(3)

    updated, count = pattern.subn(_insert, original)

    if count == 0:
        raise RuntimeError(f"Pattern not found while updating {path}")

    if updated != original:
        path.write_text(updated, encoding="utf-8")
    return count


def update_frontend_env(new_url: str) -> None:
    if not FRONTEND_ENV.exists():
        return

    lines = FRONTEND_ENV.read_text(encoding="utf-8").splitlines()
    updated = False
    for idx, line in enumerate(lines):
        if line.startswith("VITE_PI_API_BASE="):
            lines[idx] = f"VITE_PI_API_BASE={new_url}"
            updated = True
            break
    if not updated:
        lines.append(f"VITE_PI_API_BASE={new_url}")

    FRONTEND_ENV.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("url", help="Pi base URL or IP (e.g. 192.168.1.42:5000)")
    args = parser.parse_args(argv)

    try:
        resolved_url = normalise_url(args.url)
    except ValueError as exc:
        parser.error(str(exc))
        return 2

    print(f"ℹ️  Using Pi base URL: {resolved_url}")

    replace_in_file(WINDOWS_CONTROLLER, PI_ASSIGN_PATTERN, resolved_url)
    print(f"✅ Updated {WINDOWS_CONTROLLER.relative_to(ROOT)}")

    replace_in_file(VITE_CONFIG, VITE_DEFINE_PATTERN, resolved_url)
    print(f"✅ Updated {VITE_CONFIG.relative_to(ROOT)}")

    update_frontend_env(resolved_url)
    if FRONTEND_ENV.exists():
        print(f"✅ Updated {FRONTEND_ENV.relative_to(ROOT)}")

    print("✨ Pi URL synchronised across codebase.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
