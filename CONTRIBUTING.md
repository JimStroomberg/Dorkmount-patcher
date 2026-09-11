# Contributing

Dorkmount-patcher contains firmware-extension source and offline patch generation. Host rendering, sensors, widgets and GUI integration belong to the Dorkmount controller. Keep the protocol usable by other host applications.

Run `python3 -B -m unittest discover -s tests -v` before submitting changes. Firmware behavior changes also require original-instruction/emulation validation and a separately authorized hardware experiment. Synthetic tests cannot establish hardware safety.

DMR1 and DMR2 builders are preserved from the tested prototype. The JSON target files describe their constants and patch ranges; the builders remain authoritative. Tests check identity consistency. A future common patch engine must preserve full input and output checks, exact lengths, non-overlapping bounded ranges and refusal before exporting an unrecognized image.

Do not commit manufacturer images, patched full images, extracted proprietary routines, captures, device serials, photographs, credentials or machine inventories. Public source includes original project code, compatibility hashes, addresses and short instruction checks used by the patcher. Record the origin of new code and evidence. The project is not a clean-room implementation; see [provenance](docs/PROVENANCE.md).

Keep changes specific to an identified hardware revision and exact firmware set. Changing the official version string is not a capability check. Do not broaden support on the basis of version numbers alone.

The repository remains private until the maintainer explicitly chooses publication. Release preparation must include provenance review and a usable installation/restoration procedure; do not attach generated full firmware images to releases.
