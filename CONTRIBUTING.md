# Contributing

Dorkmount-patcher owns firmware source, exact-image patching, the Linux updater UI/transport, and the application-neutral DirectDraw reference client. Dashboard layouts, sensors, widgets and companion-app integration belong to Dorkmount or other clients.

## Workflow and pull requests

1. Branch from current `main` using a short descriptive name, such as `fix/usb-access-message`, `feat/developer-example`, or `build/package-checks`.
2. Keep each PR focused on one problem. Open a draft early if the approach needs discussion. Fork-based PRs are welcome once the repository is public.
3. Run `make setup`, `make doctor` and `make check`. For packaging/dependency changes also run `make package` and `make package-test`; the CI package job uses the same scripts. See [BUILDING.md](docs/BUILDING.md) and [DEPENDENCIES.md](docs/DEPENDENCIES.md).
4. Open the PR against `main` and use the supplied template. Explain the concrete problem, resulting behaviour, validation actually performed, and any meaningful firmware/recovery impact. Use a specific imperative title such as **Fix keyboard detection after reconnect**. The title and description must describe the final change, including after scope changes.
5. Resolve review conversations and wait for **Required checks**. The maintainer reviews the final diff and merges by squash. Request a second reviewer when one is available; the sole maintainer can review and merge their own PR. Do not bypass checks or force-push `main`.

A useful small PR description can be brief:

> The app currently reports a missing keyboard when USB access is denied. Show an access explanation and a setup action instead, so the user can resolve it before preparing firmware.
>
> Validation: permission-denied simulation passes, `make check` passes, and the demo was reviewed visually. No firmware bytes or update commands change. Physical USB behaviour has not been tested.

Include before/after images for visible UI changes when useful. Keep screenshots free of personal data. Distinguish simulations, package installation checks and physical hardware evidence; do not list checks that were not run. New tests should protect meaningful behaviour or failure handling, not merely repeat implementation details. Documentation-only changes need link/content and whitespace checks, not artificial unit tests.

All release work also goes through a PR. `main` contains reviewed development; alpha and stable channels are selected by immutable version tags. See [RELEASING.md](docs/RELEASING.md) for versions, CI, package contents and publishing. Mac Apple Silicon and Bazzite are Coming soon; current package work targets Ubuntu 26.04 and current stable CachyOS, x86-64.

## Firmware and runtime requirements

Qt tests run offscreen. Automated tests never open a real keyboard. Firmware behaviour changes also require original-instruction/emulation validation and a separately authorized hardware experiment. Synthetic tests cannot establish hardware safety.

DMR1/DMR2 builders are preserved unchanged. Reproduce DMR2 with the documented LLVM toolchain and user-supplied stock files, then run `python3 tools/generate_payload.py <verified-build-directory>` to regenerate the compiler-free patch data. This checks complete hashes, preimages and all changed-byte ranges before exporting only replacement patches. For DMR3, use `firmware/dmr3/build.py` and pass `--extension dmr3` to the generator. Run the original-instruction checker described in [BUILDING.md](docs/BUILDING.md#rebuild-the-firmware-extension) against the exact candidate; record its limits and pending hardware checks. Both generation and runtime patching must retain full input/output hash checks, lengths and range guards.

Use Context7 for current library API guidance and official registries/release notes for exact versions. Desktop/build dependency versions are pinned in `packaging/requirements-build.txt`; base/test containers are pinned by digest. Use `make package` for the same Linux container build used by GitHub Actions. No keyboard device is exposed to the build.

## Public and private material

Keep personal plans, test logs, downloaded vendor files, original-code research and local environment notes in ignored `.local/` or the private lab. Public docs must stand alone and must not contain absolute workstation paths. Inspect source archives, wheels and desktop bundles before distribution; `.gitignore` alone does not control package contents. `MANIFEST.in`, package-data rules and `.dockerignore` also enforce this boundary.

The UI must preserve an explicit final install action, block closing while work is active, separate demo from real operations, and never report success without fresh device verification. Update requests are never automatically retried. A failed attempt must retain its local journal and stock copies.

When changing `docs/DEVELOPERS.md`, copy it to `src/dorkmount_patcher/data/developers.md` for the app's offline guide. A test enforces equality. The bundled guide must remain useful before any repository publication.

Do not commit manufacturer images, patched full images, extracted proprietary routines, captures, device serials, photographs, credentials or machine inventories. Public source includes original project code, compatibility hashes, addresses and short instruction checks used by the patcher. Record the origin of new code and evidence. The project is not a clean-room implementation; see [provenance](docs/PROVENANCE.md).

Keep changes specific to an identified hardware revision and exact firmware set. Changing the official version string is not a capability check. Do not broaden support on the basis of version numbers alone.

The repository remains private until the maintainer explicitly chooses publication. Release preparation must include provenance review and a usable installation/restoration procedure; do not attach generated full firmware images to releases.
