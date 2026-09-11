import struct
from collections import deque

import pytest

from dorkmount_patcher.dfu import Transfer, sync
from dorkmount_patcher.qlink import DeviceError, Link, ProtocolError, crc16, decode, encode


class KeyboardModel:
    """Synthetic receiver: validates reconstructed bytes independently of the sender."""

    def __init__(self, images, fault=None, early=False):
        self.images, self.fault, self.early = images, fault, early
        self.replies = deque()
        self.received = [bytearray(), bytearray(), bytearray()]
        self.validated = []
        self.commands = []
        self.session = 7
        self.request_end = 0
        self.current = -1
        self.committed = False

    def write(self, raw):
        frame = decode(raw)
        self.commands.append(frame.command)
        command, payload = frame.command, frame.payload
        ack = b""
        events = []
        if command == (1, 1):
            ack = payload[:4] + bytes((self.session, 1, 20))
        elif command == (2, 1):
            assert payload[4:] == b"\x03\x00\x01\x02"
            ack = payload[:4] + b"\x03\0\0\0"
            if self.fault == "resume":
                ack = payload[:4] + b"\x03\x01\0\0"
        elif command == (2, 2):
            mcu, checksum, length = struct.unpack("<BHI", payload)
            assert mcu == self.current + 1
            assert self.validated == list(range(mcu))
            assert length == len(self.images[mcu]) and checksum == crc16(self.images[mcu])
            self.current = mcu
            events = self.request(mcu)
        elif command == (2, 3):
            mcu, chunk = payload[0], payload[1:]
            start = len(self.received[mcu])
            assert mcu == self.current and 1 <= len(chunk) <= 32
            assert start + len(chunk) <= self.request_end
            assert chunk == self.images[mcu][start:start + len(chunk)]
            self.received[mcu].extend(chunk)
            if self.fault == "lost_ack":
                return
            if len(self.received[mcu]) == len(self.images[mcu]):
                events = [(3, bytes((mcu,)))]
            elif len(self.received[mcu]) == self.request_end:
                events = self.request(mcu)
        elif command == (2, 4):
            mcu = payload[0]
            assert self.received[mcu] == self.images[mcu]
            if self.fault == "validation":
                self.replies.append(encode(self.session, 0, (2, 1), b"\x05"))
            else:
                self.validated.append(mcu)
                events = [(8, bytes((mcu, 2))), (4, bytes((mcu,)))]
        elif command == (2, 5):
            assert self.validated == [0, 1, 2]
            events = [(5, b"")]
        elif command == (2, 6):
            assert self.validated == [0, 1, 2]
            self.committed = True
            if self.fault == "commit_ack":
                return
            events = [] if self.fault == "commit_complete" else [(6, b"")]
        frames = [encode(self.session, 0, (2, cmd), data) for cmd, data in events]
        response = encode(self.session, frame.sequence, command, ack)
        if self.early:
            self.replies.extend(frames + [response])
        else:
            self.replies.extend([response] + frames)

    def request(self, mcu):
        offset = len(self.received[mcu])
        length = min(73, len(self.images[mcu]) - offset)
        self.request_end = offset + length
        block = 32
        requested_mcu = mcu
        if self.fault == "offset":
            offset += 1
        if self.fault == "oversize":
            length = len(self.images[mcu]) + 1
        if self.fault == "block":
            block = 33
        if self.fault == "wrong_mcu":
            requested_mcu = (mcu + 1) % 3
        if self.fault == "zero":
            length = 0
        return [(2, struct.pack("<BHII", requested_mcu, block, offset, length))]

    def read(self, timeout):
        return self.replies.popleft() if self.replies else None

    def close(self):
        pass


def make(fault=None, early=False):
    images = (bytes(range(251)), b"screen" * 47, b"numberpad" * 39)
    io = KeyboardModel(images, fault, early)
    link = Link(io, {(2, n) for n in range(1, 7)}).open()
    return io, link, Transfer(link, images, pause=lambda _: None)


def test_crc_known_standard_vector():
    assert crc16(b"123456789") == 0x4B37


def test_complete_production_sized_transfers_include_32_bit_offsets():
    images = tuple((bytes(range(256)) * ((size + 255) // 256))[:size]
                   for size in (85508, 81000, 325200))
    model = KeyboardModel(images, early=True)
    link = Link(model, {(2, n) for n in range(1, 7)}).open()
    sync(link, 0x10203040)
    transfer = Transfer(link, images, pause=lambda _: None)
    transfer.run()
    assert tuple(map(bytes, model.received)) == images
    assert transfer.offsets == [85508, 81000, 325200]
    assert model.committed


@pytest.mark.parametrize("early", [False, True])
def test_complete_update_reconstructs_every_byte_with_awkward_requested_ranges(early):
    model, link, transfer = make(early=early)
    sync(link, 5649)
    transfer.run()
    assert tuple(map(bytes, model.received)) == model.images
    assert model.committed and model.validated == [0, 1, 2]
    assert transfer.phase == "complete"


@pytest.mark.parametrize("fault", ["offset", "oversize", "block", "wrong_mcu", "zero"])
def test_unexpected_device_ranges_refused_before_any_data(fault):
    model, _, transfer = make(fault)
    with pytest.raises(ProtocolError):
        transfer.run()
    assert all(not raw for raw in model.received)
    assert (2, 5) not in model.commands and not model.committed


def test_lost_write_ack_is_not_retried_and_never_validated():
    model, _, transfer = make("lost_ack")
    with pytest.raises(TimeoutError):
        transfer.run()
    assert model.commands.count((2, 3)) == 1
    assert (2, 4) not in model.commands and not model.committed


@pytest.mark.parametrize("fault", ["validation", "commit_ack", "commit_complete"])
def test_validation_and_commit_failures_cannot_report_success(fault):
    model, _, transfer = make(fault)
    with pytest.raises(OSError):
        transfer.run()
    assert transfer.phase != "complete"
    assert model.commands.count((2, 6)) <= 1
    if fault == "validation":
        assert (2, 5) not in model.commands


def test_existing_resume_state_refused():
    model, link, _ = make("resume")
    with pytest.raises(ProtocolError, match="existing"):
        sync(link, 44)
    assert (2, 2) not in model.commands


@pytest.mark.parametrize("index", [0, 1, 8, 62, 63])
def test_corrupted_frames_rejected(index):
    frame = bytearray(encode(7, 3, (2, 2), b"test"))
    frame[index] ^= 1
    with pytest.raises(ProtocolError):
        decode(bytes(frame))


def test_link_rejects_disallowed_firmware_commands_without_write():
    model, _, _ = make()
    link = Link(model, {(3, 1)})
    count = len(model.commands)
    with pytest.raises(ValueError):
        link.request((2, 1), b"anything")
    assert len(model.commands) == count


def test_error_notification_before_ack_is_fatal():
    model, link, _ = make()
    model.replies.append(encode(7, 0, (2, 1), b"\x05"))
    with pytest.raises(ProtocolError, match="update error"):
        sync(link, 44)


def test_foreign_session_ack_cannot_satisfy_request():
    class WrongSession(KeyboardModel):
        def write(self, raw):
            frame = decode(raw)
            self.replies.append(encode(99, frame.sequence, frame.command))
    io = WrongSession(())
    link = Link(io, {(2, 4)})
    link.session = 7
    with pytest.raises(TimeoutError):
        link.request((2, 4), b"\0")


def test_status_error_never_looks_like_success():
    model, link, _ = make()
    model.replies.append(encode(7, link.sequence % 255 + 1, (2, 1), status=3))
    with pytest.raises(DeviceError):
        sync(link, 44)
