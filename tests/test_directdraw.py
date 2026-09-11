import struct

import pytest

from dorkmount_patcher.directdraw import Client


class Screen:
    def __init__(self, version=2, selected=1):
        self.version, self.selected = version, selected
        self.pixels = bytearray(320 * 240 * 2)
        self.writes = 0

    def __call__(self, request):
        assert len(request) <= 55 and request[:4] == b"DMR\x01"
        opcode = request[4]
        if opcode == 0:
            return struct.pack("<4sHHBBH", b"DMR" + bytes((self.version,)), 320, 240, 21, self.selected, 4096)
        self.writes += 1
        x, y, width, height = struct.unpack_from("<4H", request, 5)
        raw = request[13:]
        if opcode == 1:
            assert width * height <= 4096
            raw *= width * height
        else:
            assert opcode == 2 and width * height <= 21
        assert len(raw) == 2 * width * height
        for row in range(height):
            start = ((y + row) * 320 + x) * 2
            self.pixels[start:start + width * 2] = raw[row * width * 2:(row + 1) * width * 2]
        return b""


@pytest.mark.parametrize("version", [1, 2])
def test_complete_high_variance_frame_and_partial_frame_reconstruct_exactly(version):
    screen = Screen(version)
    client = Client(screen)
    expected = bytes(range(256)) * 600
    previous = client.frame(expected)
    assert screen.pixels == expected
    count = screen.writes
    client.frame(expected, previous)
    assert screen.writes == count
    changed = b"\xff\xff" + expected[2:]
    client.frame(changed, previous)
    assert screen.pixels == changed


def test_inactive_view_refuses_draws():
    screen = Screen(selected=0)
    client = Client(screen)
    with pytest.raises(IOError):
        client.fill(0, 0, 320, 240, 0)
    assert screen.writes == 0


@pytest.mark.parametrize("version", [0, 3, 255])
def test_unknown_capabilities_refused(version):
    with pytest.raises(IOError):
        Client(Screen(version))


def test_failed_frame_cannot_become_a_returned_diff_base():
    screen = Screen()
    def exchange(payload):
        if screen.writes >= 2:
            raise TimeoutError("lost reply")
        return screen(payload)
    client = Client(exchange)
    with pytest.raises(TimeoutError):
        client.frame(bytes(range(256)) * 600)


def test_documented_payload_examples_are_exact():
    captured = []
    screen = Screen()
    def exchange(data):
        captured.append(data)
        return screen(data)
    client = Client(exchange)
    assert captured.pop() == bytes.fromhex("44 4d 52 01 00")
    client.fill(0, 0, 10, 10, 0xF800)
    assert captured.pop() == bytes.fromhex("44 4d 52 01 01 00 00 00 00 0a 00 0a 00 00 f8")
    client.pixels(0, 0, 3, 1, bytes.fromhex("00 f8 e0 07 1f 00"))
    assert captured.pop() == bytes.fromhex("44 4d 52 01 02 00 00 00 00 03 00 01 00 00 f8 e0 07 1f 00")
