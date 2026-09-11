# Third-party material and provenance

Project source is GPL-3.0-only. Manufacturer firmware is not distributed or
licensed by this project. Full inputs, patched outputs and stock restoration
copies remain on the user's computer.

## QLink and host client

[re133/iocenter-linux](https://github.com/re133/iocenter-linux), revision
`6e7a10a27fe5d2e552dec9d7c6adb0ba17191da9`, is GPL-3.0-only.
`src/dorkmount_patcher/qlink.py` adapts its `bqlink.py` framing, CRC,
session negotiation and request/notification separation. It replaces direct
device I/O with an injected interface and adds strict session/fragment checks,
explicit update notifications and no-retry behavior. Device discovery is based
on the same descriptor/USB identity research; it is limited to vendor interface 02.

`src/dorkmount_patcher/directdraw.py` carries the existing Dorkmount controller's
`protocol.py` sender from commit `8047529`, with an added standalone connection
context manager and corrected module description. This is original Dorkmount
project code under GPL-3.0-only. Dorkmount is not a runtime dependency.

The update state machine is a new implementation of protocol facts observed in
the official IO Center Web updater and preceding experiments. No manufacturer
JavaScript is included. The local research source and validation comparisons
are excluded from packages and Git. See [updater protocol](docs/UPDATER-PROTOCOL.md).

## Firmware patches

The DMR1/DMR2 C, assembly, linker scripts and original builders retain their
recorded extraction hashes. See [firmware provenance](docs/PROVENANCE.md).
`src/dorkmount_patcher/data/dmr2.json` includes 301 bytes of replacement patches:
the compiled original DMR2 extension and short instruction/routing changes.
It includes no original Clock routine or full firmware image. The generator
verifies exact complete image hashes and all patch ranges before exporting it.
Source hashes and both preimage/replacement hashes are included for reproduction.

## Desktop dependencies

The optional desktop uses unmodified PySide6 (Qt for Python), distributed under
its applicable LGPL/GPL/commercial terms, and Shiboken6. PyInstaller creates the
optional executable bundle under its GPL license with its bootloader exception.
The Linux bundle includes wheel metadata, available wheel license files, the
unmodified license directory from the matching official Qt for Python source
release, and Linux system-library copyright notices; keep these notices with
redistributed bundles. `packaging/licenses/` records source URLs and hashes.
The Python source distribution
declares dependencies instead of copying them into the source tree.

Original project artwork and interface styling are GPL-3.0-only. Manufacturer
names identify compatibility and do not imply endorsement.
