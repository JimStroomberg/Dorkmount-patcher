"""Plain-language desktop flow. Demo and real hardware paths are structurally separate."""

import sys
import time
from importlib.resources import files
from pathlib import Path

from PySide6.QtCore import QObject, QThread, QTimer, Signal, Slot
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QTextBrowser,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from . import __version__, access, updater
from .firmware import obtain_originals, prepare


class Work(QObject):
    progress = Signal(int, str)
    result = Signal(object)
    failed = Signal(str)
    done = Signal()

    def __init__(self, job):
        super().__init__()
        self.job = job

    @Slot()
    def run(self):
        try:
            self.result.emit(self.job(self.progress.emit))
        except Exception as error:
            self.failed.emit(str(error))
        finally:
            self.done.emit()


class RealWorkflow:
    def check(self, progress):
        progress(0, "Looking for your keyboard…")
        return updater.probe()

    def prepare(self, restore, progress):
        originals = obtain_originals(updater.state_directory() / "official",
                                     lambda text: progress(0, text))
        return prepare(originals, restore)

    def install(self, package, device, progress):
        return updater.install(package, device, progress)

    def access(self, progress):
        progress(0, "Your desktop will ask permission to enable keyboard access.")
        access.setup()


class DemoWorkflow:
    """Never constructs a real device, downloads a file or installs a USB rule."""

    def check(self, progress):
        time.sleep(0.15)
        return "demo", {"directdraw": None}

    def prepare(self, restore, progress):
        for message in ("Getting the official firmware…", "Adding Dashboard…", "Checking the update…"):
            progress(0, message)
            time.sleep(0.15)
        return "demo package"

    def install(self, package, device, progress):
        for value in range(0, 101, 5):
            progress(value, "Demonstrating installation… No keyboard is being changed.")
            time.sleep(0.08)
        return None

    def access(self, progress):
        progress(0, "Demo: USB permissions are unchanged.")


