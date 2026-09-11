#!/usr/bin/env bash
set -euo pipefail
# Disposable container only. No host devices or credentials are mounted.
useradd --create-home builder
cp -a /input /tmp/package
chown -R builder:builder /tmp/package
cd /tmp/package
runuser -u builder -- makepkg --nodeps --noconfirm
cp -- ./*.pkg.tar.zst /output/
