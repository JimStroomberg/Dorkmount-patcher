# Dorkmount-patcher

Add custom dashboards and widgets to the be quiet! Dark Mount Media Dock.

**Development candidate 0.2.0a3: Dashboard.** A guided desktop app checks the keyboard,
downloads the exact supported official firmware, adds the Dashboard extension locally,
installs it and verifies its return. Other developers can use the independent
protocol documentation and reference client to build their own applications.

The new DMR3 firmware replaces the Clock tile and submenu with a dashboard icon
and a **Waiting…** screen. **Both this firmware candidate and the native
installer still need a real-keyboard trial.** Offline tests do not establish
hardware safety or recovery. A failed update can make the keyboard unusable.
Read [the hardware test guide](docs/TESTING.md) before installing this preview.

## Platform support

| Platform | Release plan |
|---|---|
| Ubuntu 26.04 and newer validated releases, x86-64 | Alpha packages |
| Fully updated stable CachyOS, x86-64 | Alpha packages |
| macOS on Apple Silicon | Coming soon |
| Current stable Bazzite, desktop mode | Coming soon |
| Windows | Later |

The packages include the app, a menu shortcut and the keyboard-access rule.
The package manager installs required libraries. These alpha targets still need
physical keyboard validation; newer Ubuntu releases must be checked before being
listed as tested. Other distributions can use the [source build guide](docs/BUILDING.md)
and [dependency reference](docs/DEPENDENCIES.md).

## Use the desktop app

The published alpha.2 packages contain the older DMR2 Clock-based extension.
**Dashboard is an unreleased candidate**; use this checkout's source or a locally
built candidate package to test it. See [candidate notes](docs/releases/v0.2.0-alpha.3.md).

Published packages are available from [Releases](https://github.com/JimStroomberg/Dorkmount-patcher/releases).
On Ubuntu, open the `.deb` with the system's package installer, or install it with
`sudo apt install ./dorkmount-patcher_*_amd64.deb`. On CachyOS, use
`sudo pacman -U ./dorkmount-patcher-*-x86_64.pkg.tar.zst` from the download folder.
Confirm the installation, reconnect the keyboard and open **Dorkmount Patcher**
from the application menu. No Python setup, firmware compiler or companion app is
needed. The [release notes](docs/releases/v0.2.0-alpha.2.md) include exact filenames.

1. Connect the keyboard with its screen and number pad attached. Close other
   keyboard-control applications.
2. Choose **Check keyboard**, then **Prepare update**.
3. Review the result and choose **Install Dashboard** in this candidate.
4. Keep the keyboard connected until verification finishes.

If access is denied after reconnecting, **Set up USB access** asks for the desktop
administrator password once. The updater itself runs without elevated privileges. Internet
access is needed to obtain the exact official files; verified cached files work
offline afterward. Unknown hardware or firmware is refused.

After installing this candidate, close the updater and select the **dashboard
icon** on the keyboard screen. It shows **Waiting…** until a DMR3-compatible
application draws a complete screen. The Clock submenu is no longer accessible.
Left/Right switches host views; double-click Menu returns to the selector.

**Restore original keyboard firmware** writes the exact stock 1.29.0 set from a
responsive supported keyboard. It is not a nonbooting-device recovery tool.
Its first native-app physical restoration trial is also outstanding.

## Run from source or explore without a keyboard

With Python 3.11+:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install '.[desktop]'
.venv/bin/dorkmount-patcher
```

Use `--demo` to explore without keyboard access, downloads or system changes.
Demo also runs on macOS; hardware support in this preview is Linux-only.

## Build your own screen app

Start with [the developer guide](docs/DEVELOPERS.md) and
[first_pixels.py](examples/first_pixels.py). The guide includes complete QLink
framing, sessions, capabilities, RGB565 packing, packet examples, acknowledgments,
view lifecycle and navigation. The standalone core client has no third-party
runtime dependencies. Qt is optional and used only by the updater.

DMR1, DMR2 and DMR3 provide volatile 320×240 RGB565 drawing. DMR2 adds
Left/Right navigation; DMR3 adds the Dashboard icon and waiting view. Existing
clients that accept only DMR1/DMR2 must add DMR3 support before using this candidate.
No full framebuffer, atomic swap, guaranteed frame rate
or live animation API for the eight display keys is implemented. Widgets render
on the computer, so new widgets do not require new firmware.

## Firmware and source boundary

Only USB 373f:0001, model 1, hardware revision 1 and exact Main/Dock/Numpad
1.29.0 are supported. [Compatibility and hashes](docs/FIRMWARE.md) define the
image set. Main routing and Dock Clock code change; Numpad remains byte-identical
to stock but is transferred as part of the recorded three-controller sequence.

The project ships extension source and small replacement patches, never
manufacturer firmware or full patched images. Downloads,
restoration copies and update records stay in the user's local XDG state
directory. Maintainer-specific context belongs in ignored `.local/` or the
private lab. Public builds do not depend on the lab.

## Reproduce firmware offline

Requirements: Python 3.11+, `clang`, `ld.lld` and `llvm-objcopy`. The reproduced toolchain is **22.1.8**. Other versions must produce the same exact output hashes or the builder refuses export.

Obtain the three original files yourself; [firmware compatibility](docs/FIRMWARE.md) lists their names, sizes and hashes. From this checkout:

```sh
python3 firmware/dmr3/build.py \
  --main /path/to/MCU0_1.29.0.0.bin \
  --dock /path/to/MCU1_MMD_1.29.0.0.bin \
  --numpad /path/to/MCU2_NPD_1.29.0.0.bin \
  --output ./.local/dmr3-build
```

The output directory must not exist. It contains the verified candidates, stock restoration copies and a manifest. Keep all of these local. The DMR1 and DMR2 builders remain unchanged in `firmware/dmr1/` and `firmware/dmr2/`. See [offline validation](docs/BUILDING.md#rebuild-the-firmware-extension) for the DMR3 instruction checker.

These builders remain offline-only. The desktop uses a compiler-free
patch engine and a separate native transport; see [updater protocol](docs/UPDATER-PROTOCOL.md).
Previous physical trials used an instrumented official Web updater. Recovery
from nonbooting patched code remains unproven.

## Development

```sh
make setup
make doctor
make check
```

[Contributing and PR requirements](CONTRIBUTING.md) · [Build and release workflow](docs/RELEASING.md) ·
[Validation](docs/VALIDATION.md) ·
[Architecture](docs/ARCHITECTURE.md) · [Provenance](docs/PROVENANCE.md)

GPL-3.0-only project source. Built on the QLink work in
[re133/iocenter-linux](https://github.com/re133/iocenter-linux); see
[third-party notices](THIRD_PARTY.md). Independent community project, not
affiliated with or supported by be quiet!.
