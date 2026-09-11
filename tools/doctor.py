#!/usr/bin/env python3
"""Read-only source-build prerequisite check. Never installs packages or opens USB."""

import argparse
import importlib.util
import shutil
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package", action="store_true", help="Check Docker package-build prerequisites")
    args = parser.parse_args()
    requirements = {"Python 3.11+": sys.version_info >= (3, 11)}
    if args.package:
        requirements.update({name: shutil.which(name) is not None for name in ("git", "docker")})
    else:
        requirements.update({name: importlib.util.find_spec(name) is not None
                             for name in ("PySide6", "pytest", "build")})
        if sys.platform == "linux":
            requirements.update({name: shutil.which(name) is not None
                                 for name in ("udevadm", "pkexec", "systemd-inhibit")})
    for name, present in requirements.items():
        print(f"{'OK' if present else 'MISSING'}: {name}")
    if not all(requirements.values()):
        print("See docs/BUILDING.md and docs/DEPENDENCIES.md for installation instructions.")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
