#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Build the exact DMR3 Dashboard candidate offline; never accesses hardware.

Requires LLVM 22.1.8 and the three exact official 1.29.0 images. Full images are
exported only when every preimage, section length and complete output hash match.
This candidate has not been verified on a physical keyboard.
"""

import argparse
import hashlib
import json
import pathlib
import subprocess
import tempfile

ROOT = pathlib.Path(__file__).resolve().parent
SPEC = json.loads((ROOT.parent / "targets/1.29.0-dmr3.json").read_text())
STOCK = {n: (v["size"], v["stock_sha256"]) for n, v in SPEC["components"].items()}
EXPECTED = {n: v["patched_sha256"] for n, v in SPEC["components"].items()}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def checked_input(path, name):
    raw = pathlib.Path(path).read_bytes()
    if (len(raw), sha(raw)) != STOCK[name]:
        raise ValueError(f"{name}: input is not the exact supported official 1.29.0 image")
    return raw


def build(main, dock, numpad, output):
    originals = {n: checked_input(p, n) for n, p in
                 (("main", main), ("dock", dock), ("numpad", numpad))}
    output = pathlib.Path(output)
    if output.exists():
        raise FileExistsError("Output must be a new directory")
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".dmr3-build-", dir=output.parent) as temporary:
        work = pathlib.Path(temporary)
        flags = ["--target=arm-none-eabi", "-mcpu=cortex-m4", "-mthumb", "-Oz",
                 "-ffreestanding", "-fno-builtin", "-fno-unwind-tables",
                 "-fno-asynchronous-unwind-tables", "-fdata-sections", "-ffunction-sections"]
        sources = ("live-draw.c", "dashboard.c", "hooks.S")
        for name in sources:
            subprocess.run(["clang", *flags, "-c", str(ROOT / name),
                            "-o", str(work / (name + ".o"))], check=True, capture_output=True)
        subprocess.run(["ld.lld", "-T", str(ROOT / "live-draw.ld"),
                        *(str(work / (n + ".o")) for n in sources),
                        "-o", str(work / "dashboard.elf")], check=True, capture_output=True)
        candidates = {n: bytearray(raw) for n, raw in originals.items()}
        occupied = {n: set() for n in originals}
        for region in SPEC["patches"]:
            name, offset, length = region["component"], region["offset"], region["length"]
            extent = set(range(offset, offset + length))
            if offset < 0 or length <= 0 or offset + length > len(originals[name]):
                raise ValueError("Invalid patch extent")
            if occupied[name] & extent:
                raise ValueError("Overlapping patches")
            occupied[name].update(extent)
            if sha(originals[name][offset:offset + length]) != region["original_sha256"]:
                raise ValueError("Original patch bytes differ")
            if "section" in region:
                raw_path = work / (region["section"][1:] + ".bin")
                subprocess.run(["llvm-objcopy", "-O", "binary",
                                "--only-section=" + region["section"],
                                str(work / "dashboard.elf"), str(raw_path)],
                               check=True, capture_output=True)
                data = raw_path.read_bytes()
            else:
                data = {("main", 0x85e4): b"\x38", ("dock", 0x4ee0): b"\x76\xd0",
                        ("dock", 0x3748): b"\x00\x28"}[(name, offset)]
            if len(data) != length:
                raise ValueError("Compiler output differs from pinned candidate")
            candidates[name][offset:offset + length] = data
        for name, raw in candidates.items():
            if len(raw) != len(originals[name]) or sha(raw) != EXPECTED[name]:
                raise ValueError(f"{name}: output differs from pinned candidate; nothing exported")
        record = dict(protocol="DMR3", hardware_io=False, hardware_verified=False,
                      source_sha256={n: sha(v) for n, v in originals.items()},
                      output_sha256=EXPECTED,
                      clang=subprocess.check_output(["clang", "--version"], text=True).splitlines()[0])
        output.mkdir()
        for name, raw in candidates.items():
            (output / f"{name}-dmr3.bin").write_bytes(raw)
            (output / f"{name}-stock.bin").write_bytes(originals[name])
        (output / "dashboard.elf").write_bytes((work / "dashboard.elf").read_bytes())
        (output / "manifest.json").write_text(json.dumps(record, indent=2) + "\n")
        return record


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("main", "dock", "numpad", "output"):
        parser.add_argument("--" + name, type=pathlib.Path, required=True)
    args = parser.parse_args()
    try:
        print(json.dumps(build(args.main, args.dock, args.numpad, args.output), indent=2))
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        parser.exit(1, f"DMR3 build refused: {error}\n")
