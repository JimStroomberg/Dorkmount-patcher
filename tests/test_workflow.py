import json
from types import SimpleNamespace

import pytest
from test_protocol import KeyboardModel

from dorkmount_patcher import firmware, updater
from dorkmount_patcher.device import Device, check_identity, discover
from dorkmount_patcher.qlink import Link, ProtocolError
from dorkmount_patcher.system import environment


class NoSleepGuard:
    def start(self):
        pass
    def close(self):
        pass


def backend_for(images, bad_return=False):
    normal = Device("/dev/synthetic", "1-2", "synthetic", 1)
    boot = Device("/dev/synthetic-update", "1-2", "synthetic-update", 9)
    models = []
    state = {"opened": 0}

    class Lock:
        def __init__(self, name):
            pass
        def close(self):
            pass

    def connect(device, update=False):
        state["opened"] += 1
        if state["opened"] < 3:
            model = KeyboardModel(images)
            models.append(model)
            return Link(model, {(2, n) for n in range(1, 7)}).open()
        class Final:
            def request(self, command, payload=b""):
                assert command == (0x21, 0)
                return bytes.fromhex("444d52024001f00015000010") if not bad_return else b"wrong"
            def close(self, **kwargs):
                pass
        return Final()

    return normal, models, SimpleNamespace(
        single_device=lambda: normal, ProcessLock=Lock, connect=connect,
        check_identity=lambda link: {"model": 1, "revision": 1}, NORMAL=1, UPDATER=9,
        wait_device=lambda product, port, **kw: normal if product == 1 else boot,
    )


def test_complete_workflow_saves_stock_before_transfer_and_verifies_return(synthetic, tmp_path, monkeypatch):
    stock, output, _ = synthetic
    normal, models, backend = backend_for(tuple(output.values()))
    monkeypatch.setattr(updater.Transfer, "__init__", _fast_transfer_init)
    run = updater.install(firmware.prepare(stock), normal, lambda *_: None,
                          root=tmp_path, backend=backend, inhibit_factory=NoSleepGuard)
    result = json.loads((run / "session.json").read_text())
    assert result["status"] == "verified"
    assert result["capabilities"]["dmr_version"] == 2
    assert result["capabilities"]["features"] == ["dock_directdraw", "dock_navigation"]
    assert models[-1].committed
    assert all((run / f"{name}-stock.bin").read_bytes() == raw for name, raw in stock.items())


_original_transfer_init = updater.Transfer.__init__


def _fast_transfer_init(self, *args, **kwargs):
    _original_transfer_init(self, *args, **kwargs, pause=lambda _: None)


def test_wrong_post_update_capabilities_never_claim_success(synthetic, tmp_path, monkeypatch):
    stock, output, _ = synthetic
    normal, _, backend = backend_for(tuple(output.values()), bad_return=True)
    monkeypatch.setattr(updater.Transfer, "__init__", _fast_transfer_init)
    with pytest.raises(ProtocolError, match="could not be verified"):
        updater.install(firmware.prepare(stock), normal, lambda *_: None,
                        root=tmp_path, backend=backend, inhibit_factory=NoSleepGuard)
    journals = list(tmp_path.glob("*/session.json"))
    assert len(journals) == 1
    assert json.loads(journals[0].read_text())["status"] == "needs_attention"


def test_changed_device_refused_before_export_or_open(synthetic, tmp_path):
    stock, output, _ = synthetic
    normal, models, backend = backend_for(tuple(output.values()))
    with pytest.raises(ProtocolError, match="changed"):
        updater.install(firmware.prepare(stock), Device("other", "other", "other", 1),
                        lambda *_: None, root=tmp_path, backend=backend)
    assert not models and list(tmp_path.iterdir()) == []


@pytest.mark.parametrize("raw", [
    b"", bytes.fromhex("0200010300002901") + bytes.fromhex("00002901") * 2,
    bytes.fromhex("0100020300002901") + bytes.fromhex("00002901") * 2,
    bytes.fromhex("010001020000290100002901"),
    bytes.fromhex("0100010300003001") + bytes.fromhex("00002901") * 2,
])
def test_unsupported_identity_refused(raw):
    with pytest.raises(ProtocolError):
        check_identity(SimpleNamespace(request=lambda _: raw))


def test_supported_identity_accepted():
    raw = bytes.fromhex("01000103") + bytes.fromhex("00002901") * 3
    assert check_identity(SimpleNamespace(request=lambda _: raw))["versions"] == ["1.29.0"] * 3


def test_descriptor_and_interface_discovery_does_not_open_keyboard_input(tmp_path):
    sysfs = tmp_path / "sys/class/hidraw"
    sysfs.mkdir(parents=True)
    usb = tmp_path / "sys/devices/usb1/1-2"
    usb.mkdir(parents=True)
    (usb / "idVendor").write_text("373f")
    (usb / "idProduct").write_text("0001")
    for index in range(4):
        interface = usb / f"1-2:1.{index}"
        hid = interface / f"hid-{index}"
        hid.mkdir(parents=True)
        (interface / "bInterfaceNumber").write_text(f"{index:02x}")
        (hid / "report_descriptor").write_bytes(bytes.fromhex("0600ff0901a101"))
        node = sysfs / f"hidraw{index}"
        node.mkdir()
        (node / "device").symlink_to(hid)
    found = discover(sysfs, tmp_path / "dev")
    assert len(found) == 1 and found[0].path.endswith("hidraw2")


def test_bad_package_never_reaches_device(synthetic, tmp_path):
    stock, _, _ = synthetic
    package = firmware.prepare(stock)
    # Frozen data cannot be modified by ordinary API use; even deliberate object
    # tampering is caught at the final device boundary.
    object.__setattr__(package, "mode", "stock")
    backend = SimpleNamespace(single_device=lambda: pytest.fail("Device opened before validation"))
    with pytest.raises(ValueError):
        updater.install(package, None, lambda *_: None, root=tmp_path, backend=backend)


@pytest.mark.parametrize("original", [None, "/usr/local/lib/custom"])
def test_external_os_tools_do_not_load_frozen_private_libraries(monkeypatch, original):
    monkeypatch.setenv("LD_LIBRARY_PATH", "/bundle/_internal")
    monkeypatch.delenv("LD_LIBRARY_PATH_ORIG", raising=False)
    if original is not None:
        monkeypatch.setenv("LD_LIBRARY_PATH_ORIG", original)
    result = environment()
    assert result.get("LD_LIBRARY_PATH") == original
    assert "LD_LIBRARY_PATH_ORIG" not in result
