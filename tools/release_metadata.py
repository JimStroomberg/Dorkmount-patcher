#!/usr/bin/env python3
"""One application version, explicit mappings for release/package ecosystems."""

import argparse
import ast
import json
import re
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def metadata(root=ROOT):
    project = tomllib.loads((root / "pyproject.toml").read_text())["project"]
    version = project["version"]
    match = re.fullmatch(r"(\d+\.\d+\.\d+)(?:([ab])([1-9]\d*))?", version)
    if not match:
        raise ValueError("Release versions must be X.Y.Z, X.Y.ZaN or X.Y.ZbN (N starts at 1).")
    if (root / "VERSION").read_text().strip() != version:
        raise ValueError("VERSION must match pyproject.toml.")
    module = ast.parse((root / "src/dorkmount_patcher/__init__.py").read_text())
    actual = next(ast.literal_eval(node.value) for node in module.body
                  if isinstance(node, ast.Assign)
                  and any(isinstance(t, ast.Name) and t.id == "__version__" for t in node.targets))
    if actual != version:
        raise ValueError("Runtime version must match pyproject.toml.")
    base, phase, number = match.groups()
    channel = {"a": "alpha", "b": "beta"}.get(phase)
    debian_version = f"{base}~{channel}{number}-1" if channel else f"{base}-1"
    return {
        "version": version,
        "tag": f"v{base}-{channel}.{number}" if channel else f"v{base}",
        "debian_version": debian_version,
        # GitHub normalizes '~' in asset names. Keep Debian's ordering inside the
        # package and use a portable filename for checksums and downloads.
        "debian_filename": f"dorkmount-patcher_{debian_version.replace('~', '-')}_amd64.deb",
        "arch_version": f"{base}{channel}{number}" if channel else base,
        "prerelease": channel is not None,
        "maintainer": f"{project['authors'][0]['name']} <{project['authors'][0]['email']}>",
        "repository": project["urls"]["Repository"],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check-tag")
    args = parser.parse_args()
    info = metadata()
    if args.check_tag and args.check_tag != info["tag"]:
        parser.error(f"Expected release tag {info['tag']} for this checkout.")
    print(json.dumps(info, indent=2))


if __name__ == "__main__":
    main()
