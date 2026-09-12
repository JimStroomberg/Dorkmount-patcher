#!/bin/sh
set -eu
# Container test of the installed product, with no physical USB devices.
test -f /usr/share/applications/dorkmount-patcher.desktop
test -f /usr/share/icons/hicolor/scalable/apps/io.github.JimStroomberg.DorkmountPatcher.svg
test -f /usr/lib/udev/rules.d/70-dorkmount-patcher.rules
test -f /opt/dorkmount-patcher/_internal/dorkmount_patcher/data/dmr2.json
test -f /opt/dorkmount-patcher/_internal/dorkmount_patcher/data/dmr3.json
test -f /opt/dorkmount-patcher/_internal/dorkmount_patcher/data/developers.md
test "$(dorkmount-patcher --version)" = "$EXPECTED_VERSION"
desktop-file-validate /usr/share/applications/dorkmount-patcher.desktop
udevadm verify /usr/lib/udev/rules.d/70-dorkmount-patcher.rules
mkdir -p /tmp/dorkmount-desktop /results
chmod 755 /tmp/dorkmount-desktop
HOME=/tmp/dorkmount-desktop QT_QPA_PLATFORM=offscreen dorkmount-patcher --demo --screenshot /results/demo.png
test -s /results/demo.png
# Exercise X11 plugin loading too, not only Qt's minimal offscreen plugin.
HOME=/tmp/dorkmount-desktop QT_QPA_PLATFORM=xcb xvfb-run -a dorkmount-patcher --demo --screenshot /results/demo-x11.png
test -s /results/demo-x11.png
export XDG_RUNTIME_DIR=/tmp/dorkmount-runtime
mkdir -p "$XDG_RUNTIME_DIR"
chmod 700 "$XDG_RUNTIME_DIR"
weston --backend=headless --renderer=pixman --socket=dorkmount-test --idle-time=0 > /results/wayland-compositor.log 2>&1 &
compositor=$!
trap 'kill "$compositor" 2>/dev/null || true' EXIT INT TERM
attempt=0
while [ ! -S "$XDG_RUNTIME_DIR/dorkmount-test" ]; do
    attempt=$((attempt + 1))
    if [ "$attempt" -ge 20 ]; then cat /results/wayland-compositor.log; exit 1; fi
    sleep 1
done
HOME=/tmp/dorkmount-desktop WAYLAND_DISPLAY=dorkmount-test QT_QPA_PLATFORM=wayland dorkmount-patcher --demo --screenshot /results/demo-wayland.png
test -s /results/demo-wayland.png
test ! -d /tmp/dorkmount-desktop/.local/state/dorkmount-patcher
# Exercise HTTPS in the actual frozen runtime, without any USB access. Keep
# manufacturer bytes inside this disposable container, outside uploaded results.
HOME=/tmp/dorkmount-desktop dorkmount-patcher prepare --download --output /tmp/dorkmount-prepared > /results/prepare.json
test -s /tmp/dorkmount-prepared/manifest.json
rm -rf /tmp/dorkmount-prepared
printf '%s\n' 'Installed app launches; desktop metadata and USB rule validate; demo creates no update state.'
