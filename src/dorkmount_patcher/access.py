"""Explicit one-time desktop USB permission setup; never runs during a transfer."""

import subprocess
from importlib.resources import files

from .system import environment


def setup():
    rule = files(__package__).joinpath("data/70-dorkmount-patcher.rules").read_text()
    # A fixed script and fixed destination. No paths, commands or environment values
    # supplied by the caller are evaluated by the elevated shell.
    script = "set -eu\ninstall -d -m 755 /etc/udev/rules.d\n"
    script += "cat > /etc/udev/rules.d/70-dorkmount-patcher.rules <<'DORKMOUNT_RULE'\n"
    script += rule + "DORKMOUNT_RULE\n"
    script += "chmod 644 /etc/udev/rules.d/70-dorkmount-patcher.rules\n"
    script += "udevadm control --reload-rules\nudevadm trigger --subsystem-match=hidraw\nudevadm settle\n"
    subprocess.run(["pkexec", "/bin/sh", "-c", script], check=True, capture_output=True,
                   timeout=180, env=environment())
