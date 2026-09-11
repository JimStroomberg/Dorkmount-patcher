# Project boundary and roadmap

The current path is:

`host widgets → host RGB565 renderer → QLink / DMR → patched Main routing → patched Dock Clock handler → existing LCD routines`

Dorkmount-patcher owns firmware, exact-image patching, the Linux installer and a small renderer-independent DirectDraw reference client. Dorkmount owns the companion application, sensor/game data, widgets and display-key configuration. The private lab retains historical experiments and sensitive artifacts independently.

The source extraction changes no firmware bytes and requires no keyboard update. DMR2 uses the existing DMR1 request prefix and its own capability reply; application and firmware release numbers remain separate. New host widgets can use the existing drawing commands without modifying firmware.

## Implemented boundary

- Exact official 1.29.0 inputs for all three MCU images. Tested hardware: model 1, revision 1.
- Main routing patch plus bounded Dock payload/hooks in the Clock slot. Stock Numpad image is verified and copied unchanged.
- RGB565 solid rectangles and pixel rectangles; volatile direct drawing, serialized acknowledgments, active-view checks.
- DMR2 Left / Right notifications and original Menu double-click return.
- Original C/assembly/linker source and offline builders, with unchanged firmware hashes.
- Compiler-free runtime patching from verified local/downloaded originals; full hash and range checks.
- Plain-language Linux desktop updater with simulated mode, explicit install action, scoped USB setup, stock copies, a sleep inhibitor, requested-range transfers and fresh reconnect verification.
- Standalone DirectDraw client, complete developer guide, synthetic protocol/frame tests and Linux bundling. No Dorkmount or private-lab runtime dependency.

The native updater is new and awaits its first hardware test. It is distinct from the previously used official Web update route.

## Code map

`firmware.py` owns immutable firmware packages and patch verification. `qlink.py`
owns framing/session/notification correlation over injected I/O. `device.py`
supplies the Linux hidraw adapter and advisory locks. `dfu.py` follows the device's
requested ranges and completion events; `updater.py` owns the full install and
fresh-verification lifecycle. `gui.py` runs that work outside the GUI thread.
`directdraw.py` is the renderer-independent host client. Its connection helper
does not allow firmware commands. Demo mode never constructs the real workflow.

## Planned work

The first packaged release targets Ubuntu 26.04 and newer validated releases and
fully updated stable CachyOS, both x86-64. macOS on Apple Silicon and Bazzite are
**Coming soon**; Windows follows later. The existing Mac demo does not establish
Mac firmware-update support. See [the platform release plan](../README.md#planned-platform-support).

Linux release preparation includes dependency-aware graphical installation,
GitHub Actions package builds, clean-desktop installation checks, and documented
source builds and dependencies for other distributions. It must preserve the
private/public artifact boundary and the exact firmware checks.

1. Complete physical installation, restoration, graphics and navigation checks with the new native app. Validate bootloader timing/ACK shapes and the Linux permission/reconnect flow.
2. Establish interruption and nonbooting-device recovery. The preview stops uncertain transfers without retrying or claiming recovery.
3. Expand client conformance and OS transport coverage while preserving DMR1/DMR2 compatibility. Stabilize a public host-library API based on developer use.
4. Investigate a separate Numpad target for volatile updates to the eight display keys. Existing stored-image uploads write persistent storage and are not a live animation API.
5. Evaluate larger transfers, event source/generation identifiers and frame presentation only after measuring the hardware path. A framebuffer, atomic present, per-display capabilities and asynchronous transport are proposals, not features of DMR2.

There is no new firmware behavior, plugin ABI or portable flashing framework. The original controller remains compatible with the exact same DMR2 extension.
