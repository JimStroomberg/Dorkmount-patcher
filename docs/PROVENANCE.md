# Source provenance

Copyright 2026 Dorkmount contributors. Original project code is GPL-3.0-only; see [LICENSE](../LICENSE).

The eight files under `firmware/dmr1/` and `firmware/dmr2/` were extracted byte-for-byte from the Dorkmount controller prototype at commit `0cba68db5ffc30387649190cb2b0ec1e94e14f00`. [The extraction manifest](../firmware/provenance.json) records their hashes. That prototype was developed in the private darkmount-lab research workspace; the separate lab repository preserves the earlier history. Compatibility/protocol documentation was adapted during extraction. Target JSON, repository documentation and offline tests were added for this split.

The C handlers and assembly hooks are original project additions. Linker addresses, patch locations, compatibility hashes and short expected-instruction byte checks were derived from analysis of official firmware and recorded lab experiments. They are target-specific facts and patch checks. This project does not claim a clean-room process and does not include copied full manufacturer functions, original firmware files or generated full patched images.

[re133/iocenter-linux](https://github.com/re133/iocenter-linux), studied at revision `6e7a10a27fe5d2e552dec9d7c6adb0ba17191da9`, provided the reverse-engineered QLink discovery/transport foundation used by the lab and controller. It is GPL-3.0-only. Its transport implementation is not vendored into this patcher; DMR firmware extensions are Dorkmount work, not an upstream feature or endorsement.

The manufacturer retains rights in its firmware. The project license applies to project source, not to user-supplied firmware or a full image assembled from it. Generated images and restoration copies stay local. A public release still needs a final provenance/distribution review and must not publish research artifacts or firmware binaries.
