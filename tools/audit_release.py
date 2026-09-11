#!/usr/bin/env python3
"""Audit and checksum only explicitly selected distributable files."""

import argparse
import hashlib
import io
import json
import posixpath
import subprocess
import tarfile
import zipfile
from pathlib import Path, PurePosixPath

from release_metadata import metadata

FORBIDDEN = {".git", ".local", ".venv", ".env", ".DS_Store", "captures", "upstream"}
EXTENSIONS = {".bin", ".elf", ".o", ".hex", ".pcap", ".pcapng", ".pem", ".key"}


def check_member(name, link=None):
    path = PurePosixPath(name)
    if (path.is_absolute() or ".." in path.parts or FORBIDDEN.intersection(path.parts)
            or path.suffix in EXTENSIONS or any(p.startswith("private-") for p in path.parts)):
        raise ValueError(f"Forbidden release member: {name}")
    if link:
        resolved = posixpath.normpath(posixpath.join(str(path.parent), link))
        if PurePosixPath(link).is_absolute() or resolved == ".." or resolved.startswith("../"):
            raise ValueError(f"Release symlink escapes the package: {name}")


def audit(path):
    if path.suffix == ".whl":
        with zipfile.ZipFile(path) as archive:
            for name in archive.namelist():
                check_member(name)
    else:
        if path.suffix == ".deb":
            raw = subprocess.check_output(["dpkg-deb", "--fsys-tarfile", str(path)])
            source = io.BytesIO(raw)
        elif path.name.endswith(".pkg.tar.zst"):
            raw = subprocess.check_output(["bsdtar", "-cf", "-", "--format=pax", "@" + str(path)])
            source = io.BytesIO(raw)
        elif path.name.endswith(".tar.gz"):
            source = path.open("rb")
        else:
            return
        with source, tarfile.open(fileobj=source) as archive:
            for member in archive:
                check_member(member.name, member.linkname if member.issym() or member.islnk() else None)
                if not (member.isfile() or member.isdir() or member.issym() or member.islnk()):
                    raise ValueError(f"Special device in release: {member.name}")


def assets(directory):
    info = metadata()
    expected = [
        f"dorkmount-patcher_{info['debian_version']}_amd64.deb",
        f"dorkmount-patcher-{info['arch_version']}-1-x86_64.pkg.tar.zst",
        f"Dorkmount-patcher-{info['version']}-linux-x86_64.tar.gz",
        f"dorkmount_patcher-{info['version']}.tar.gz",
        f"dorkmount_patcher-{info['version']}-py3-none-any.whl",
        "release-metadata.json", "build-requirements.txt",
    ]
    result = [directory / name for name in expected]
    if any(not item.is_file() for item in result):
        raise FileNotFoundError("Release is missing expected assets: " + ", ".join(
            str(item) for item in result if not item.is_file()))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("--copy-to", type=Path)
    args = parser.parse_args()
    files = assets(args.directory)
    rows = {}
    for path in files:
        audit(path)
        rows[path.name] = {"sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                           "bytes": path.stat().st_size}
    checksums = args.directory / "SHA256SUMS"
    checksums.write_text("".join(f"{row['sha256']}  {name}\n" for name, row in rows.items()))
    report = args.directory / "artifact-manifest.json"
    report.write_text(json.dumps(rows, indent=2) + "\n")
    if args.copy_to:
        import shutil
        args.copy_to.mkdir(parents=True, exist_ok=True)
        if any(args.copy_to.iterdir()):
            raise FileExistsError("Use an empty release staging directory.")
        for path in files + [checksums, report]:
            shutil.copyfile(path, args.copy_to / path.name)
    print(f"Audited {len(rows)} release assets; no private directories or full firmware members.")


if __name__ == "__main__":
    main()
