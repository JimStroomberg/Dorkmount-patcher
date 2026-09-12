# SPDX-License-Identifier: GPL-3.0-only
"""Offline LCD model reused from the project's original-instruction research.

No USB transport. Flash is read/execute and flash controllers are unmapped.
GPIO mode executes the original LCD byte writers. Fast mode intercepts those
writers; external image reads and palette conversion use explicit fixtures.
"""
import struct

import unicorn as u
from unicorn import arm_const as arm

STOP, STACK = 0x08000100, 0x20015070

class Lcd:
    """Logical address-space model; MADCTL is retained, not physically simulated."""

    def __init__(self):
        self.pixels = bytearray(320 * 240 * 2)
        self.command = None
        self.parameters = bytearray()
        self.columns, self.rows = (0, 319), (0, 239)
        self.cursor = 0
        self.high = None
        self.madctl = None
        self.pixel_count = 0
        self.windows = []
        self.command_count = 0

    def write(self, data, value):
        if not data:
            if self.high is not None:
                raise ValueError("LCD command interrupted half a pixel")
            if value not in (0x2A, 0x2B, 0x2C, 0x36):
                raise ValueError(f"Unmodeled LCD command {value:02x}")
            self.command = value
            self.parameters.clear()
            self.command_count += 1
            if value == 0x2C:
                self.cursor = 0
                self.windows.append([*self.columns, *self.rows])
            return
        if self.command == 0x2C:
            if self.high is None:
                self.high = value
                return
            width = self.columns[1] - self.columns[0] + 1
            height = self.rows[1] - self.rows[0] + 1
            if self.cursor >= width * height:
                raise ValueError("Pixel stream exceeds selected window")
            x = self.columns[0] + self.cursor % width
            y = self.rows[0] + self.cursor // width
            offset = (y * 320 + x) * 2
            self.pixels[offset : offset + 2] = bytes((value, self.high))
            self.high = None
            self.cursor += 1
            self.pixel_count += 1
        elif self.command in (0x2A, 0x2B):
            self.parameters.append(value)
            if len(self.parameters) > 4:
                raise ValueError("Too many window bytes")
            if len(self.parameters) == 4:
                bounds = struct.unpack(">HH", self.parameters)
                limit = 320 if self.command == 0x2A else 240
                if not 0 <= bounds[0] <= bounds[1] < limit:
                    raise ValueError("LCD window outside modeled screen")
                if self.command == 0x2A:
                    self.columns = bounds
                else:
                    self.rows = bounds
        elif self.command == 0x36:
            self.madctl = value
        else:
            raise ValueError("Data without a modeled command")


class DrawingMachine:
    def __init__(self, source):
        self.source = source
        raw = self.source
        self.mu = u.Uc(u.UC_ARCH_ARM, u.UC_MODE_THUMB | u.UC_MODE_MCLASS)
        self.mu.mem_map(0x08000000, 0x40000)
        self.mu.mem_write(0x08006000, raw)
        self.mu.mem_protect(0x08000000, 0x40000, u.UC_PROT_READ | u.UC_PROT_EXEC)
        self.mu.mem_map(0x20000000, 0x1A000)
        self.mu.mem_map(0x40020000, 0x1000)
        self.mu.reg_write(arm.UC_ARM_REG_CPSR, 0x20)
        self.output = {0x40020000: 0xFFFF, 0x40020400: 0xFFFF, 0x40020800: 0}
        for base, value in self.output.items():
            self.mu.mem_write(base + 0x14, struct.pack("<I", value))
        self.lcd = Lcd()
        self.bus_bytes = 0
        self.calls = []
        self.mu.hook_add(
            u.UC_HOOK_MEM_WRITE, self.gpio, begin=0x40020000, end=0x40020FFF
        )

    def gpio(self, mu, _access, address, size, value, _context):
        base = address & ~0x3FF
        register = address - base
        if base not in self.output or register not in (0x14, 0x18, 0x28) or size != 4:
            raise ValueError(f"Unexpected GPIO write {address:08x}/{size}")
        previous = self.output[base]
        if register == 0x14:
            current = value & 0xFFFF
        elif register == 0x18:
            current = ((previous | (value & 0xFFFF)) & ~(value >> 16)) & 0xFFFF
        else:
            current = previous & ~value
        self.output[base] = current
        mu.mem_write(base + 0x14, struct.pack("<I", current))
        # Original code pulses PB2 low/high. PA9=CS, PA10=data/command,
        # PB3=read strobe (inactive high), PC0..7=parallel data.
        if base == 0x40020400 and not previous & 4 and current & 4:
            if self.output[0x40020000] & 0x200 or not current & 8:
                raise ValueError("Write strobe with inactive CS or active read")
            self.lcd.write(
                bool(self.output[0x40020000] & 0x400), self.output[0x40020800] & 255
            )
            self.bus_bytes += 1

    def call(self, address, *args):
        mu = self.mu
        mu.reg_write(arm.UC_ARM_REG_SP, STACK)
        mu.reg_write(arm.UC_ARM_REG_LR, STOP | 1)
        for register, value in zip(
            (
                arm.UC_ARM_REG_R0,
                arm.UC_ARM_REG_R1,
                arm.UC_ARM_REG_R2,
                arm.UC_ARM_REG_R3,
            ),
            args,
        ):
            mu.reg_write(register, value)
        for index, value in enumerate(args[4:]):
            mu.mem_write(STACK + index * 4, struct.pack("<I", value))
        before = self.lcd.pixel_count
        mu.emu_start(address | 1, STOP, timeout=30_000_000, count=80_000_000)
        if mu.reg_read(arm.UC_ARM_REG_PC) != STOP:
            raise RuntimeError(
                f"Drawing did not return: PC={mu.reg_read(arm.UC_ARM_REG_PC):08x}"
            )
        if self.lcd.high is not None:
            raise ValueError("Incomplete final pixel")
        self.calls.append(
            dict(
                address=f"{address:08x}",
                arguments=list(args),
                pixels=self.lcd.pixel_count - before,
            )
        )
