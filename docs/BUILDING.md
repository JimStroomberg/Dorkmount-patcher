# Build and develop

End users should download a native package from [Releases](https://github.com/JimStroomberg/Dorkmount-patcher/releases). These instructions are for contributors and other Linux distributions. Source availability does not establish hardware or distribution support.

## Run from source

Use Python 3.11+ with virtual-environment support, Git and Make. Install the desktop libraries and Linux integration tools listed in [DEPENDENCIES.md](DEPENDENCIES.md) through your distribution's package manager first.

```sh
git clone https://github.com/JimStroomberg/Dorkmount-patcher.git
cd Dorkmount-patcher
make setup
make doctor
make demo
make check
```

`make setup` installs the pinned development tools into `.venv`. It does not modify system Python. `make doctor` is read-only and reports missing tools; it is not proof that USB or every Qt plugin works. `make demo` never accesses hardware, downloads firmware or changes permissions. To run the real Linux workflow, use `.venv/bin/dorkmount-patcher`.

From a source archive, the equivalent Python commands also work:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r packaging/requirements-build.txt
.venv/bin/python -m pip install --no-deps --no-build-isolation .
.venv/bin/dorkmount-patcher --demo
```

If the distribution has no compatible PySide6 wheel, follow its Qt/PySide6 packaging instructions. A source build does not automatically support musl, non-systemd desktops, Linux ARM, old graphics stacks or a different keyboard revision. Keep the exact firmware identity/hash restrictions.

## Build the downloadable packages

From a Git checkout, install Docker with Linux containers enabled, Git and Python 3.11+. Docker handles the build tools and native packaging. On macOS, Docker Desktop can run the x86-64 containers; builds are slower under emulation. No local ARM compiler or Qt installation is needed.

```sh
make package
make package-test
```

The output directory must be new so previous files cannot enter a release. To keep an earlier build:

```sh
make package OUT=dist/next-candidate
make package-test OUT=dist/next-candidate
```

The shared PyInstaller application is built using `packaging/Dockerfile`; `tools/package_linux.py` prepares Debian metadata and a `PKGBUILD` around the same files. The official CachyOS container runs `makepkg`. `packaging/platforms.json` pins the test images and declares the remaining system dependencies. No keyboard device is exposed to any container.

Package tests install through APT/pacman, allowing those tools to resolve dependencies. They check the installed desktop entry, USB rule, bundled developer guide, version, offscreen/X11/headless-Wayland demo launch, verified HTTPS preparation and uninstall. Preparation downloads the exact supported official files, verifies all hashes and constructs the existing patch entirely inside the disposable container. Manufacturer bytes are not included in test artifacts. These checks require the official download server to be reachable; they do not run a complete user desktop, logind session or physical keyboard update.

To exercise the same download/preparation path without opening a keyboard:

```sh
dorkmount-patcher prepare --download --output ./prepared-local
```

The output directory must be new and its firmware files must stay private. For offline preparation, use `--stock-dir ./originals` instead of `--download`. HTTPS uses the operating system's trust store, including an explicit `SSL_CERT_FILE` or `SSL_CERT_DIR` override. On Linux, if the bundled OpenSSL's default certificate file is absent and neither override is set, the app loads the system CA bundle at `/etc/ssl/certs/ca-certificates.crt`. Certificate and hostname verification stay enabled.

Before adding display-test tools, the tests check the app's library dependencies
and launch its offscreen demo. The disposable CachyOS test container receives
`SYS_ADMIN` only to support pacman's network-isolated package hooks; the hook
isolation and package-signature checks remain enabled. No host devices or
personal directories are mounted.

`tools/audit_release.py` selects the release assets and writes checksums. For native package inspection it requires `dpkg-deb` and `bsdtar` on Linux; the GitHub workflow provides them. The intermediate rootfs and CachyOS build input are not release assets.

## Rebuild the firmware extension

This is a separate task. The desktop build includes the reviewed compiler-free patch data and does not need manufacturer images or an ARM toolchain.

Follow [FIRMWARE.md](FIRMWARE.md) to reproduce firmware using Clang, LLD and llvm-objcopy 22.1.8 and locally supplied, verified originals. Keep complete input/output images private. Other compiler versions are acceptable only when every resulting image matches the exact reviewed hashes.

## Before contributing

Read [CONTRIBUTING.md](../CONTRIBUTING.md). Use a short-lived branch, open a PR to `main`, and report the checks actually performed. See [RELEASING.md](RELEASING.md) for the separate release workflow.
