"""Linux vendor-interface discovery and process locks. No device serial query."""

import fcntl
import os
import select
import stat
import struct
import sys
import time
from dataclasses import dataclass
from pathlib import Path

from .firmware import private_directory
from .qlink import Link, ProtocolError

NORMAL, UPDATER = 1, 9
READ_COMMANDS = {(3, 1), (0x21, 0)}
UPDATE_COMMANDS = {(2, n) for n in range(1, 7)}


@dataclass(frozen=True)
class Device:
    path: str
    port: str
    hid_identity: str
    product: int


def discover(sysfs=Path("/sys/class/hidraw"), dev=Path("/dev")):
    result = []
    for node in sorted(sysfs.glob("hidraw*")):
        try:
            hid = (node / "device").resolve()
            if not (hid / "report_descriptor").read_bytes().startswith(bytes.fromhex("0600ff0901a101")):
                continue
            interface = next(p for p in hid.parents if (p / "bInterfaceNumber").exists())
            usb = next(p for p in interface.parents if (p / "idVendor").exists())
            vid = int((usb / "idVendor").read_text().strip(), 16)
            pid = int((usb / "idProduct").read_text().strip(), 16)
            if vid != 0x373F or pid not in (NORMAL, UPDATER):
                continue
            if (interface / "bInterfaceNumber").read_text().strip() != "02":
                continue
            result.append(Device(str(dev / node.name), usb.name, hid.name, pid))
        except (OSError, StopIteration, ValueError):
            continue
    return result


def single_device(product=NORMAL, port=None):
    nodes = discover()
    if len(nodes) > 1:
        raise ProtocolError("Connect only one Dark Mount keyboard, then try again.")
    if not nodes:
        raise FileNotFoundError("Connect your Dark Mount with its screen and number pad attached.")
    node = nodes[0]
    if port is not None and node.port != port:
        raise ProtocolError("The keyboard returned on a different USB port. Update stopped.")
    if node.product != product:
        raise FileNotFoundError("Waiting for the keyboard to reconnect…")
    return node


class ProcessLock:
    def __init__(self, name, namespace="dorkmount-patcher"):
        runtime = Path(os.environ.get("XDG_RUNTIME_DIR", f"/run/user/{os.getuid()}"))
        if not runtime.is_dir():
            runtime = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache"))
        root = private_directory(runtime / namespace)
        self.stream = (root / (name + ".lock")).open("a")
        try:
            fcntl.flock(self.stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BaseException:
            self.stream.close()
            raise ProtocolError("Another keyboard app is running. Close it and try again.") from None

    def close(self):
        self.stream.close()


class HidIO:
    def __init__(self, device):
        self.lock = ProcessLock(device.hid_identity, "dorkmount")
        self.fd = None
        try:
            # Re-resolve identity immediately before opening; never select an arbitrary hidraw node.
            if device not in discover():
                raise ProtocolError("The keyboard connection changed. Please check it again.")
            self.fd = os.open(device.path, os.O_RDWR | os.O_NONBLOCK | os.O_NOFOLLOW)
            if not stat.S_ISCHR(os.fstat(self.fd).st_mode):
                raise ProtocolError("Expected a keyboard device.")
        except BaseException:
            self.close()
            raise

    def write(self, frame):
        if len(frame) != 64 or os.write(self.fd, b"\0" + frame) != 65:
            raise IOError("The keyboard report was not fully written.")

    def read(self, timeout):
        if not select.select([self.fd], [], [], timeout)[0]:
            return None
        return os.read(self.fd, 64)

    def close(self):
        if self.fd is not None:
            os.close(self.fd)
            self.fd = None
        self.lock.close()


def connect(device, update=False):
    if sys.platform != "linux":
        raise OSError("Keyboard access in this preview is available on Linux.")
    link = Link(HidIO(device), READ_COMMANDS | (UPDATE_COMMANDS if update else set()))
    try:
        return link.open()
    except BaseException:
        link.close(polite=False)
        raise


def check_identity(link):
    raw = link.request((3, 1))
    if len(raw) != 16 or struct.unpack_from("<HBB", raw) != (1, 1, 3):
        raise ProtocolError("This keyboard model or hardware revision is not supported.")
    if raw[4:] != bytes.fromhex("00002901") * 3:
        raise ProtocolError("This preview needs official firmware 1.29.0 on all three parts.")
    return {"model": 1, "revision": 1, "versions": ["1.29.0"] * 3}


def wait_device(product, port, timeout=45):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            return single_device(product, port)
        except FileNotFoundError:
            time.sleep(0.2)
    raise TimeoutError("The keyboard did not reconnect. Keep it connected and open the help details.")
