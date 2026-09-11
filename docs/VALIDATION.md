# Validation — initial extraction, 2026-09-11

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
