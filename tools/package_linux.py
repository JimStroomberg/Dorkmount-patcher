#!/usr/bin/env python3
"""Create a Debian package and a makepkg input from the same frozen app."""

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import tarfile
from pathlib import Path

from release_metadata import ROOT, metadata


def copy(source, destination, mode=0o644):
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, destination)
    destination.chmod(mode)


def build(bundle, output):
    info = metadata()
    platforms = json.loads((ROOT / "packaging/platforms.json").read_text())
    output.mkdir(parents=True, exist_ok=True)
    tree = output / "rootfs"
    if tree.exists():
        raise FileExistsError(f"Use a fresh package output directory: {tree}")
    tree.mkdir()
    shutil.copytree(bundle, tree / "opt/dorkmount-patcher", symlinks=True)
    launcher = tree / "usr/bin/dorkmount-patcher"
    launcher.parent.mkdir(parents=True)
    launcher.write_text('#!/bin/sh\nexec /opt/dorkmount-patcher/Dorkmount-patcher "$@"\n')
    launcher.chmod(0o755)
    copy(ROOT / "packaging/dorkmount-patcher.desktop",
         tree / "usr/share/applications/dorkmount-patcher.desktop")
    copy(ROOT / "packaging/io.github.JimStroomberg.DorkmountPatcher.svg",
         tree / "usr/share/icons/hicolor/scalable/apps/io.github.JimStroomberg.DorkmountPatcher.svg")
    copy(ROOT / "src/dorkmount_patcher/data/70-dorkmount-patcher.rules",
         tree / "usr/lib/udev/rules.d/70-dorkmount-patcher.rules")
    copy(ROOT / "LICENSE", tree / "usr/share/licenses/dorkmount-patcher/LICENSE")
    copy(ROOT / "THIRD_PARTY.md", tree / "usr/share/doc/dorkmount-patcher/THIRD_PARTY.md")
    subprocess.run(["desktop-file-validate", str(tree / "usr/share/applications/dorkmount-patcher.desktop")], check=True)

    # makepkg supplies native Arch metadata, mtree, compression and installation hooks.
    arch = output / "cachyos-input"
    arch.mkdir()
    with tarfile.open(arch / "rootfs.tar.gz", "w:gz", dereference=False) as archive:
        archive.add(tree, arcname="rootfs")
    checksum = hashlib.sha256((arch / "rootfs.tar.gz").read_bytes()).hexdigest()
    deps = " ".join(repr(dep) for dep in platforms["cachyos_dependencies"])
    (arch / "PKGBUILD").write_text(
        f"# Maintainer: {info['maintainer']}\n"
        "pkgname=dorkmount-patcher\n"
        f"pkgver={info['arch_version']}\npkgrel=1\n"
        "pkgdesc='Add custom app support to the Dark Mount screen'\n"
        "arch=('x86_64')\n"
        f"url='{info['repository']}'\nlicense=('GPL-3.0-only')\n"
        f"depends=({deps})\n"
        "options=('!strip' '!debug')\ninstall=cachyos.install\n"
        "source=('rootfs.tar.gz')\n"
        f"sha256sums=('{checksum}')\n"
        'package() {\n    cp -a "$srcdir/rootfs/." "$pkgdir/"\n}\n'
    )
    copy(ROOT / "packaging/cachyos.install", arch / "cachyos.install")

    control = tree / "DEBIAN"
    control.mkdir()
    size = sum(p.stat().st_size for p in tree.rglob("*") if p.is_file() and not p.is_symlink()) // 1024
    (control / "control").write_text(
        f"Package: dorkmount-patcher\nVersion: {info['debian_version']}\n"
        "Section: utils\nPriority: optional\nArchitecture: amd64\n"
        f"Maintainer: {info['maintainer']}\nInstalled-Size: {size}\n"
        f"Depends: {', '.join(platforms['debian_dependencies'])}\n"
        f"Homepage: {info['repository']}\n"
        "Description: Add custom app support to the Dark Mount screen\n"
        " Guided community firmware updater for the supported Dark Mount model.\n"
        " Includes a hardware-free demo and an independent developer guide.\n"
    )
    for name in ("postinst", "postrm"):
        copy(ROOT / f"packaging/debian-{name}", control / name, 0o755)
    deb = output / info["debian_filename"]
    subprocess.run(["dpkg-deb", "--root-owner-group", "--build", str(tree), str(deb)], check=True)
    (output / "release-metadata.json").write_text(json.dumps({**info,
        "source_commit": os.environ.get("SOURCE_COMMIT", "local"),
        "source_dirty": os.environ.get("SOURCE_DIRTY", "true") == "true",
        "source_date_epoch": os.environ.get("SOURCE_DATE_EPOCH", ""),
        "platforms": platforms,
        "hardware_verified": False,
    }, indent=2) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("bundle", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    build(args.bundle, args.output)
