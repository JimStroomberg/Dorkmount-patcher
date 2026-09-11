# SPDX-License-Identifier: GPL-3.0-only
"""DMR1/DMR2 volatile pixel sender, extracted from the tested Dorkmount controller.

The exchange callable owns QLink session, sequence, CRC and device-status checks.
This module also runs against original firmware instructions in the offline model.
It is separate from the larger DMLB protocol and has no lease or atomic present.
"""

import struct
import time
from collections import Counter, deque
from contextlib import contextmanager

MAGIC = b"DMR\x01"
NAV_MAGIC = b"DMR\x02"
COMMAND = (0x21, 0)
WIDTH, HEIGHT = 320, 240
_FEATURES = {
    MAGIC: ("dock_directdraw",),
    NAV_MAGIC: ("dock_directdraw", "dock_navigation"),
}


class Client:
    def __init__(self, exchange):
        self.exchange = exchange
        self.transactions = 0
        self.latencies = deque(maxlen=10000)
        self.capabilities()

    def request(self, payload):
        if not isinstance(payload, bytes) or len(payload) > 55:
            raise ValueError("Invalid DMR1 payload")
        start = time.monotonic()
        response = self.exchange(payload)
        self.latencies.append(time.monotonic() - start)
        self.transactions += 1
        return response

    def capabilities(self):
        """Refresh the known DMR version and its features, independently of Clock.

        DMR1/DMR2 carry a version, not feature flags. Only explicitly supported
        contracts are mapped here; a higher number never implies compatibility.
        A failed refresh revokes cached drawing/navigation permission.
        """
        self.selected = self.navigation = False
        self.dmr_version = None
        self.features = ()
        response = self.request(MAGIC + b"\0")
        if not isinstance(response, bytes) or len(response) != 12:
            raise IOError("Missing or malformed DMR capability response")
        magic, width, height, pixels, selected, fill = struct.unpack("<4sHHBBH", response)
        if magic not in _FEATURES or (width, height, pixels, fill) != (320, 240, 21, 4096):
            raise IOError("Unsupported DMR capabilities")
        if selected not in (0, 1):
            raise IOError("Invalid DMR view state")
        self.dmr_version = magic[3]
        self.features = _FEATURES[magic]
        self.selected = bool(selected)
        self.navigation = "dock_navigation" in self.features
        self.max_pixels, self.max_fill = pixels, fill
        return dict(
            dmr_version=self.dmr_version,
            features=self.features,
            width=width,
            height=height,
            max_pixels=pixels,
            max_fill_pixels=fill,
            selected=self.selected,
            navigation=self.navigation,
        )

    @staticmethod
    def bounds(x, y, width, height):
        if any(type(v) is not int for v in (x, y, width, height)) or not (
            0 <= x < WIDTH
            and 0 <= y < HEIGHT
            and 0 < width <= WIDTH - x
            and 0 < height <= HEIGHT - y
        ):
            raise ValueError("Rectangle outside the 320x240 display")

    def draw(self, operation, x, y, width, height, data):
        self.bounds(x, y, width, height)
        if not self.selected:
            raise IOError("Verify DirectDraw support and select Clock on the Dock before drawing")
        payload = MAGIC + bytes((operation,)) + struct.pack("<4H", x, y, width, height) + data
        if self.request(payload) != b"":
            raise IOError("Unexpected DMR1 drawing acknowledgment")

    def fill(self, x, y, width, height, color):
        self.bounds(x, y, width, height)
        if type(color) is not int or not 0 <= color <= 65535:
            raise ValueError("RGB565 color must be a 16-bit integer")
        rows = self.max_fill // width
        for row in range(0, height, rows):
            self.draw(1, x, y + row, width, min(rows, height - row), struct.pack("<H", color))

    def pixels(self, x, y, width, height, pixels):
        self.bounds(x, y, width, height)
        if not isinstance(pixels, bytes) or len(pixels) != 2 * width * height:
            raise ValueError("Pixel bytes do not match rectangle")
        for column in range(0, width, self.max_pixels):
            w = min(self.max_pixels, width - column)
            rows = self.max_pixels // w
            for row in range(0, height, rows):
                h = min(rows, height - row)
                data = b"".join(
                    pixels[2 * ((row + r) * width + column) : 2 * ((row + r) * width + column + w)]
                    for r in range(h)
                )
                self.draw(2, x + column, y + row, w, h, data)

    def frame(self, pixels, previous=None):
        """Write changed row spans; a failed frame must not become `previous`.

        Flat spans use bounded fills. Everything else uses RGB565 blocks. No
        atomic frame swap or detection of a local view leave/re-enter is provided.
        """
        if not isinstance(pixels, bytes) or len(pixels) != WIDTH * HEIGHT * 2:
            raise ValueError("A full RGB565 frame is required")
        if previous is None:
            color = Counter(struct.iter_unpack("<H", pixels)).most_common(1)[0][0][0]
            self.fill(0, 0, WIDTH, HEIGHT, color)
            previous = struct.pack("<H", color) * WIDTH * HEIGHT
        elif not isinstance(previous, bytes) or len(previous) != len(pixels):
            raise ValueError("Invalid previous framebuffer")
        for y in range(HEIGHT):
            row = y * WIDTH * 2
            x = 0
            while x < WIDTH:
                i = row + x * 2
                if pixels[i : i + 2] == previous[i : i + 2]:
                    x += 1
                    continue
                run = x + 1
                while (
                    run < WIDTH and pixels[row + run * 2 : row + run * 2 + 2] == pixels[i : i + 2]
                ):
                    run += 1
                if run - x >= 4:
                    self.fill(x, y, run - x, 1, int.from_bytes(pixels[i : i + 2], "little"))
                    x = run
                else:
                    end = min(WIDTH, x + self.max_pixels)
                    self.pixels(x, y, end - x, 1, pixels[i : row + end * 2])
                    x = end
        return pixels


@contextmanager
def open_keyboard():
    """Linux reference connection. Only identity and volatile graphics are allowed."""
    from .device import ProcessLock, check_identity, connect, single_device

    device = single_device()
    lock = ProcessLock(device.port)
    link = None
    try:
        link = connect(device)
        check_identity(link)
        client = Client(lambda payload: link.request(COMMAND, payload))
        yield client
    finally:
        if link is not None:
            link.close()
        lock.close()
