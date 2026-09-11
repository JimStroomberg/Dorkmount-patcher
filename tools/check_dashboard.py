#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Execute a pinned Dashboard candidate offline. Never opens a keyboard.

Full images and generated previews belong in ignored local output directories.
Synthetic image-store pixels stand in for unavailable factory artwork. Their
read and palette routines are fixtures; original menu, glyph, rectangle, window,
QLink and custom instructions execute. GPIO mode also executes LCD byte writers.
"""

import argparse
import hashlib
import json
import random
import struct
import sys
import zlib
from pathlib import Path

import unicorn as u
from dashboard_model import STACK, DrawingMachine
from unicorn import arm_const as arm

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from dorkmount_patcher.directdraw import Client  # noqa: E402
from dorkmount_patcher.qlink import DeviceError, decode, encode  # noqa: E402

REGS = [getattr(arm, f"UC_ARM_REG_R{i}") for i in range(4)]


def references(raw, ram):
    """Conservative direct-branch/literal scan; not a whole-program proof."""
    from capstone import CS_ARCH_ARM, CS_MODE_MCLASS, CS_MODE_THUMB, Cs
    from capstone.arm import (
        ARM_INS_B,
        ARM_INS_BL,
        ARM_INS_BLX,
        ARM_INS_CBNZ,
        ARM_INS_CBZ,
        ARM_OP_IMM,
    )
    regions = [(0x080097ea, 0x0800982e), (0x08009938, 0x080099a0),
               (0x08009a60, 0x08009bb8), (0x0800a470, 0x0800a5ac)]
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB | CS_MODE_MCLASS)
    md.detail = True
    found = []
    # The halfword at a45c is inside the original 32-bit branch at a45a.
    # A halfword-aligned conservative scan would misdecode it as another branch.
    assert raw[0x445a:0x445e] == bytes.fromhex("00f0b9b9")
    for offset in range(0, len(raw) - 3, 2):
        address = 0x08006000 + offset
        if address == 0x0800a45c:
            continue
        ins = next(md.disasm(raw[offset:offset+4], address), None)
        if ins and ins.id in (ARM_INS_B, ARM_INS_BL, ARM_INS_BLX, ARM_INS_CBZ, ARM_INS_CBNZ):
            dest = ins.operands[-1].imm if ins.operands[-1].type == ARM_OP_IMM else 0
            for lo, hi in regions:
                if lo <= dest < hi and not lo <= address < hi:
                    assert dest == lo, "External branch into reclaimed body"
                    found.append((hex(address), hex(dest)))
    assert set(found) == {
        ("0x8009762", "0x800a470"), ("0x800978e", "0x80097ea"),
        ("0x80098e4", "0x800a470"), ("0x800a36c", "0x800a470"),
        ("0x800a380", "0x800a470"), ("0x800af9c", "0x8009a60"),
        ("0x800c9c0", "0x8009a60"), ("0x800c9f6", "0x8009938"),
    }
    for origin, data in ((0x08006000, raw), (0x20000000, ram)):
        for offset in range(0, len(data) - 3, 2):
            value = struct.unpack_from("<I", data, offset)[0] & ~1
            for lo, hi in regions:
                if lo <= value < hi and not lo <= origin + offset < hi:
                    assert value == lo, "Literal pointer into reclaimed body"
    return found


def handoff(raw):
    """Original application's update reset only; missing bootloader is not modeled."""
    mu = u.Uc(u.UC_ARCH_ARM, u.UC_MODE_THUMB | u.UC_MODE_MCLASS)
    mu.mem_map(0x08000000, 0x40000)
    mu.mem_write(0x08006000, raw)
    mu.mem_protect(0x08000000, 0x40000, u.UC_PROT_READ | u.UC_PROT_EXEC)
    mu.mem_map(0x20000000, 0x1a000)
    mu.mem_map(0xe000e000, 0x1000)
    mu.reg_write(arm.UC_ARM_REG_CPSR, 0x20)
    mu.reg_write(arm.UC_ARM_REG_SP, STACK)
    mu.reg_write(arm.UC_ARM_REG_R0, 1)
    writes = []
    def write(uc, _access, address, size, value, _context):
        writes.append((address, size, value))
        if address == 0xe000ed0c:
            uc.emu_stop()
    for address in (0x200197fc, 0xe000ed0c):
        mu.hook_add(u.UC_HOOK_MEM_WRITE, write, begin=address, end=address+3)
    mu.emu_start(0x0800a19d, 0x08000100, count=100000)
    assert writes == [(0x200197fc, 4, 0xa55aa55a), (0xe000ed0c, 4, 0x05fa0004)]
    return writes


