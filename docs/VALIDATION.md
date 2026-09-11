# Validation

## Explicit DMR capabilities — 2026-09-11

- The reference client exposes the existing DMR version and named features;
  no firmware bytes, wire format, build target or application version changed.
- `make doctor` and `make check` pass locally: 91 tests and 26 subtests, lint and
  whitespace checks. Synthetic cases cover DMR1/DMR2 outside Clock, unknown
  versions, malformed replies, timeout, capability revocation and rechecking.
- The bundled offline developer guide matches the public guide. Original
  firmware source hashes still pass the extraction checks.

No real keyboard was used. Native installation/restoration and the companion
detection flow after those operations remain unverified on hardware.

## Linux release pipeline — 2026-09-11

- The expanded suite passes 80 tests and 26 subtests on the development host. GitHub Actions compatibility checks pass on Python 3.11 and 3.14; the production Linux build runs Python 3.13.
- Both native package formats are built from the same frozen application. Release checks install them through APT/pacman in Ubuntu 26.04 and the official CachyOS container, check desktop libraries before installing test tools, launch the demo offscreen and under X11/headless Wayland, validate the desktop entry and USB rule, and verify removal. Package-hook errors fail the CachyOS check.
- Local CachyOS installation, all three launch paths and removal pass. Initial clean-Ubuntu testing detected a missing Wayland cursor dependency; the package metadata now declares the Wayland runtime explicitly. The complete installed-package checks must pass on the final PR and again before release publication.
- The release audit passes for the native packages, portable bundle, source archive and wheel. Release metadata records the source commit, dirty-checkout flag and container digests; CI rejects dirty source. The audit excludes private directories, full firmware images, capture files, keys and escaping archive paths.
- `main` requires a PR, the GitHub Actions **Required checks** result, resolved conversations and linear history. Force pushes/deletion are blocked. Alpha tags select prereleases; stable releases remain drafts pending acceptance.

Container checks do not verify a full desktop/logind session or any physical USB
operation. The native hardware trial and recovery limitations below still apply.

## Native updater preview 0.2.0a1 — 2026-09-11

- 68 automated tests pass on the development host, plus 26 parameter subtests. These include compiler-free patch range/hash checks, full production-sized synthetic transfers (85,508 / 81,000 / 325,200 bytes), device-requested windows, malformed ranges, lost ACKs, commit uncertainty, fresh-reconnect verification, GUI consent/failure/demo flow, and complete RGB565 reconstruction.
- The original five extraction/builder cases remain intact. All eight original firmware files retain their extraction hashes.
- LLVM 22.1.8 rebuilt DMR2 from freshly verified official inputs. Every output matches the previously tested hashes. The compiler-free runtime independently produces the same hashes and exact stock restoration images.
- Original Main instructions executed offline with the new Sync payload: the application forwards it to Dock and Numpad and does not send a normal Sync reply before its deferred reset. This supports the explicit connection-transition handling; it does not execute the missing bootloader.
- Context7 supplied current Qt worker/thread and PyInstaller deployment guidance. Exact PySide6 6.11.2 and PyInstaller 6.22.2 versions were checked against their official package records.
- The Linux x86-64 bundle builds on Debian 13, runs the same test suite, and launches its demo with Qt's offscreen display. An extracted bundle also launches in a separate Linux environment with only normal desktop graphics libraries, without Qt or other Python packages installed. A physical CachyOS Wayland/X11 session remains untested. The bundle uses the host's graphics and C++ runtime libraries and requires glibc 2.41+.
- Six command serializers from the current official Web source were executed against synthetic inputs and agree with the native wire layout; that source remains local.
- Manufacturer downloads, full reproduced images, original-code experiments and local logs remain in ignored local state. Public artifacts include only source, original replacement patches, synthetic tests and documentation.

No physical keyboard was available. Native installation, native restoration, real USB access/reconnect, switch behavior and interruption recovery remain pending. A simulation or exact image hash is not proof of those outcomes. Follow [TESTING.md](TESTING.md).

## Initial source extraction, 2026-09-11

The source split preserves all eight DMR1/DMR2 firmware source and builder files byte-for-byte from controller commit `0cba68db5ffc30387649190cb2b0ec1e94e14f00`.

## Checks performed for this repository

- Five offline unittest cases pass, including subcases for both builders and each MCU input: wrong size/content refusal, no compiler/export before identity checks, compiler-failure cleanup, target identity/range consistency, and extraction hashes.
- Both builders ran locally with the exact official 1.29.0 inputs and Clang/LLD/llvm-objcopy 22.1.8. Every generated Main/Dock/Numpad image matches the previously tested output SHA-256 recorded in `firmware/targets/`.
- Each manifest patch preimage hash matches its original input range. Every changed byte is inside a declared range, sizes are preserved, and Numpad is unchanged.
- Official inputs and generated outputs remained in private local research state. No keyboard commands, firmware transfer or new physical test were performed for the extraction.

CI runs only the synthetic/source tests. Reproducing full images requires locally supplied official inputs and the matching toolchain; it is not covered by public CI.

## Earlier lab evidence

The firmware research recorded 4,230 graphics transactions, including 500 malformed-input cases, original-instruction frame reconstruction and a measured maximum graphics stack of 104 bytes. DMR2 additionally passed 96 original-instruction button/menu cases. USB traces verified the exact image transfers on the research keyboard; user observations confirmed custom pixels and automatic resume after returning to Clock. DMR2 Left / Right notifications were captured and drove host view changes.

These are results from one research keyboard and the specific images in [FIRMWARE.md](FIRMWARE.md). The private lab retains the capture, emulation and photograph evidence; these artifacts are not bundled here. Hash reproduction proves equivalence to those images, not universal hardware safety. Restoration from executable DMR code and recovery from nonbooting patched firmware remain unproven.
