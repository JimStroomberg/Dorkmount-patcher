#!/usr/bin/env python3
"""Reproduce the installed DMR2 image from exact user-supplied stock firmware.

Offline only. No USB imports, downloads, device access or flashing commands.
Outputs are emitted only if the compiled result matches the tested image hashes.
"""

import argparse
import hashlib
import json
import pathlib
import subprocess
import tempfile

ROOT = pathlib.Path(__file__).resolve().parent
STOCK = {
    "main": (85508, "94d6927103b1a0bdbe8a214e90fb7f0bcc4f891a546ada8f63d0f0d2869c5b70"),
    "dock": (81000, "d2cbc938269e9c2272c3667320c625cdd418f0dda7e079050c45dbc1f6ebb0df"),
    "numpad": (325200, "12a57913e1a3bf4ecddd95a4877d93fbd5fa9b8c9ece988f535f5e81500baf1d"),
}
EXPECTED = {
    "main": "23fa16e4e5bc0fbc520bdfadc35e3d3d2e2cbbdd45ee34651336ce647a421c02",
    "dock": "676f8f535a1d539fb104a87ecddd3e4ab3772eec15d63b06aa0b6b1608bd5b5e",
    "numpad": STOCK["numpad"][1],
}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def checked_input(path, name):
    data = pathlib.Path(path).read_bytes()
    if (len(data), sha(data)) != STOCK[name]:
        raise ValueError(f"{name}: input is not the exact supported official 1.29.0 image")
    return data


def build(main, dock, numpad, output):
    originals = {
        name: checked_input(path, name)
        for name, path in [("main", main), ("dock", dock), ("numpad", numpad)]
    }
    output = pathlib.Path(output)
    if output.exists():
        raise FileExistsError("Output must be a new directory")
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".dmr2-build-", dir=output.parent) as temporary:
        work = pathlib.Path(temporary)
        commands = [
            [
                "clang",
                "--target=arm-none-eabi",
                "-mcpu=cortex-m4",
                "-mthumb",
                "-Oz",
                "-ffreestanding",
                "-fno-builtin",
                "-fno-unwind-tables",
                "-fno-asynchronous-unwind-tables",
                "-fdata-sections",
                "-ffunction-sections",
                "-c",
                str(ROOT / "live-draw.c"),
                "-o",
                str(work / "handler.o"),
            ],
            [
                "clang",
                "--target=arm-none-eabi",
                "-mcpu=cortex-m4",
                "-mthumb",
                "-c",
                str(ROOT / "live-draw-hooks.S"),
                "-o",
                str(work / "hooks.o"),
            ],
            [
                "ld.lld",
                "-T",
                str(ROOT / "live-draw.ld"),
                str(work / "handler.o"),
                str(work / "hooks.o"),
                "-o",
                str(work / "live.elf"),
            ],
        ]
        for command in commands:
            subprocess.run(command, check=True, capture_output=True, text=True)
        patched_dock = bytearray(originals["dock"])
        ranges = []
        for section, address, length in [
            (".clock_entry", 0x08009A60, 4),
            (".text", 0x08009A64, 288),
            (".dispatch_hook", 0x0800C058, 4),
        ]:
            path = work / (section[1:] + ".bin")
            subprocess.run(
                [
                    "llvm-objcopy",
                    "-O",
                    "binary",
                    "--only-section=" + section,
                    str(work / "live.elf"),
                    str(path),
                ],
                check=True,
                capture_output=True,
            )
            raw = path.read_bytes()
            if len(raw) != length:
                raise ValueError(f"{section}: compiler output differs from the tested build")
            offset = address - 0x08006000
            patched_dock[offset : offset + length] = raw
            ranges.append(dict(section=section, address=hex(address), length=length))
        for address, before, after in [
            (0x0800AEE0, bytes.fromhex("3cd0"), bytes.fromhex("76d0")),
            (0x08009748, bytes.fromhex("0128"), bytes.fromhex("0028")),
        ]:
            offset = address - 0x08006000
            if patched_dock[offset : offset + 2] != before:
                raise ValueError("Original navigation instruction differs")
            patched_dock[offset : offset + 2] = after
            ranges.append(dict(section="navigation", address=hex(address), length=2))
        patched_main = bytearray(originals["main"])
        if patched_main[0x85E4] != 0x5A:
            raise ValueError("Main routing table mismatch")
        patched_main[0x85E4] = 0x38
        candidates = dict(
            main=bytes(patched_main), dock=bytes(patched_dock), numpad=originals["numpad"]
        )
        for name, raw in candidates.items():
            if sha(raw) != EXPECTED[name] or len(raw) != len(originals[name]):
                raise ValueError(f"{name}: output differs from the tested image; nothing exported")
        # No candidate image is exported before all identities pass.
        output.mkdir()
        for name, raw in candidates.items():
            (output / f"{name}-dmr2.bin").write_bytes(raw)
            (output / f"{name}-stock.bin").write_bytes(originals[name])
        record = dict(
            protocol="DMR2",
            source_sha256={n: sha(v) for n, v in originals.items()},
            output_sha256=EXPECTED,
            dock_ranges=ranges,
            hardware_io=False,
            clang=subprocess.check_output(["clang", "--version"], text=True).splitlines()[0],
        )
        (output / "manifest.json").write_text(json.dumps(record, indent=2) + "\n")
        return record


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("main", "dock", "numpad", "output"):
        parser.add_argument("--" + name, required=True, type=pathlib.Path)
    args = parser.parse_args()
    try:
        print(json.dumps(build(args.main, args.dock, args.numpad, args.output), indent=2))
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        parser.exit(1, f"DMR2 build refused: {error}\n")


if __name__ == "__main__":
    main()
