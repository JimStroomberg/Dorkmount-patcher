"""Desktop entry point and explicit offline preparation commands."""

import argparse
import json
import sys
from pathlib import Path

from . import __version__


def main(argv=None):
    parser = argparse.ArgumentParser(description="Dorkmount screen updater")
    parser.add_argument("--version", action="version", version=__version__)
    parser.add_argument("--demo", action="store_true", help="Preview the app without accessing hardware")
    parser.add_argument("--screenshot", type=Path, help=argparse.SUPPRESS)
    sub = parser.add_subparsers(dest="command")
    offline = sub.add_parser("prepare", help="Verify and prepare firmware files without device access")
    offline.add_argument("--stock-dir", type=Path, required=True)
    offline.add_argument("--output", type=Path, required=True)
    offline.add_argument("--restore", action="store_true")
    args = parser.parse_args(argv)
    if args.command == "prepare":
        from .firmware import export, prepare, target
        originals = {name: (args.stock_dir / item["stock_filename"]).read_bytes()
                     for name, item in target()["components"].items()}
        print(json.dumps(export(prepare(originals, args.restore), args.output), indent=2))
        return 0
    if args.screenshot and not args.demo:
        parser.error("Screenshots require --demo")
    try:
        from .gui import run
    except ImportError as error:
        if getattr(sys, "frozen", False):
            parser.exit(1, f"The updater could not load a desktop component. Run it on a supported Linux desktop. Details: {error}\n")
        parser.exit(1, "Desktop components are missing. Install dorkmount-patcher[desktop].\n")
    return run(args.demo, args.screenshot)


if __name__ == "__main__":
    sys.exit(main())
