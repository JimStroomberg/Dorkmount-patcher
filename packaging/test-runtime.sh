#!/bin/sh
set -eu
# Run before installing Xvfb/Weston: harness dependencies must not hide missing
# application libraries. Match the frozen bootloader's library search path.
bundle=/opt/dorkmount-patcher/_internal
for plugin in libqoffscreen.so libqxcb.so libqwayland.so; do
    LD_LIBRARY_PATH="$bundle" ldd "$bundle/PySide6/Qt/plugins/platforms/$plugin" > "/results/$plugin.dependencies.txt"
    if grep -q 'not found' "/results/$plugin.dependencies.txt"; then
        cat "/results/$plugin.dependencies.txt"
        exit 1
    fi
done
test "$(dorkmount-patcher --version)" = "$EXPECTED_VERSION"
mkdir -p /tmp/dorkmount-desktop
HOME=/tmp/dorkmount-desktop QT_QPA_PLATFORM=offscreen dorkmount-patcher --demo --screenshot /results/demo-runtime.png
test -s /results/demo-runtime.png
