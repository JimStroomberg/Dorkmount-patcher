#!/usr/bin/env python3
"""Export only original extension bytes from an exact, verified builder output.

Run firmware/dmr2/build.py first. Full stock/patched images remain local.
This does not extract or redistribute any stock firmware routine.
"""

import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def generate(build_directory):
    spec = json.loads((ROOT / "firmware/targets/1.29.0-dmr2.json").read_text())
    stock, patched = {}, {}
    def sha(data):
        return hashlib.sha256(data).hexdigest()
    for name, item in spec["components"].items():
        stock[name] = (build_directory / f"{name}-stock.bin").read_bytes()
        patched[name] = (build_directory / f"{name}-dmr2.bin").read_bytes()
        if (len(stock[name]), sha(stock[name])) != (item["size"], item["stock_sha256"]):
            raise ValueError("Unknown stock input")
        if (len(patched[name]), sha(patched[name])) != (item["size"], item["patched_sha256"]):
            raise ValueError("Unknown builder output")
    allowed = {name: set() for name in stock}
    for region in spec["patches"]:
        name, start, length = region["component"], region["offset"], region["length"]
        if sha(stock[name][start:start + length]) != region["original_sha256"]:
            raise ValueError("Patch preimage mismatch")
        data = patched[name][start:start + length]
        region.update(replacement_hex=data.hex(), replacement_sha256=sha(data))
        allowed[name].update(range(start, start + length))
    for name in stock:
        if any(a != b and i not in allowed[name] for i, (a, b) in enumerate(zip(stock[name], patched[name]))):
            raise ValueError("Changed byte outside documented patch ranges")
    spec["source_sha256"] = {
        str(p.relative_to(ROOT)): sha(p.read_bytes())
        for p in sorted((ROOT / "firmware/dmr2").iterdir()) if p.suffix in (".c", ".S", ".ld", ".py")
    }
    spec["flashing_included"] = True
    output = ROOT / "src/dorkmount_patcher/data/dmr2.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(spec, indent=2) + "\n")
    print("Verified extension metadata written; no full firmware images exported.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("build_directory", type=Path)
    generate(parser.parse_args().build_directory)
