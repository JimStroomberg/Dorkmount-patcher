#!/usr/bin/env python3
"""Preserve installed wheel license notices with the optional desktop bundle."""

import argparse
import importlib.metadata
from pathlib import Path


def collect(output):
    output.mkdir(parents=True, exist_ok=True)
    rows = []
    for name in ("PySide6", "PySide6-Essentials", "PySide6-Addons", "shiboken6", "pyinstaller"):
        distribution = importlib.metadata.distribution(name)
        copied = []
        for entry in distribution.files or []:
            if any(part.lower() in ("licenses", "license", "copying") for part in entry.parts) or entry.name.lower().startswith(("license", "copying")):
                source = distribution.locate_file(entry)
                if not source.is_file():
                    continue
                destination = output / name / str(entry)
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes(source.read_bytes())
                copied.append(str(destination.relative_to(output)))
        if not copied:
            # PySide6 6.11.2 wheels declare their license in METADATA but do not
            # include license files. Ship that metadata plus the unmodified
            # license directory from the matching official source release.
            destination = output / name / "METADATA.txt"
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(distribution.read_text("METADATA") or "")
        rows.append(f"{name} {distribution.version}: {len(copied)} wheel notice files; metadata/source notices supplied")
    source_notices = Path(__file__).resolve().parents[1] / "packaging/licenses"
    for source in source_notices.rglob("*"):
        if source.is_file():
            destination = output / source.relative_to(source_notices)
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(source.read_bytes())
    # Copyright notices for the Linux image's system libraries are retained too.
    for source in Path("/usr/share/doc").glob("*/copyright"):
        destination = output / "linux-system" / source.parent.name / "copyright"
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(source.read_bytes())
    python_notice = Path("/usr/local/lib/python3.13/LICENSE.txt")
    if python_notice.is_file():
        (output / "Python-LICENSE.txt").write_bytes(python_notice.read_bytes())
    (output / "README.txt").write_text(
        "Unmodified dependency notices copied from their installed distributions.\n\n"
        + "\n".join(rows) + "\n\nQt sources and licenses: https://www.qt.io/download-qt-installer-oss\n"
        "PyInstaller: https://github.com/pyinstaller/pyinstaller\n"
        "Python: https://www.python.org/downloads/source/\n"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    collect(parser.parse_args().output)
