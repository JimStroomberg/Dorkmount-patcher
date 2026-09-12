# Releasing

`main` contains reviewed work. Use short-lived branches and pull requests for
changes, and version tags for alpha and stable releases.

## Versions

| Channel | App version | Git tag | Debian version | CachyOS version |
|---|---|---|---|---|
| Alpha | `0.2.0a3` | `v0.2.0-alpha.3` | `0.2.0~alpha3-1` | `0.2.0alpha3-1` |
| Stable | `0.2.0` | `v0.2.0` | `0.2.0-1` | `0.2.0-1` |

Update `pyproject.toml`, `VERSION` and the runtime `__version__` together.
`tools/release_metadata.py` checks that they agree and generates package versions.
Give fixes a new version; published tags and assets stay unchanged.

## Checks

Pull requests require **Required checks**, resolved review conversations and a
squash merge. Keep `main` protected against force pushes and deletion.

CI checks Python 3.11 and 3.14 compatibility and runs the production tests with
Python 3.13 during packaging. It installs the native packages in Ubuntu 26.04 and
CachyOS containers and checks dependencies, startup, firmware preparation and
removal. [Testing](TESTING.md) covers the separate desktop and keyboard checks.

PR workflows have read-only permissions; only the release job can publish assets.
Action versions and container images are pinned. Review pin changes through a PR
and keep contributor code off privileged workflows and hardware runners.

## Prepare and publish

1. Open a PR with the changes, version update and `docs/releases/<tag>.md` notes.
   Use full GitHub links in the notes so they also work on the release page.
   Include test results and any remaining platform limitations. Merge after review
   and **Required checks** passes.
2. On `main`, run **Actions → Release candidate → Run workflow** with the exact
   tag, for example `v0.2.0-alpha.3`.
3. The workflow builds and tests the packages, checks their contents, uploads a
   draft release and downloads the assets again to verify filenames and checksums.
   Both alpha and stable releases stay drafts.
4. Test those downloaded packages on the supported desktops and keyboard using
   [TESTING.md](TESTING.md). Record the package checksums and results in the release
   notes. Keep firmware files and full logs local.
5. Review the notes and publish the existing draft. Keep alphas marked as
   prereleases, with **latest stable** disabled. Publish the tested files without
   rebuilding them.

Continue alpha releases until the supported-platform checks are complete.
[Validation](VALIDATION.md) records CachyOS hardware results and the pending
Ubuntu desktop/USB test.

## Downloads and failed builds

The main downloads are the `.deb` and `.pkg.tar.zst` packages. Also include the
portable Linux archive, source archive, reference-client wheel, `SHA256SUMS`,
artifact manifest and build metadata. `tools/audit_release.py` checks this asset
list and rejects private files, full firmware images and unsafe archive paths.

Debian uses `~` inside alpha package versions for upgrade ordering. Download
filenames use `-` because GitHub normalizes tildes. Checksums use the downloadable
filename.

CI artifacts are temporary; GitHub Release assets are the distribution copies.
If a run stops after creating a draft, inspect its assets and checksums before
continuing. The workflow refuses to overwrite an existing release. Fix errors in
published packages with a new version.
