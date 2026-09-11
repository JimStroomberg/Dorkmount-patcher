"""Device-requested update state machine for the exact three-controller target.

Protocol facts are documented in docs/UPDATER-PROTOCOL.md. No automatic retry,
resume, Abort, controller omission or unchecked offset is supported in this preview.
"""

import struct
import time

from .qlink import ProtocolError, crc16

SELECTION = b"\x03\x00\x01\x02"


def sync(link, upgrade_id):
    response = link.request((2, 1), struct.pack("<I", upgrade_id) + SELECTION, timeout=10)
    if len(response) != 8 or response[:4] != struct.pack("<I", upgrade_id):
        raise ProtocolError("Unexpected update synchronization reply.")
    if response[4:] != b"\x03\0\0\0":
        raise ProtocolError("The keyboard reports an existing or unsupported update state. No data sent.")


class Transfer:
    def __init__(self, link, images, progress=lambda value, text: None, record=lambda **kw: None,
                 pause=time.sleep):
        self.link, self.images, self.progress, self.record = link, tuple(images), progress, record
        self.pause = pause
        self.offsets = [0, 0, 0]
        self.validated = [False, False, False]
        self.total = sum(map(len, images))
        self.resume = [0, 0, 0]
        self.phase = "transfer"
        self.last_percent = -1

    def event(self, wanted, mcu=None, timeout=45):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            frame = self.link.notification(2, max(0, deadline - time.monotonic()))
            command, data = frame.command[1], frame.payload
            if command == 8:
                if len(data) != 2 or data[0] > 2 or data[1] > 4:
                    raise ProtocolError("Invalid update-state notification.")
                self.resume[data[0]] = data[1]
                self.record(event="resume", mcu=data[0], state=data[1])
                continue
            if command != wanted or (mcu is not None and (not data or data[0] != mcu)):
                raise ProtocolError(f"Unexpected update notification {command} while waiting for {wanted}.")
            if command in (3, 4) and len(data) != 1:
                raise ProtocolError("Malformed controller completion notification.")
            if command in (5, 6) and data:
                raise ProtocolError("Malformed update completion notification.")
            return data
        raise TimeoutError("Keyboard update progress stopped. No command was retried.")

    def run(self):
        for mcu, image in enumerate(self.images):
            self.record(event="transfer_start", mcu=mcu, size=len(image), crc16=crc16(image))
            self.link.request((2, 2), struct.pack("<BHI", mcu, crc16(image), len(image)))
            while self.offsets[mcu] < len(image):
                data = self.event(2, mcu)
                if len(data) != 11:
                    raise ProtocolError("Malformed firmware data request.")
                requested_mcu, block, offset, length = struct.unpack("<BHII", data)
                if (requested_mcu != mcu or not 1 <= block <= 32 or length <= 0
                        or offset != self.offsets[mcu] or length > len(image) - offset):
                    raise ProtocolError("The keyboard requested an unexpected firmware range. Transfer stopped.")
                self.record(event="data_request", mcu=mcu, block=block, offset=offset, length=length)
                end = offset + length
                while self.offsets[mcu] < end:
                    start = self.offsets[mcu]
                    chunk = image[start:min(start + block, end)]
                    # The receiver owns the offset. A missing ACK must never cause a blind resend.
                    self.link.request((2, 3), bytes((mcu,)) + chunk)
                    self.offsets[mcu] += len(chunk)
                    percent = sum(self.offsets) * 85 // self.total
                    if percent != self.last_percent:
                        self.progress(percent,
                                      f"Installing part {mcu + 1} of 3… Keep the keyboard connected.")
                        self.last_percent = percent
                    self.pause(0.004)
            self.event(3, mcu)
            self.link.request((2, 4), bytes((mcu,)), timeout=10)
            self.event(4, mcu)
            self.validated[mcu] = True
            self.record(event="validated", mcu=mcu)
        if not all(self.validated):
            raise ProtocolError("Not all firmware parts were validated.")
        self.phase = "ready"
        self.progress(88, "Checking the installation…")
        self.link.request((2, 5), timeout=15)
        self.event(5, timeout=30)
        self.record(event="ready")
        self.phase = "commit"
        self.progress(92, "Finishing the update… Keep the keyboard connected.")
        # The research keyboard took over seven seconds to acknowledge Commit.
        # A lost ACK/completion is an uncertain update, never a reason to resend.
        self.record(event="commit_sending")
        self.link.request((2, 6), timeout=30)
        self.event(6, timeout=30)
        self.record(event="commit_complete")
        self.phase = "complete"
