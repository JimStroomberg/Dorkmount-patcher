# Dorkmount-patcher

Reproducible firmware extensions for the be quiet! Dark Mount.

This project owns the DMR firmware payloads, exact-image builders and graphics protocol. The separate **Dorkmount** Linux controller renders widgets and sends drawing commands. Other host applications can implement the same documented protocol.

Initial source release: **0.1.0a1**. The repository is private while the project is prepared for an open-source release. Project source is GPL-3.0-only; manufacturer firmware is not included or licensed by this project.

## What works today

- **DMR2**: volatile 320×240 RGB565 drawing in the Dock's Clock slot, with Left / Right notifications for host view switching. This is the extension tested on the research keyboard.
- **DMR1**: the earlier graphics-only build, retained for reproduction and compatibility.
- Offline builders that require exact official 1.29.0 images for Main, Media Dock and Numpad, and export only the tested output hashes. Numpad remains unchanged.

The payload draws through existing LCD routines. It does not allocate a full framebuffer, provide atomic frame swaps, or run widgets on the keyboard. Fast drawing on the eight display keys remains research.

## Build locally

Requirements: Python 3.11+, `clang`, `ld.lld` and `llvm-objcopy`. The reproduced toolchain is **22.1.8**. Other versions must produce the same exact output hashes or the builder refuses export.

Obtain the three original files yourself; [firmware compatibility](docs/FIRMWARE.md) lists their names, sizes and hashes. From this checkout:

```sh
python3 firmware/dmr2/build.py \
  --main /path/to/MCU0_1.29.0.0.bin \
  --dock /path/to/MCU1_MMD_1.29.0.0.bin \
  --numpad /path/to/MCU2_NPD_1.29.0.0.bin \
  --output ./private-build/dmr2
```

The output directory must not exist. It contains the verified candidates, stock restoration copies and a manifest. Keep all of these local. To reproduce DMR1, use `firmware/dmr1/build.py` with a different output directory.

**Building does not install firmware.** This repository has no flasher, firmware downloader or USB access. A supported installation and restoration workflow is still needed. The lab used an instrumented official Web updater; the normal official UI has no documented custom-image upload path. Recovery from nonbooting patched code has not been demonstrated. See [installation evidence and limitations](docs/FIRMWARE.md#installation-and-restoration-evidence).

## Development

```sh
python3 -B -m unittest discover -s tests -v
```

Tests run offline with synthetic inputs; they require no firmware files or keyboard. [Validation](docs/VALIDATION.md) distinguishes these checks from exact-image builds and earlier hardware observations.

- [Protocol](docs/PROTOCOL.md): current wire format and limitations.
- [Architecture and next steps](docs/ARCHITECTURE.md): the project boundary and future work.
- [Target manifests](firmware/targets/): supported identities and patch ranges.
- [Contributing](CONTRIBUTING.md) and [source provenance](docs/PROVENANCE.md).

Dorkmount-patcher is an independent community project, not affiliated with or supported by be quiet!.
