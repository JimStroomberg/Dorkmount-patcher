# Branches, candidates and releases

## Branch policy

`main` holds reviewed work. Use short-lived branches and PRs; there is no permanent `alpha` branch. A version tag selects a particular commit and the release channel:

| Channel | Python/app version | Git tag | Debian version | CachyOS version |
|---|---|---|---|---|
| Alpha example | `0.2.0a1` | `v0.2.0-alpha.1` | `0.2.0~alpha1-1` | `0.2.0alpha1-1` |
| Stable example | `0.2.0` | `v0.2.0` | `0.2.0-1` | `0.2.0-1` |

`pyproject.toml` is the source of release metadata. Keep `VERSION` and the runtime `__version__` synchronized; `tools/release_metadata.py` rejects disagreement. It also validates the tag and produces the native version mappings. Never move or reuse a released version/tag. Fixes receive a new version.

## Automated checks

The **Checks** workflow runs for PRs and pushes to `main`. It checks Python compatibility, lint and version consistency, then builds the shared desktop app and both native packages. Production Python 3.13 tests run inside the package build; compatibility checks cover 3.11 and 3.14. Installed-package tests run in the pinned Ubuntu 26.04 and official CachyOS images.

Configure protection for `main` to require a PR, the **Required checks** status, resolved review conversations and linear history, and disallow force pushes/deletion. The sole maintainer may merge their own PR after reviewing the diff and green checks; request another reviewer when one is available. A green workflow is not a hardware approval.

PR workflows have read-only repository permissions and no release credentials. Release permissions exist only in the manually invoked release job. Action versions are pinned by commit, and base/test containers by digest. Updating these pins is a normal reviewed change. Do not run contributor code in a privileged `pull_request_target` workflow or on a personal hardware runner.

## Prepare an alpha

1. Open a PR with the version changes, implementation, validation evidence and `docs/releases/<tag>.md` notes. Complete the archive/provenance review and merge after **Required checks** passes.
2. On `main`, run **Actions → Release candidate → Run workflow** and enter the exact tag, such as `v0.2.0-alpha.1`.
3. The workflow validates the version, builds and tests packages, audits release contents, creates a draft with all assets, then publishes an alpha as a **prerelease**. It is not marked as the latest stable release.
4. Download and test those exact assets with hardware. Retain captures/full journals privately; describe relevant outcomes in reviewed release notes or issues without firmware attachments.

The repository's visibility is a separate maintainer decision. A release in a private repository remains accessible only to users with access. Do not change repository visibility as a side effect of packaging.

## Stable releases

The same workflow prepares a **draft** for a stable version. It never automatically publishes stable releases. Test the actual draft assets on fresh supported desktops and real hardware, document installation/restoration results and remaining limitations, and then publish the existing draft assets. Do not rebuild them after the acceptance test.

Until the native installer has physical installation/restoration evidence, distribute only clearly labelled experimental alpha builds. A successful simulation, packaged demo, exact firmware hash, or Apple notarization does not prove a physical update or recovery path.

## Assets and failed runs

Native `.deb` and `.pkg.tar.zst` packages are the primary downloads. Also retain the portable Linux archive, matching source archive, independent Python wheel, `SHA256SUMS`, artifact manifest, and build metadata. Only the explicit list in `tools/audit_release.py` is uploaded. Manufacturer images, patched complete images, `.local/`, keys, captures and research clones must never be included.

CI artifacts expire quickly to limit storage; GitHub Release assets are the distribution copies. A failed run does not publish a successful alpha. If creation/upload fails after a draft exists, inspect the draft and hashes before resuming. The workflow refuses to overwrite an existing release. Do not delete or replace published assets to hide an error; issue a new version.

No package installation or CI job flashes a keyboard. The end user must explicitly confirm the app's install action.
