# SPDX-License-Identifier: GPL-3.0-only
"""Strict single-report QLink, based on re133/iocenter-linux's transport.

See THIRD_PARTY.md. No automatic write retries, implicit device selection or
firmware operations. The injected I/O object reads/writes complete 64-byte frames.
"""

import secrets
import struct
import time
from collections import deque
from dataclasses import dataclass


def crc16(data):
    value = 0xFFFF
    for byte in data:
        value ^= byte
        for _ in range(8):
            value = (value >> 1) ^ (0xA001 if value & 1 else 0)
    return value


def encode(session, sequence, command, payload=b"", status=0):
    if not isinstance(payload, bytes) or len(payload) > 55:
        raise ValueError("QLink payload must be at most 55 bytes.")
    raw = bytearray(64)
    raw[:7] = bytes((6 + len(payload), 0, session, status, sequence, *command))
    raw[7:7 + len(payload)] = payload
    struct.pack_into("<H", raw, 62, crc16(raw[:62]))
    return bytes(raw)


class ProtocolError(IOError):
    pass


class DeviceError(ProtocolError):
    def __init__(self, command, status):
        self.command, self.status = command, status
        super().__init__(f"Keyboard rejected {command[0]:02x}/{command[1]:02x} (status {status}).")


@dataclass(frozen=True)
class Frame:
    session: int
    sequence: int
    command: tuple
    status: int
    payload: bytes


def decode(raw):
    if len(raw) != 64 or raw[1] or not 6 <= raw[0] <= 61:
        raise ProtocolError("Unexpected QLink frame length or fragmentation.")
    if crc16(raw[:62]) != int.from_bytes(raw[62:], "little"):
        raise ProtocolError("QLink checksum mismatch.")
    return Frame(raw[2], raw[4], tuple(raw[5:7]), raw[3], raw[7:raw[0] + 1])


class Link:
    def __init__(self, io, allowed=(), timeout=3.0):
        self.io, self.allowed, self.timeout = io, frozenset(allowed), timeout
        self.session, self.sequence = 0, 0x30
        self.pending = deque()

    def open(self, nonce=None):
        nonce = nonce or struct.pack("<I", secrets.randbelow(90000) + 10000)
        reply = self._request((1, 1), nonce + b"\x02")
        if len(reply) != 7 or reply[:4] != nonce or not reply[4] or reply[5] != 1:
            raise ProtocolError("Keyboard control is unavailable. Close other keyboard apps and retry.")
        self.session = reply[4]
        return self

    def request(self, command, payload=b"", timeout=None):
        if tuple(command) not in self.allowed:
            raise ValueError("Command is outside this connection's allowed operations.")
        return self._request(tuple(command), payload, timeout)

    def _read(self, deadline):
        raw = self.io.read(max(0, deadline - time.monotonic()))
        if raw is None:
            raise TimeoutError("The keyboard did not reply in time.")
        return decode(raw)

    def _queue(self, frame):
        if frame.command[0] not in (1, 2, 0x11):
            return
        if len(self.pending) >= 64:
            raise ProtocolError("Too many pending keyboard notifications.")
        self.pending.append(frame)

    def _check(self, frame):
        if frame.status:
            raise DeviceError(frame.command, frame.status)
        if frame.command == (2, 1) and frame.sequence == 0:
            raise ProtocolError("Keyboard update error: " + frame.payload.hex())
        if frame.command == (1, 1) and frame.sequence == 0 and frame.payload[:1] == b"\0":
            raise ProtocolError("Another application took keyboard control.")

    def _request(self, command, payload, timeout=None):
        self.sequence = self.sequence % 255 + 1
        self.io.write(encode(self.session, self.sequence, command, payload))
        deadline = time.monotonic() + (self.timeout if timeout is None else timeout)
        while time.monotonic() < deadline:
            frame = self._read(deadline)
            if frame.session != self.session and command != (1, 1):
                continue
            self._check(frame)
            if frame.command == command and frame.sequence == self.sequence:
                return frame.payload
            if frame.sequence == 0:
                self._queue(frame)
        raise TimeoutError("The keyboard did not acknowledge the command. It was not retried.")

    def notification(self, feature, timeout=30):
        deadline = time.monotonic() + timeout
        while True:
            for frame in tuple(self.pending):
                if frame.command[0] == feature:
                    self.pending.remove(frame)
                    self._check(frame)
                    return frame
            frame = self._read(deadline)
            if frame.session != self.session or frame.sequence != 0:
                continue
            self._check(frame)
            if frame.command[0] == feature:
                return frame
            # Unrelated ordinary key events are discarded, never logged.
            if time.monotonic() >= deadline:
                raise TimeoutError("Expected keyboard notification did not arrive.")

    def close(self, polite=True):
        try:
            if polite and self.session:
                try:
                    self._request((1, 2), b"", timeout=1)
                except OSError:
                    pass
        finally:
            self.session = 0
            self.io.close()
