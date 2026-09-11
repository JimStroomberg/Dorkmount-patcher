import os
import time

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6.QtWidgets import QApplication

from dorkmount_patcher import access, device, updater
from dorkmount_patcher.gui import DemoWorkflow, Window


@pytest.fixture
def app():
    return QApplication.instance() or QApplication([])


def wait(app, window):
    deadline = time.monotonic() + 10
    while window.busy and time.monotonic() < deadline:
        app.processEvents()
        time.sleep(0.01)
    app.processEvents()
    assert not window.busy


def test_demo_all_steps_no_hardware_network_or_system_setup(app, monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail("Demo attempted a real operation")
    monkeypatch.setattr(device, "connect", forbidden)
    monkeypatch.setattr(updater, "probe", forbidden)
    monkeypatch.setattr(updater, "install", forbidden)
    monkeypatch.setattr(access, "setup", forbidden)
    window = Window(demo=True)
    window.show()
    window.advance()
    wait(app, window)
    assert window.phase == "checked"
    window.advance()
    wait(app, window)
    assert window.phase == "ready" and not window.primary.isEnabled()
    window.advance()
    assert window.phase == "ready"
    window.accept.setChecked(True)
    assert window.primary.isEnabled()
    window.advance()
    wait(app, window)
    assert window.phase == "done"
    assert "Demo complete" in window.status.text()
    window.close()


def test_failed_install_disables_retry_and_never_shows_success(app):
    class Failing(DemoWorkflow):
        def install(self, *args):
            raise IOError("simulated disconnected keyboard")
    window = Window(demo=True, workflow=Failing())
    window.show()
    for _ in range(2):
        window.advance()
        wait(app, window)
    window.accept.setChecked(True)
    window.advance()
    wait(app, window)
    assert window.phase == "attention"
    assert not window.primary.isEnabled() and not window.mode.isEnabled()
    assert "disconnected" in window.description.text()
    window.close()


def test_mode_change_invalidates_prepared_package(app):
    window = Window(demo=True)
    for _ in range(2):
        window.advance()
        wait(app, window)
    window.accept.setChecked(True)
    window.mode.setCurrentIndex(1)
    assert window.phase == "welcome" and window.package is None
    assert not window.accept.isChecked()
    window.close()
