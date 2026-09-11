# Project boundary and roadmap

The current path is:

`host widgets → host RGB565 renderer → QLink / DMR → patched Main routing → patched Dock Clock handler → existing LCD routines`

Dorkmount-patcher owns the firmware extension, supported-image definitions, offline patch builders and canonical DMR protocol. Dorkmount owns the Linux application, sensor/game data, widget rendering, connection lifecycle and display-key configuration. The research lab retains captures, firmware analysis and experimental tooling independently.

The source extraction changes no firmware bytes and requires no keyboard update. DMR2 uses the existing DMR1 request prefix and its own capability reply; application and firmware release numbers remain separate. New host widgets can use the existing drawing commands without modifying firmware.

## Implemented boundary

- Exact official 1.29.0 inputs for all three MCU images. Tested hardware: model 1, revision 1.
- Main routing patch plus bounded Dock payload/hooks in the Clock slot. Stock Numpad image is verified and copied unchanged.
- RGB565 solid rectangles and pixel rectangles; volatile direct drawing, serialized acknowledgments, active-view checks.
- DMR2 Left / Right notifications and original Menu double-click return.
- Original project C/assembly/linker source and Python offline builders; no controller dependency and no flasher.

## Planned work

1. Consolidate target definitions and generation into a reviewed patch engine while reproducing the current exact hashes. Add patch-range verification and a machine-readable dry-run report before exporting.
2. Make installation and restoration repeatable: exact device identity, known image set, transfer verification, interruption behavior and recovery evidence. Official tooling is useful evidence; support for arbitrary custom images must not be assumed.
3. Define application-neutral conformance tests and a small reference host client. Preserve existing DMR1/DMR2 compatibility when extending capabilities; negotiate only implemented operations.
4. Investigate a separate Numpad target for volatile updates to the eight display keys. Existing stored-image uploads write persistent storage and are not a live animation API.
5. Evaluate larger transfers, event source/generation identifiers and frame presentation only after measuring the hardware path. A framebuffer, atomic present, per-display capabilities and asynchronous transport are proposals, not features of DMR2.

The initial split does not implement a plugin ABI, a new firmware version, an installer or a portable flashing framework. The existing controller remains usable with the already-installed DMR2 extension.
