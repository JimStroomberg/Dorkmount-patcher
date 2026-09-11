# Source provenance

Copyright 2026 Dorkmount contributors. Original project code is GPL-3.0-only; see [LICENSE](../LICENSE).

The eight files under `firmware/dmr1/` and `firmware/dmr2/` were extracted byte-for-byte from the Dorkmount controller prototype at commit `0cba68db5ffc30387649190cb2b0ec1e94e14f00`. [The extraction manifest](../firmware/provenance.json) records their hashes. That prototype was developed in the private darkmount-lab research workspace; the separate lab repository preserves the earlier history. Compatibility/protocol documentation was adapted during extraction. Target JSON, repository documentation and offline tests were added for this split.

The C handlers and assembly hooks are original project additions. Linker addresses, patch locations, compatibility hashes and short expected-instruction byte checks were derived from analysis of official firmware and recorded lab experiments. They are target-specific facts and patch checks. This project does not claim a clean-room process and does not include copied full manufacturer functions, original firmware files or generated full patched images.

[re133/iocenter-linux](https://github.com/re133/iocenter-linux), reviewed at revision `6e7a10a27fe5d2e552dec9d7c6adb0ba17191da9`, provides the reverse-engineered QLink foundation. The 0.2 native transport adapts its framing/session work with explicit attribution in [THIRD_PARTY.md](../THIRD_PARTY.md). DMR extensions and the native updater are independent Dorkmount work, not upstream features or endorsement.

The compiler-free runtime retains the 301-byte DMR2 patch and adds the 616-byte DMR3 patch. DMR3 contains project-owned drawing code, monitor/bar-chart artwork, view wrappers and short hooks. Two trampolines replay the original four-byte renderer prologues before returning to unchanged vendor code. Complete input/output hashes, bounded ranges and source hashes are checked. No full original Clock function or full vendor image is included. The generator is `tools/generate_payload.py`.

The DMR3 instruction checker adapts the project-owned LCD/GPIO emulator from the private lab into a standalone tool. It takes user-supplied images, models external image data with explicit synthetic fixtures and emits local diagnostic previews. It contains no extracted vendor functions or image assets. New firmware source is separate from the unchanged DMR1/DMR2 extraction files.

The new update state machine implements observed protocol facts from the official Web updater and recorded experiments. No manufacturer JavaScript is copied into the project. `directdraw.py` retains the controller's original GPL sender, with a standalone connection helper. The new desktop workflow, simulator, tests and documentation are original project additions. Local research material stays ignored and outside package contents.

The manufacturer retains rights in its firmware. The project license applies to project source, not to user-supplied firmware or a full image assembled from it. Generated images and restoration copies stay local. A public release still needs a final provenance/distribution review and must not publish research artifacts or firmware binaries.
