# Dependency reference

Native Ubuntu/CachyOS packages bundle Python, PySide6/Qt, the app and its Python dependencies. Their package metadata declares the remaining OS libraries and integration tools, so the package manager can install them. Desktop users should not install Python modules or a compiler themselves.

The authoritative package lists are in [`packaging/platforms.json`](../packaging/platforms.json). The build environment is pinned in [`packaging/requirements-build.txt`](../packaging/requirements-build.txt) and the Docker base image. Release assets include the installed Python package versions and build/image metadata. Repository packages are resolved at build/test time; bit-for-bit reproducibility across changing distribution repositories is not claimed.

## Runtime requirements

| Purpose | Ubuntu package names | CachyOS package names |
|---|---|---|
| C/C++ runtime | `libc6 >= 2.41`, `libstdc++6 >= 14`, `libgcc-s1` | `glibc >= 2.41`, `gcc-libs >= 14` |
| Graphics, X11 and Wayland connection | `libgl1`, `libegl1`, `libxcb1`, `libwayland-client0`, `libwayland-cursor0`, `libwayland-egl1` | `libglvnd`, `libxcb`, `wayland` |
| Font configuration and a known font | `fontconfig`, `fonts-dejavu-core` | `fontconfig`, `ttf-dejavu` |
| Device rules and sleep inhibition | `systemd`, `udev` | `systemd` |
| Explicit administrator prompt for source/portable setup | `pkexec`, `polkitd` | `polkit` |
| Desktop icon integration | `hicolor-icon-theme` | `hicolor-icon-theme` |
| HTTPS trust roots for official downloads | `ca-certificates` | `ca-certificates` |

Use a normal graphical desktop with a working GPU/driver stack, active local session and authorization agent. OS core/graphics libraries are intentionally supplied by the distribution. Additional Qt platform libraries are bundled. The packages install the vendor-interface rule in `/usr/lib/udev/rules.d/`; reconnect the keyboard after installing. They do not open or flash a device in package scripts.

Fontconfig also comes from the distribution so its library matches the system's
font configuration format. The GUI uses the packaged DejaVu Sans font on Linux.

CachyOS x86-64 has maintainer-confirmed hardware results. Ubuntu 26.04 x86-64 has package/container coverage; real-machine verification remains pending. New Ubuntu releases need validation. macOS Apple Silicon and Bazzite are Coming soon; Windows is later. The generic Linux archive retains the same system requirements but does not install dependencies or rules automatically.

## Running from source on other distributions

Install Python 3.11+ and virtual-environment support, plus PySide6 through the documented virtual environment. On Ubuntu, `python3`, `python3-venv`, `git` and `make` provide the basic setup. On Arch-derived systems use `python`, `python-pip`, `git` and `make`.

An unfrozen source environment also needs the Qt platform dependencies that the native bundle normally carries. Common names include `libxkbcommon`, XCB cursor/image/keysyms/render-util/ICCCM/XKB libraries, D-Bus, GLib, fontconfig, FreeType, and OpenGL/EGL. Ubuntu uses names such as `libxkbcommon0`, `libxcb-cursor0`, `libxcb-image0`, `libxcb-keysyms1`, `libxcb-render-util0`, `libxcb-icccm4`, `libxcb-xkb1`, `libxkbcommon-x11-0`, `libdbus-1-3`, and `libglib2.0-0t64`. Other distributions have different names: consult their Qt/PySide6 packages and [Qt's Linux requirements](https://doc.qt.io/qt-6/linux-requirements.html).

Keep Linux `udevadm`, `pkexec` and `systemd-inhibit` available for the current hardware workflow. Alternate init systems and permission mechanisms require an adapter, not merely a dependency rename. Source/portable users can use the app's **Set up USB access** button.

## Build-only and test-only tools

- Desktop development: pytest, Ruff and Python build tools; exact versions are in the build requirements.
- Native packaging: PyInstaller, binutils, dpkg-deb, desktop-file-utils, and CachyOS makepkg. The container build supplies these.
- Installed-package checks: Xvfb, xauth, headless Weston and desktop-file-utils. These are test tools, not end-user requirements.
- Full firmware reproduction only: Clang, LLD and llvm-objcopy 22.1.8. Normal app builds and installations do not need these.
- Optional DMR3 instruction validation: Unicorn 2.1.4 and Capstone 5.0.9, pinned in the `firmware-check` extra. These are contributor tools; they are not required by or bundled into the desktop app.

Dependencies and original license notices are retained in the desktop bundle. See [THIRD_PARTY.md](../THIRD_PARTY.md).
