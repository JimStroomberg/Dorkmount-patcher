# Architecture and roadmap

The current path is:

`host widgets → host RGB565 renderer → QLink / DMR → patched Main routing → patched Dock Dashboard handler → existing LCD routines`

Dorkmount-patcher owns firmware, exact-image patching, the Linux installer and a small renderer-independent DirectDraw reference client. Dorkmount owns the companion application, sensor/game data, widgets and display-key configuration.

The original source extraction preserved DMR1/DMR2. The current DMR3 candidate adds a Dashboard icon and waiting view, using the existing drawing requests and its own capability reply. Application and firmware release numbers remain separate. New host widgets can use the existing drawing commands without modifying firmware.

## Components

- Exact official 1.29.0 inputs for all three MCU images. Tested hardware: model 1, revision 1.
- Main routing patch plus bounded Dock payload/hooks in the Clock slot. Stock Numpad image is verified and copied unchanged.
- RGB565 solid rectangles and pixel rectangles; volatile direct drawing, serialized acknowledgments, active-view checks.
- DMR2/DMR3 Left / Right notifications and original Menu double-click return.
- DMR3 Dashboard artwork, direct entry and waiting text, with old Clock controls bypassed.
- C/assembly/linker source and offline builders with exact pinned hashes; DMR1/DMR2 remain unchanged.
- Compiler-free runtime patching from verified local/downloaded originals; full hash and range checks.
- Plain-language Linux desktop updater with simulated mode, explicit install action, scoped USB setup, stock copies, a sleep inhibitor, requested-range transfers and fresh reconnect verification.
- Standalone DirectDraw client, developer guide, protocol/frame tests and Linux bundling. Companion apps can use it independently of Dorkmount.
- Ubuntu/CachyOS package metadata, desktop integration and USB rules; GitHub Actions build, installed-package checks and audited prerelease/stable release workflow.

The native installer and DMR3 workflow have maintainer-confirmed CachyOS hardware results, including restoration and reinstallation. Ubuntu 26.04 still needs real-machine verification. Prior DMR1/DMR2 evidence used the official Web update route. See [validation](VALIDATION.md).

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
Mac firmware-update support. See [platform support](../README.md#compatibility).

Linux packages install declared dependencies through the system package manager.
The container checks cover installation, X11/headless-Wayland launch and removal;
full desktop and hardware acceptance remain separate. Source builds and dependency
requirements for other distributions are in [Building](BUILDING.md) and
[Dependencies](DEPENDENCIES.md).

1. Complete Ubuntu 26.04 desktop and keyboard acceptance using the final native package. Extend evidence beyond the single CachyOS test setup.
2. Extend stage-specific interruption and recovery evidence. CachyOS disconnect/restart tests passed as reported; nonbooting-device recovery remains unproven. The app stops uncertain transfers without automatic retries.
3. Expand client conformance and OS transport coverage while preserving DMR1/DMR2/DMR3 compatibility. Stabilize a public host-library API based on developer use.
4. Investigate a separate Numpad target for volatile updates to the eight display keys. Existing stored-image uploads write persistent storage and are not a live animation API.
5. Evaluate larger transfers, event source/generation identifiers and frame presentation only after measuring the hardware path. A framebuffer, atomic present, per-display capabilities and asynchronous transport are proposals, not features of DMR1/DMR2/DMR3.

There is no plugin ABI or portable flashing framework. Older strict companions must add DMR3 to their known capability contracts and repaint after Dashboard entry. The patcher provides the updated reference client; companion-specific integration belongs in its own repository.
