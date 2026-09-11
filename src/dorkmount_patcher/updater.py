"""Desktop workflow. All device mutations start only in install(), after review."""

import json
import os
import secrets
import subprocess
import time
from contextlib import suppress
from datetime import datetime, timezone
from pathlib import Path

from . import __version__
from . import device as hardware
from .dfu import Transfer, sync
from .directdraw import Client
from .firmware import COMPONENTS, atomic_write, export, private_directory
from .qlink import DeviceError, ProtocolError
from .system import environment


def state_directory():
    return Path(os.environ.get("XDG_STATE_HOME", Path.home() / ".local/state")) / "dorkmount-patcher"


def probe():
    device = hardware.single_device()
    lock = hardware.ProcessLock(device.port)
    link = None
    try:
        link = hardware.connect(device)
        identity = hardware.check_identity(link)
        caps = None
        try:
            caps = Client(lambda payload: link.request((0x21, 0), payload)).capabilities()
        except DeviceError as error:
            # Stock rejects the extension command; other errors must remain visible.
            if error.status not in (2, 3):
                raise
        except TimeoutError:
            # Stock Main drops command zero without replying on the reviewed baseline.
            # Recheck normal traffic before treating absence as stock-compatible.
            hardware.check_identity(link)
        return device, {**identity, "directdraw": caps}
    finally:
        if link is not None:
            link.close()
        lock.close()


class Journal:
    def __init__(self, directory):
        self.path = directory / "session.json"
        self.data = {"app_version": __version__, "hardware_test": True, "events": [], "status": "prepared"}
        self.save()

    def save(self):
        atomic_write(self.path, (json.dumps(self.data, indent=2) + "\n").encode())

    def record(self, **fields):
        self.data["events"].append({"time": datetime.now(timezone.utc).isoformat(), **fields})
        self.save()


class SleepGuard:
    def __init__(self):
        self.process = None

    def start(self):
        # No shell, services or persistent settings. Inhibitor ends when stdin closes.
        self.process = subprocess.Popen([
            "systemd-inhibit", "--what=sleep:idle", "--mode=block",
            "--who=Dorkmount-patcher", "--why=Keyboard firmware update", "cat",
        ], stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
            env=environment())
        time.sleep(0.2)
        if self.process.poll() is not None:
            raise OSError("Could not keep the computer awake. Check desktop power settings before updating.")

    def close(self):
        if self.process is not None:
            with suppress(BrokenPipeError):
                self.process.stdin.close()
            try:
                self.process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                self.process.terminate()
                self.process.wait(timeout=3)


def install(package, expected_device, progress, root=None, backend=hardware, inhibit_factory=SleepGuard):
    """Install a verified in-memory package. Never called by probe, prepare or demo."""
    package.verify()
    current = backend.single_device()
    if current != expected_device:
        raise ProtocolError("The keyboard changed since it was checked. Check it again before installing.")
    lock = backend.ProcessLock(current.port)
    link, journal, transfer = None, None, None
    inhibitor = inhibit_factory()
    mutation_started = False
    run = None
    try:
        root = private_directory(root or state_directory())
        run = root / (datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S") + "-" + secrets.token_hex(3))
        export(package, run)  # Durable stock restoration copies exist before opening update commands.
        journal = Journal(run)
        journal.data.update(mode=package.mode, port=current.port)
        upgrade_id = secrets.randbelow(0x7FFFFFFE) + 1
        journal.data["upgrade_id"] = upgrade_id
        journal.save()
        inhibitor.start()
        link = backend.connect(current, update=True)
        backend.check_identity(link)
        package.verify()
        progress(0, "Restarting the keyboard for the update… Keep it connected.")
        journal.record(event="sync_sending")
        mutation_started = True
        # Normal application may disappear before its Sync ACK. Reconnect is the only
        # allowed next step; no retry is sent to the application.
        try:
            sync(link, upgrade_id)
        except (TimeoutError, OSError) as error:
            if isinstance(error, ProtocolError):
                raise
            journal.record(event="sync_connection_transition", error=type(error).__name__)
        link.close(polite=False)
        link = None
        boot = backend.wait_device(backend.UPDATER, current.port)
        link = backend.connect(boot, update=True)
        sync(link, upgrade_id)
        transfer = Transfer(link, [package.images[name] for name in COMPONENTS], progress, journal.record)
        transfer.run()
        link.close()
        link = None
        progress(96, "Waiting for your keyboard to reconnect…")
        normal = backend.wait_device(backend.NORMAL, current.port, timeout=60)
        link = backend.connect(normal)
        identity = backend.check_identity(link)
        if package.mode == "dmr2":
            caps = Client(lambda payload: link.request((0x21, 0), payload)).capabilities()
            if caps["dmr_version"] != 2:
                raise ProtocolError("The keyboard returned, but the expected DirectDraw extension was not found.")
            journal.data["capabilities"] = caps
        else:
            # Absence of DMR after a verified stock transfer is expected. Revalidate
            # normal identity after a dropped command so a transport fault cannot pass.
            try:
                Client(lambda payload: link.request((0x21, 0), payload))
            except DeviceError as error:
                if error.status not in (2, 3):
                    raise
            except TimeoutError:
                backend.check_identity(link)
            else:
                raise ProtocolError("DirectDraw is still present after the stock update.")
        journal.data.update(status="verified", identity=identity)
        journal.record(event="normal_mode_verified")
        progress(100, "DirectDraw is ready." if package.mode == "dmr2" else "Original firmware restored.")
        return run
    except BaseException as error:
        if journal is not None:
            journal.data.update(status="needs_attention" if mutation_started else "not_started",
                                phase=transfer.phase if transfer else "preparation",
                                error=str(error))
            journal.save()
        if mutation_started:
            raise ProtocolError(
                f"The update could not be verified. Keep the keyboard connected and do not retry blindly. "
                f"Local recovery files: {run}. Details: {error}"
            ) from error
        raise
    finally:
        try:
            if link is not None:
                with suppress(OSError):
                    link.close(polite=not mutation_started)
        finally:
            try:
                with suppress(OSError, subprocess.SubprocessError):
                    inhibitor.close()
            finally:
                lock.close()