class Window(QMainWindow):
    def __init__(self, demo=False, workflow=None):
        super().__init__()
        self.demo = demo
        self.workflow = workflow or (DemoWorkflow() if demo else RealWorkflow())
        self.phase, self.busy, self.device, self.package = "welcome", False, None, None
        self.thread, self.worker = None, None
        self.setWindowTitle("Dorkmount · Screen updater" + (" · Demo" if demo else ""))
        self.resize(820, 760)
        self.setMinimumSize(720, 680)
        self.setStyleSheet("""
            QWidget { background: #11161d; color: #e7edf5; font-size: 14px; }
            QLabel#brand { color: #7ed7c6; font-size: 13px; font-weight: 700; }
            QLabel#title { font-size: 30px; font-weight: 700; }
            QLabel#muted { color: #b4c0cf; }
            QLabel#status { font-size: 19px; font-weight: 600; }
            QFrame#card { background: #1a222d; border: 1px solid #34404f; border-radius: 12px; }
            QFrame#card QLabel, QFrame#card QCheckBox { background: transparent; }
            QPushButton { background: #263240; border: 1px solid #405063; border-radius: 7px; padding: 11px 16px; }
            QPushButton:hover { background: #34485b; }
            QPushButton:focus { border: 2px solid #a9f0e0; }
            QPushButton#primary { background: #8de0ca; color: #092a25; font-weight: 700; border: 0; }
            QPushButton#primary:hover { background: #b4f0e0; }
            QPushButton:disabled { background: #232d37; color: #7d8a99; }
            QPushButton#primary:disabled { background: #2b3e3b; color: #8da59f; }
            QProgressBar { border: 0; background: #293544; border-radius: 5px; min-height: 10px; }
            QProgressBar::chunk { background: #8de0ca; border-radius: 5px; }
            QComboBox { padding: 8px; border: 1px solid #405063; border-radius: 6px; }
            QTextEdit { background: #0b1016; border: 1px solid #405063; font-family: monospace; }
            QCheckBox { spacing: 10px; }
            QCheckBox::indicator { width: 18px; height: 18px; border: 1px solid #a4b6c8; border-radius: 3px; background: #11161d; }
            QCheckBox::indicator:checked { background: #8de0ca; border: 2px solid #d5fff4; }
        """)
        body = QWidget()
        self.setCentralWidget(body)
        layout = QVBoxLayout(body)
        layout.setContentsMargins(34, 28, 34, 24)
        layout.setSpacing(16)
        layout.addWidget(self.label("DORKMOUNT  /  SCREEN UPDATER" + ("  /  DEMO" if demo else ""), "brand"))
        layout.addWidget(self.label("Prepare your screen for widgets.", "title"))
        layout.addWidget(self.label(
            "This app only updates your keyboard. It does not include widgets.\n"
            "Dorkmount, the separate widget app, is coming soon.", "muted"))
        self.steps = self.label("1  Check keyboard     →     2  Prepare     →     3  Install     →     4  Verify", "muted")
        layout.addWidget(self.steps)
        card = QFrame()
        card.setObjectName("card")
        content = QVBoxLayout(card)
        content.setContentsMargins(22, 22, 22, 22)
        content.setSpacing(15)
        self.status = self.label("Let’s check your keyboard.", "status")
        content.addWidget(self.status)
        self.description = self.label(
            "Connect the keyboard directly by USB, with the screen and number pad attached. "
            "Close Dorkmount, IO Center and other keyboard-control apps first.", "muted")
        content.addWidget(self.description)
        self.mode = QComboBox()
        self.mode.addItems(["Add Dashboard to my screen", "Restore original keyboard firmware"])
        self.mode.currentIndexChanged.connect(self.reset)
        content.addWidget(self.mode)
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setTextVisible(False)
        self.progress.setAccessibleName("Update progress")
        content.addWidget(self.progress)
        self.accept = QCheckBox("I understand this is a test release and a failed update could\nmake the keyboard unusable.")
        self.accept.setVisible(False)
        self.accept.toggled.connect(self.accept_changed)
        content.addWidget(self.accept)
        self.primary = QPushButton("Check keyboard")
        self.primary.setObjectName("primary")
        self.primary.clicked.connect(self.advance)
        content.addWidget(self.primary)
        layout.addWidget(card)
        self.notice = self.label(
            "Demo mode · No keyboard access, downloads or system changes." if demo else
            "Test release · For the supported Dark Mount revision with firmware 1.29.0. "
            "Installation and restoration tested on CachyOS; Ubuntu desktop testing pending.", "muted")
        layout.addWidget(self.notice)
        row = QHBoxLayout()
        self.access_button = QPushButton("Set up USB access")
        self.access_button.clicked.connect(self.setup_access)
        row.addWidget(self.access_button)
        self.help_button = QPushButton("Help && details")
        self.help_button.clicked.connect(lambda: self.details.setVisible(not self.details.isVisible()))
        row.addWidget(self.help_button)
        row.addStretch()
        self.docs_button = QPushButton("For developers")
        self.docs_button.clicked.connect(self.developer_guide)
        row.addWidget(self.docs_button)
        layout.addLayout(row)
        self.details = QTextEdit()
        self.details.setReadOnly(True)
        self.details.setPlainText(
            "Dashboard replaces the Clock icon and its clock/timer submenu. "
            "It shows Waiting… until a compatible app starts drawing. "
            "Dorkmount, the separate widget app, is coming soon. This updater does not include widgets. "
            "Left/Right switches views in a compatible host app. Double-click Menu to leave.\n\n"
            "The updater downloads only the exact supported official files from be quiet!, "
            "checks them, and adds Dashboard locally. Installation and restoration have been "
            "tested on a CachyOS keyboard setup. Ubuntu desktop testing is pending.\n\n"
            "USB setup adds a narrow active-desktop permission rule and asks for your administrator password. "
            "Reconnect the keyboard afterward. The updater itself runs without administrator privileges.\n\n"
            "If an update stops: keep the keyboard connected, save the details and consult docs/TROUBLESHOOTING.md. "
            "Do not repeat installation blindly. Recovery from nonbooting firmware is unproven.\n\n"
            f"Version {__version__}. Local files: {updater.state_directory()}"
        )
        self.details.setMinimumHeight(120)
        self.details.setVisible(False)
        layout.addWidget(self.details)
        layout.addStretch()
        layout.addWidget(self.label("Independent community project · Not affiliated with be quiet!", "muted"))

    @staticmethod
    def label(text, kind):
        result = QLabel(text)
        result.setObjectName(kind)
        result.setWordWrap(True)
        return result

    @Slot()
    def developer_guide(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("DirectDraw developer guide")
        dialog.resize(860, 720)
        layout = QVBoxLayout(dialog)
        guide = QTextBrowser()
        guide.document().setDefaultStyleSheet("pre, code { font-family: monospace; } p { margin-bottom: 12px; }")
        guide.setOpenExternalLinks(False)
        guide.setMarkdown(files(__package__).joinpath("data/developers.md").read_text())
        # Only explicit HTTPS links can leave the bundled guide.
        guide.anchorClicked.connect(lambda url: QDesktopServices.openUrl(url)
                                    if url.scheme() == "https" else None)
        layout.addWidget(guide)
        close = QPushButton("Close guide")
        close.clicked.connect(dialog.accept)
        layout.addWidget(close)
        dialog.exec()

    @Slot()
    def reset(self):
        if self.busy:
            return
        self.phase, self.device, self.package = "welcome", None, None
        self.accept.setChecked(False)
        self.accept.setVisible(False)
        self.primary.setText("Check keyboard")
        self.primary.setEnabled(True)
        self.status.setText("Let’s check your keyboard.")
        self.description.setText("Close other keyboard-control apps. Connect the screen and number pad, then check again.")
        self.progress.setValue(0)

    @Slot(bool)
    def accept_changed(self, checked):
        if self.phase == "ready" and not self.busy:
            self.primary.setEnabled(checked)

    def start(self, job, finished):
        if self.busy:
            return
        self.busy = True
        self.primary.setEnabled(False)
        self.mode.setEnabled(False)
        self.access_button.setEnabled(False)
        self.accept.setEnabled(False)
        self._finished_callback = finished
        self.worker = Work(job)
        self.thread = QThread(self)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.progress.connect(self.on_progress)
        self.worker.result.connect(self.job_result)
        self.worker.failed.connect(self.failed)
        self.worker.done.connect(self.thread.quit)
        self.worker.done.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.idle)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.start()

    @Slot(object)
    def job_result(self, result):
        self._finished_callback(result)

    @Slot()
    def idle(self):
        self.busy = False
        self.thread, self.worker = None, None
        self.mode.setEnabled(self.phase != "attention")
        self.access_button.setEnabled(self.phase != "attention")
        self.accept.setEnabled(True)
        self.primary.setEnabled(self.phase not in ("attention", "done") and (
            self.phase != "ready" or self.accept.isChecked()))

    @Slot(int, str)
    def on_progress(self, value, message):
        self.progress.setValue(value)
        self.status.setText(message)

    @Slot(str)
    def failed(self, message):
        installing = self.phase == "installing"
        self.phase = "attention" if installing else "welcome"
        self.package = None
        self.status.setText("The update needs attention." if installing else "We couldn’t complete that step.")
        self.description.setText(message)
        self.details.append("\n" + message)
        self.details.setVisible(True)
        self.accept.setVisible(False)
        self.primary.setText("Update stopped" if installing else "Check keyboard again")

    @Slot()
    def advance(self):
        if self.phase == "welcome":
            self.start(self.workflow.check, self.checked)
        elif self.phase == "checked":
            restore = self.mode.currentIndex() == 1
            self.start(lambda progress: self.workflow.prepare(restore, progress), self.prepared)
        elif self.phase == "ready" and self.accept.isChecked():
            self.phase = "installing"
            self.description.setText("Keep your computer awake and the keyboard connected until verification finishes.")
            self.primary.setText("Installing…")
            self.start(lambda progress: self.workflow.install(self.package, self.device, progress), self.installed)

    def checked(self, result):
        self.device, info = result
        self.phase = "checked"
        self.status.setText("Your keyboard is supported.")
        self.description.setText(
            "Custom screen support is present. You can install the Dashboard update or choose original firmware above."
            if info["directdraw"] else
            "We’ll get the official firmware, prepare your update and verify every file. Your keyboard stays unchanged during preparation."
        )
        self.primary.setText("Prepare update")

    def prepared(self, package):
        self.package, self.phase = package, "ready"
        restore = self.mode.currentIndex() == 1
        self.status.setText("Ready to restore original firmware." if restore else "Ready to add Dashboard.")
        self.description.setText(
            "This returns the screen to its original built-in functions."
            if restore else "Dashboard replaces Clock. It shows Waiting… until a compatible app provides widgets. Dorkmount, the separate widget app, is coming soon."
        )
        self.description.setText(self.description.text() +
            " Allow several minutes. Keep the screen and number pad attached and all keyboard apps closed.")
        self.accept.setVisible(True)
        self.accept.setChecked(False)
        self.primary.setText("Restore original firmware" if restore else "Install Dashboard")

    def installed(self, directory):
        self.phase = "done"
        self.progress.setValue(100)
        self.accept.setVisible(False)
        restore = self.mode.currentIndex() == 1
        self.status.setText("Demo complete." if self.demo else (
            "Original firmware restored." if restore else "Your screen is ready."))
        self.description.setText(
            "This was a simulation. No keyboard was accessed." if self.demo else
            "You can now close the updater." if restore else
            "Close this updater and select the dashboard icon on your keyboard. Waiting… means it is ready for a compatible widget app. Dorkmount is coming soon; this updater does not provide widgets."
        )
        self.primary.setText("Finished")
        if directory:
            self.details.append(f"\nVerified session and restoration files: {directory}")

    @Slot()
    def setup_access(self):
        if self.busy:
            return
        self.start(self.workflow.access, lambda _: self.access_ready())

    def access_ready(self):
        self.phase = "welcome"
        self.device, self.package = None, None
        self.accept.setVisible(False)
        self.status.setText("USB access is set up." if not self.demo else "Demo: USB access unchanged.")
        self.description.setText("Unplug and reconnect the keyboard, then check it again.")
        self.primary.setText("Check keyboard")

    def closeEvent(self, event):
        if self.busy:
            QMessageBox.information(self, "Please wait", "Let this step finish before closing the updater. Keep the keyboard connected.")
            event.ignore()
        else:
            event.accept()


def run(demo=False, screenshot=None):
    app = QApplication.instance() or QApplication(sys.argv[:1])
    if sys.platform.startswith("linux"):
        from PySide6.QtGui import QFont
        # Native packages supply this font, including on a minimal desktop.
        app.setFont(QFont("DejaVu Sans"))
    app.setApplicationName("Dorkmount-patcher")
    window = Window(demo=demo)
    window.show()
    if screenshot:
        def capture():
            window.grab().save(str(Path(screenshot)))
            app.quit()
        QTimer.singleShot(200, capture)
    return app.exec()
