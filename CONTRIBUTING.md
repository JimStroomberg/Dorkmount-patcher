# Contributing

Bug reports, documentation fixes and code contributions are welcome.
This repository contains the keyboard patcher and DirectDraw reference client.
Widgets and companion-app features belong in
[Dorkmount](https://github.com/JimStroomberg/Dorkmount), which is coming soon,
or another compatible app.

## Getting started

See [Building](docs/BUILDING.md) for setup and [Dependencies](docs/DEPENDENCIES.md)
for the required libraries. For a larger change, opening an issue first is a good
way to discuss the approach before spending time on it.

Fork the repository and create a branch from `main`. Keep each pull request
focused on one improvement; draft PRs are welcome while work is in progress.

Before submitting code, run `make doctor` and `make check`. Packaging or dependency
changes also need `make package` and `make package-test`. For documentation-only
changes, check the wording, links and `git diff --check`.

## Pull requests

Use a descriptive title, such as **Fix keyboard detection after reconnect**.
Explain the problem, what changes and how you checked it. Add a screenshot for
visible UI changes and mention any effect on installation or restoration.
Small changes can have short descriptions.

For example:

> USB permission errors currently look like a missing keyboard. Show an access
> explanation and the setup button so users can resolve the problem.
>
> Checked with the permission-denied test and a demo screenshot. Firmware and
> update commands are unchanged.

Open the PR against `main` and use the template as a starting point. The maintainer
reviews the change after **Required checks** passes and merges by squash. Releases
use version tags; see [Releasing](docs/RELEASING.md).

## Firmware changes

Firmware changes need extra care. Preserve the supported hardware checks,
verified HTTPS downloads, exact image hashes and transfer bounds. Installation requires the user's confirmation,
and success requires a fresh check of the keyboard. Keep demo mode separate from
hardware operations, and preserve stock copies and logs when an update fails.

The DMR1/DMR2 builders are preserved reference versions. Follow
[the firmware build instructions](docs/BUILDING.md#rebuild-the-firmware-extension)
for DMR3 changes, including payload generation and the instruction checker.
Describe hardware tests separately from simulations, with the version, operating
system and results. [Testing](docs/TESTING.md) has the keyboard checklist.

## Documentation and shared files

The [developer guide](docs/DEVELOPERS.md) defines the drawing protocol.
When changing it, also update `src/dorkmount_patcher/data/developers.md`, the copy
shown in the app. Tests check that they match. Installation help belongs in
[Installing](docs/INSTALLING.md) and [Troubleshooting](docs/TROUBLESHOOTING.md).

Keep downloaded or patched firmware, device captures, credentials and personal
notes out of commits. The ignored `.local/` directory is available for local work.
Check screenshots and log excerpts for personal information before sharing them.
Record the source and license of borrowed code or artwork; see
[Provenance](docs/PROVENANCE.md) and [third-party notices](THIRD_PARTY.md).

Please report security problems privately as described in [SECURITY.md](SECURITY.md).
