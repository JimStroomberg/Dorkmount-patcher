#!/bin/sh
set -eu
export DEBIAN_FRONTEND=noninteractive
# Use authenticated HTTPS; HTTP mirrors may be unavailable on developer networks.
sed -i 's|http://|https://|g' /etc/apt/sources.list.d/ubuntu.sources
printf '%s\n' 'Acquire::https::CaInfo "/results/bootstrap-ca.crt";' 'Acquire::https::Timeout "30";' 'Acquire::Retries "2";' > /etc/apt/apt.conf.d/99dorkmount-test
apt-get update -qq
# The package manager must discover runtime requirements from the .deb.
apt-get install -y --no-install-recommends /packages/*.deb
# These are test harness tools, deliberately installed after the app/dependencies.
apt-get install -y --no-install-recommends desktop-file-utils xvfb xauth weston
sh /scripts/test-installed.sh
dpkg-query -W > /results/installed-packages.txt
cat /etc/os-release > /results/os-release.txt
apt-get remove -y dorkmount-patcher
test ! -e /usr/bin/dorkmount-patcher
test ! -e /usr/share/applications/dorkmount-patcher.desktop
test ! -e /usr/lib/udev/rules.d/70-dorkmount-patcher.rules
printf '%s\n' 'Ubuntu package uninstall verified.'
