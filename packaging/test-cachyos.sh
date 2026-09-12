#!/usr/bin/env bash
set -euo pipefail
unshare --net true
# Users must be able to upgrade alpha -> beta -> stable without a downgrade.
test "$(vercmp 0.2.0alpha2-1 0.2.0beta1-1)" = -1
test "$(vercmp 0.2.0beta1-1 0.2.0-1)" = -1
pacman -Syu --noconfirm 2>&1 | tee /results/pacman-update.log
# Local package follows the distribution's existing local-signature policy.
pacman -U --noconfirm /packages/*.pkg.tar.zst 2>&1 | tee /results/pacman-install.log
sh /scripts/test-runtime.sh
pacman -S --needed --noconfirm desktop-file-utils xorg-server-xvfb xorg-xauth weston 2>&1 | tee /results/pacman-harness.log
sh /scripts/test-installed.sh
pacman -Q > /results/installed-packages.txt
cp /etc/os-release /results/os-release.txt
pacman -R --noconfirm dorkmount-patcher 2>&1 | tee /results/pacman-remove.log
if grep -q '^error:' /results/pacman-*.log; then
    printf '%s\n' 'A package operation or hook failed; inspect the retained pacman logs.' >&2
    exit 1
fi
test ! -e /usr/bin/dorkmount-patcher
test ! -e /usr/share/applications/dorkmount-patcher.desktop
test ! -e /usr/lib/udev/rules.d/70-dorkmount-patcher.rules
printf '%s\n' 'CachyOS package uninstall verified.'
