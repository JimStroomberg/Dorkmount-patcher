# Firmware compatibility and release boundary

**Custom graphics require an installed DMR extension.** Version 0.2.0a1 adds
a Linux desktop installer and compiler-free DMR2 patching alongside the original
offline builders. Extension bytes are unchanged; the new native installer has
not yet been tested on hardware. Follow [TESTING.md](TESTING.md) for the trial.

The extension changes one routing byte in Main and reuses the existing Clock renderer space on the Media Dock. The Numpad firmware stays stock. Clock becomes the host dashboard view. Widget changes happen on Linux. The manufacturer version replies remain 1.29.0, so a version string alone cannot establish compatibility. The app checks exact DMR capabilities before drawing; this is a protocol check, not a firmware attestation.

## DMR2: physical view navigation

DMR2 retains the DMR1 drawing request format and Main image, advertises capability magic `DMR\x02`, and routes Clock Left / Right through the existing Profiles notification path. Clock's internal stopwatch/timer navigation is replaced by host view switching. Single Menu / Select inside Clock does nothing; double-click retains the original return to the app selector. Selecting Clock always permits host drawing, regardless of the former Clock subview flag.

DMR2 Dock SHA-256: `676f8f535a1d539fb104a87ecddd3e4ab3772eec15d63b06aa0b6b1608bd5b5e`.

Source and exact-hash offline builder: `firmware/dmr2/`. Use the same build arguments below with `firmware/dmr2/build.py` and a new output directory. This build uses a 288-byte handler and two instruction patches: `0800aee0: 3cd0 → 76d0` (Clock Left / Right) and `08009748: 0128 → 0028` (ignore Clock single-click). No new RAM allocation, flash-writing command or additional Main change is introduced.

Offline validation passed 4,230 graphics transactions (including 500 malformed random inputs), exact frame reconstruction and 96 button/menu instruction cases. Maximum measured graphics stack remains 104 bytes. Physical validation status is summarized in [VALIDATION.md](VALIDATION.md); emulation cannot establish switch timing or USB delivery.

## Exact supported baseline

Official release source: [Dark Mount firmware manifest](https://dfu-release.bequiet.com/fw/dark_mount/index.json). Obtain the original files from the manufacturer's release infrastructure; they are not included in this repository. The builder requires all three exact original images and preserves stock copies in its output for later restoration.

| Image | File / bytes | Stock SHA-256 |
| --- | --- | --- |
| Main | `MCU0_1.29.0.0.bin` / 85,508 | `94d6927103b1a0bdbe8a214e90fb7f0bcc4f891a546ada8f63d0f0d2869c5b70` |
| Dock | `MCU1_MMD_1.29.0.0.bin` / 81,000 | `d2cbc938269e9c2272c3667320c625cdd418f0dda7e079050c45dbc1f6ebb0df` |
| Numpad | `MCU2_NPD_1.29.0.0.bin` / 325,200 | `12a57913e1a3bf4ecddd95a4877d93fbd5fa9b8c9ece988f535f5e81500baf1d` |

Device information must report model **1**, hardware revision **1**, and Main/Dock **1.29.0** before the application tries DMR1. The read-only `03/01` identity query precedes graphics allowlisting; other revisions stop with an explanation. No serial-number query is made.

The only hardware-tested DMR1 outputs are:

- Main: `23fa16e4e5bc0fbc520bdfadc35e3d3d2e2cbbdd45ee34651336ce647a421c02`
- Dock: `bc758017eee8cbf883fec08e2feaa5640eee9eca23fbb5f47b08c11d206e31c4`
- Numpad: exact stock hash above.

## Reproduce offline

Source is in `firmware/dmr1/`. The reproduced build used Clang/LLD/llvm-objcopy **22.1.8**, targeting Cortex-M4 Thumb with `-Oz`. Other toolchains are accepted only if they emit the exact same tested output hashes.

```sh
python3 firmware/dmr1/build.py \
  --main /path/to/MCU0_1.29.0.0.bin \
  --dock /path/to/MCU1_MMD_1.29.0.0.bin \
  --numpad /path/to/MCU2_NPD_1.29.0.0.bin \
  --output ./private-dmr1-build
```

The output must be new. All source hashes, output hashes, sizes and patch extents must match before any candidate is exported. The builder performs no network or USB access and does not flash anything. It does not accept arbitrary firmware revisions or modify MCU addresses supplied by a caller. Binary inputs/outputs are Git-ignored and must not be added to a public release.

## Installation and restoration evidence

The research keyboard was updated using the official Web updater with an instrumented, immutable package selecting the exact tested images. WebHID and independent USB reconstruction verified every transferred byte and successful validation/commit, followed by normal interface return. This involved research tooling and is **not a supported installation flow shipped here**. The official web UI alone does not provide a documented custom-image upload button. Do not assume building files makes an unmodified keyboard usable with Dorkmount.

The native flow is specified in [UPDATER-PROTOCOL.md](UPDATER-PROTOCOL.md): fixed
inputs, exact hashes/ranges, restoration copies, device-requested transfers and
fresh normal-mode verification. Physical installation, restoration and
interruption behavior still need validation. Recovery from nonbooting code
remains unproven. The earlier data-only Clock marker was restored to stock;
restoration from executable graphics code remains untested. Firmware updates
can brick hardware; host backups do not restore keyboard firmware.

For an already compatible Dock, the application uses session management, the read-only `03/01` identity query and the bounded volatile `21/00` drawing command. Unsupported capability replies stop physical output. The controller graphics path does not invoke firmware updates. Its separate display-key image feature does use persistent storage and is unrelated to DMR drawing.

## Protocol and limitations

[PROTOCOL.md](PROTOCOL.md) documents DMR1. Current limitations are one keyboard, the Clock slot, serialized small reports, no atomic frame swap, no view-generation counter; DMR1 lacks physical button forwarding. DMR2 enables Clock Left / Right. A full repaint every five seconds repairs a very fast leave/re-enter between capability probes. The source uses no new global RAM, heap or framebuffer; it calls existing LCD routines and checks the active Clock view before drawing.

The preceding lab validation executed 4,230 transactions through original Dock instructions, checked 104-byte maximum stack use and reconstructed full frames. Real captures and photographs confirmed host pixels and automatic menu return. These findings apply to the tested hardware/images, not all Dark Mount revisions or future official firmware releases.
