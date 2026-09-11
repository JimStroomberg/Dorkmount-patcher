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
    match = re.fullmatch(r"(\d+\.\d+\.\d+)(?:a([1-9]\d*))?", version)
    if not match:
        raise ValueError("Release versions must be X.Y.Z or X.Y.ZaN (N starts at 1).")
    if (root / "VERSION").read_text().strip() != version:
        raise ValueError("VERSION must match pyproject.toml.")
    module = ast.parse((root / "src/dorkmount_patcher/__init__.py").read_text())
    actual = next(ast.literal_eval(node.value) for node in module.body
                  if isinstance(node, ast.Assign)
                  and any(isinstance(t, ast.Name) and t.id == "__version__" for t in node.targets))
    if actual != version:
        raise ValueError("Runtime version must match pyproject.toml.")
    base, alpha = match.groups()
    return {
        "version": version,
        "tag": f"v{base}-alpha.{alpha}" if alpha else f"v{base}",
        "debian_version": f"{base}~alpha{alpha}-1" if alpha else f"{base}-1",
        "arch_version": f"{base}alpha{alpha}" if alpha else base,
        "prerelease": alpha is not None,
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