def initialized(raw):
    mu = u.Uc(u.UC_ARCH_ARM, u.UC_MODE_THUMB | u.UC_MODE_MCLASS)
    mu.mem_map(0x08000000, 0x40000)
    mu.mem_write(0x08006000, raw)
    mu.mem_protect(0x08000000, 0x40000, u.UC_PROT_READ | u.UC_PROT_EXEC)
    mu.mem_map(0x20000000, 0x1a000)
    mu.mem_write(0x20000000, b"\xa5" * 0x1a000)
    mu.reg_write(arm.UC_ARM_REG_CPSR, 0x20)
    mu.reg_write(arm.UC_ARM_REG_SP, STACK)
    # No write hook during scatter initialization: see original lab model caveat.
    mu.emu_start(0x080061e9, 0x0800635e, count=5_000_000)
    assert mu.reg_read(arm.UC_ARM_REG_PC) == 0x0800635e
    return bytes(mu.mem_read(0x20000000, 0x19800))


class Model(DrawingMachine):
    def __init__(self, raw, ram, gpio=False):
        super().__init__(raw)
        self.mu.mem_write(0x20000000, ram)
        self.gpio_mode = gpio
        self.external_reads = []
        self.notifications = []
        self.texts = []
        self.lowest_stack = STACK
        self.transactions = 0
        for address in (0x08008cf4, 0x08008d44, 0x0800d3d0, 0x0800beec,
                        0x0800b284, 0x08008e90):
            self.mu.hook_add(u.UC_HOOK_CODE, self.trace, begin=address, end=address)
        self.mu.hook_add(u.UC_HOOK_BLOCK, self.stack_depth)
        self.call(0x08008ab8, 1)
        self.mu.mem_write(0x200000d5, b"\0\0")  # Awake, no sleep request.
        self.mu.mem_write(0x20004265, bytes.fromhex("dc4d00"))  # Fixture accent RGB.

    def trace(self, mu, address, _size, _context):
        self.lowest_stack = min(self.lowest_stack, mu.reg_read(arm.UC_ARM_REG_SP))
        args = [mu.reg_read(r) for r in REGS]
        sp = mu.reg_read(arm.UC_ARM_REG_SP)
        if not self.gpio_mode and address in (0x08008cf4, 0x08008d44):
            self.lcd.write(address == 0x08008d44, args[0] & 255)
        elif address == 0x0800d3d0:
            destination, source, size = args[:3]
            assert size <= 2048
            # Deliberately visible texture: compare untouched regions and wrappers.
            data = bytes(255 if ((source + i) // 16) % 2 else 0 for i in range(size))
            mu.mem_write(destination, data)
            self.external_reads.append((source, size))
        elif address == 0x0800beec:
            rgb = args[1]
            color = (((rgb & 248) << 8) | ((rgb >> 5) & 2016) | ((rgb >> 19) & 31)) if args[0] else args[2]
            # Fixture at palette conversion only; original window/crop loops execute.
            self.lcd.write(True, color >> 8)
            self.lcd.write(True, color & 255)
        elif address == 0x0800b284:
            assert args[3] <= 64
            self.notifications.append((args[0], args[1], bytes(mu.mem_read(args[2], args[3])).hex()))
        elif address == 0x08008e90:
            pointer, height, count = struct.unpack("<III", mu.mem_read(sp, 12))
            assert count <= 32
            self.texts.append((args[0], args[1], height, bytes(mu.mem_read(pointer, count)).decode("ascii")))
            return  # Actual original glyph renderer executes.
        else:
            return
        mu.reg_write(arm.UC_ARM_REG_PC, mu.reg_read(arm.UC_ARM_REG_LR))

    def stack_depth(self, mu, _address, _size, _context):
        self.lowest_stack = min(self.lowest_stack, mu.reg_read(arm.UC_ARM_REG_SP))

    def call(self, address, *args):
        saved = [getattr(arm, f"UC_ARM_REG_R{i}") for i in range(4, 12)]
        values = [0xA1000010 + i for i in range(8)]
        for r, value in zip(saved, values):
            self.mu.reg_write(r, value)
        super().call(address, *args)
        assert [self.mu.reg_read(r) for r in saved] == values, "Callee-saved register changed"
        assert self.mu.reg_read(arm.UC_ARM_REG_SP) == STACK, "Unbalanced stack"

    def select(self, view, slot=0):
        self.mu.mem_write(0x200000f2, struct.pack("<HH", view, slot))
        self.mu.mem_write(0x200000d1, bytes([slot]))

    def exchange(self, payload):
        self.transactions += 1
        sequence = self.transactions % 255 + 1
        self.mu.mem_write(0x200046ac, encode(1, sequence, (0x21, 0), payload))
        self.mu.mem_write(0x20011718, b"\xa5" * 64)
        self.mu.mem_write(0x20000010, b"\1")
        self.mu.mem_write(0x2000019e, b"\0\0")
        self.call(0x0800d55c, 0x200046ac)  # Original fragment prefilter.
        assert self.mu.reg_read(arm.UC_ARM_REG_R0) == 0
        before = bytes(self.mu.mem_read(0x20000000, 0x19800))
        self.call(0x0800c038)  # Original dispatch, custom handler, original reply/CRC.
        after = bytes(self.mu.mem_read(0x20000000, 0x19800))
        allowed = [(0x10, 0x11), (0x19e, 0x1a0), (0x46ac, 0x46ec), (0x11718, 0x11798),
                   (STACK - 0x20000000 - 512, STACK - 0x20000000)]
        unexpected = [hex(0x20000000+i) for i, (a, b) in enumerate(zip(before, after))
                      if a != b and not any(lo <= i < hi for lo, hi in allowed)]
        assert not unexpected, f"Unexpected graphics SRAM write: {unexpected}"
        reply = decode(bytes(self.mu.mem_read(0x20011718, 64)))
        assert (reply.session, reply.sequence, reply.command) == (1, sequence, (0x21, 0))
        if reply.status:
            raise DeviceError(reply.command, reply.status)
        return reply.payload


def png(path, pixels):
    """Export exact modeled RGB565 pixels as an RGB PNG, without Qt/Pillow."""
    rows = bytearray()
    for y in range(240):
        rows.append(0)
        for x in range(320):
            value = int.from_bytes(pixels[(320*y+x)*2:(320*y+x)*2+2], "little")
            rows.extend(((value >> 11) * 255 // 31, ((value >> 5) & 63) * 255 // 63, (value & 31) * 255 // 31))
    def chunk(kind, data):
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data))
    path.write_bytes(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", 320, 240, 8, 2, 0, 0, 0)) + chunk(b"IDAT", zlib.compress(rows)) + chunk(b"IEND", b""))


def check(original, candidate, output):
    if not __debug__:
        raise RuntimeError("Firmware validation requires Python assertions; do not use -O")
    spec = json.loads((ROOT / "firmware/targets/1.29.0-dmr3.json").read_text())
    assert hashlib.sha256(original).hexdigest() == spec["components"]["dock"]["stock_sha256"]
    assert hashlib.sha256(candidate).hexdigest() == spec["components"]["dock"]["patched_sha256"]
    ram = initialized(original)
    assert initialized(candidate) == ram, "Runtime initialization changed"
    found_references = references(original, ram)
    assert handoff(original) == handoff(candidate)
    output.mkdir(parents=True, exist_ok=False)
    model = Model(candidate, ram)
    model.select(0, 0)
    model.call(0x08009714, 1)
    assert int.from_bytes(model.mu.mem_read(0x200000f2, 2), "little") == 1
    assert model.texts == [(40, 96, 48, "Waiting...")]
    assert not model.external_reads, "Dashboard entry still reads Clock submenu artwork"
    png(output / "waiting.png", model.lcd.pixels)
    print("Waiting screen: original click and glyph instructions passed", flush=True)
    waiting = bytes(model.lcd.pixels)
    client = Client(model.exchange)
    assert client.capabilities()["features"] == ("dock_directdraw", "dock_navigation", "dashboard_view")
    assert bytes(model.lcd.pixels) == waiting, "Capability query overwrote waiting view"
    expected = b"\xe0\x07" * (320 * 240)
    previous = client.frame(expected)
    assert bytes(model.lcd.pixels) == expected, "First frame left waiting pixels"
    pixels = bytes(range(42))
    client.pixels(299, 239, 21, 1, pixels)
    assert bytes(model.lcd.pixels[-42:]) == pixels
    sent = bytes(model.lcd.pixels)
    for address in (0x08009a60, 0x08009938, 0x0800a470):
        model.call(address, 0xffffffff, 1)
    model.call(0x08009714, 1)  # Single click cannot start the old clock tools.
    assert bytes(model.lcd.pixels) == sent
    print("DMR3 negotiation, first frame, edge pixels and old Clock no-ops passed", flush=True)
    # Full selector entry and repeated highlight transitions exercise both wrappers.
    baseline = Model(original, ram)
    baseline.select(1)
    model.call(0x08009714, 2)
    baseline.call(0x08009714, 2)
    def unchanged_other_tiles():
        for y in range(240):
            for x in range(320):
                if 10 <= x < 110 and 20 <= y < 110:
                    continue
                p = 2 * (y * 320 + x)
                assert model.lcd.pixels[p:p+2] == baseline.lcd.pixels[p:p+2]
    unchanged_other_tiles()
    selected_icon = bytes(model.lcd.pixels)
    for direction in (0,) * 6 + (1,) * 6:
        model.call(0x0800aec8, direction)
        baseline.call(0x0800aec8, direction)
        assert model.mu.mem_read(0x200000f2, 4) == baseline.mu.mem_read(0x200000f2, 4)
        unchanged_other_tiles()
    assert bytes(model.lcd.pixels) == selected_icon, "Icon did not survive selection round trip"
    print("Menu entry, exit and 12 highlight transitions preserve every other tile", flush=True)
    # Non-selector full images and arbitrary crops still use the original paths.
    for image_address in (0x4b000, 0x190000):
        model.call(0x0800b1cc, image_address, 0)
        baseline.call(0x0800b1cc, image_address, 0)
        assert model.lcd.pixels == baseline.lcd.pixels
    for args in [(110, 20, 100, 90, 0xffffff, 0x1082, 0),
                 (10, 20, 100, 90, 0x004ddc, 0, 0x4b000),
                 (70, 30, 40, 40, 0x004ddc, 0x1082, 0x4b000)]:
        model.call(0x08009690, *args)
        baseline.call(0x08009690, *args)
        assert model.lcd.pixels == baseline.lcd.pixels
    print("Shared full-image/crop paths match original output", flush=True)
    # Re-entry always shows the placeholder once; host must discard its old diff base.
    model.select(0)
    model.texts.clear()
    model.call(0x08009714, 1)
    assert bytes(model.lcd.pixels) == waiting and len(model.texts) == 1
    client.capabilities()
    previous = client.frame(expected)
    assert previous == expected and bytes(model.lcd.pixels) == expected
    for address, args in [(0x0800b1cc, (0x25800, 0)),
                          (0x08009690, (70, 30, 40, 40, 0xffffff, 0x1082, 0x25800)),
                          (0x080093f0, (1,))]:
        model.call(address, *args)
        assert bytes(model.lcd.pixels) == expected, "Old Clock assets resurfaced"
    # Caps outside Dashboard are valid; drawing is rejected without changing pixels.
    model.select(4)
    assert not client.capabilities()["selected"]
    try:
        model.exchange(b"DMR\x01\x01" + struct.pack("<5H", 0, 0, 1, 1, 0))
    except DeviceError as error:
        assert error.status == 10
    else:
        raise AssertionError("Inactive drawing accepted")
    assert bytes(model.lcd.pixels) == expected
    model.select(1)
    for scan, payload in [(2, "0301"), (4, "0300")]:
        model.notifications.clear()
        model.call(0x0800bb3c, 1, scan)
        assert model.notifications == [(128, 0, payload)]
        model.notifications.clear()
        model.call(0x0800bb3c, 0, scan)
        assert not model.notifications
    randomizer = random.Random(3)
    for _ in range(200):
        payload = b"DMR\x01" + randomizer.randbytes(randomizer.randrange(1, 52))
        before = bytes(model.lcd.pixels)
        try:
            model.exchange(payload)
        except DeviceError as error:
            assert error.status == 3
            assert bytes(model.lcd.pixels) == before
        else:
            raise AssertionError("Malformed drawing request accepted")
    print("Re-entry, inactive drawing, navigation and 200 malformed requests passed", flush=True)
    for background, name in [(0, "icon"), (0x1082, "icon-selected")]:
        model.lcd.pixels[:] = b"\0" * len(model.lcd.pixels)
        model.call(0x08009690, 10, 20, 100, 90, 0x004ddc, background, 0)
        png(output / (name + ".png"), model.lcd.pixels)
    # Independent slow path: no LCD byte-writer fixtures for icon or waiting screen.
    hardware_bus = Model(candidate, ram, gpio=True)
    hardware_bus.select(0)
    hardware_bus.call(0x08009714, 1)
    assert bytes(hardware_bus.lcd.pixels) == waiting
    hardware_bus.lcd.pixels[:] = b"\0" * len(hardware_bus.lcd.pixels)
    hardware_bus.call(0x08009690, 10, 20, 100, 90, 0x004ddc, 0x1082, 0)
    assert hardware_bus.lcd.pixels == model.lcd.pixels
    print("Original LCD GPIO instructions reproduce both previews exactly", flush=True)
    model.call(0x08006398)
    assert model.mu.reg_read(arm.UC_ARM_REG_R1) == STACK
    stack_base = model.mu.reg_read(arm.UC_ARM_REG_R3)
    lowest = min(model.lowest_stack, hardware_bus.lowest_stack)
    assert lowest >= stack_base, "Exceeded original declared stack"
    record = dict(hardware_io=False, hardware_verified=False, passed=True,
                  dock_sha256=hashlib.sha256(candidate).hexdigest(),
                  maximum_stack_bytes=STACK-lowest, declared_stack_bytes=STACK-stack_base,
                  graphics_transactions=model.transactions,
                  retained_entry_references=found_references,
                  initialized_ram_equal=True, application_reset_handoff_equal=True,
                  limitations=["Factory artwork replaced by synthetic texture; no factory asset readback",
                               "External storage and palette conversion are fixtures",
                               "No physical display, USB, interrupt scheduling or bootloader validation"])
    (output / "result.json").write_text(json.dumps(record, indent=2) + "\n")
    return record


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--original", type=Path, required=True)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    check(args.original.read_bytes(), args.candidate.read_bytes(), args.output)
