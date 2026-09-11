#!/usr/bin/env bash
set -euo pipefail
pacman -Syu --noconfirm
# Local alpha package follows the distribution's existing local-signature policy.
pacman -U --noconfirm /packages/*.pkg.tar.zst
pacman -S --needed --noconfirm desktop-file-utils xorg-server-xvfb xorg-xauth weston
sh /scripts/test-installed.sh
pacman -Q > /results/installed-packages.txt
cp /etc/os-release /results/os-release.txt
pacman -R --noconfirm dorkmount-patcher
test ! -e /usr/bin/dorkmount-patcher
test ! -e /usr/share/applications/dorkmount-patcher.desktop
test ! -e /usr/lib/udev/rules.d/70-dorkmount-patcher.rules
printf '%s\n' 'CachyOS package uninstall verified.'
