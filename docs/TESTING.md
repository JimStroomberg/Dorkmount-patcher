# Testing a release

For everyday installation, restoration and failure handling, use
[INSTALLING.md](INSTALLING.md) and [TROUBLESHOOTING.md](TROUBLESHOOTING.md).
[VALIDATION.md](VALIDATION.md) records completed checks and their scope.

## Record the candidate

Record app version, exact package checksum/source commit, OS version, keyboard
model/revision, manufacturer versions and DMR capability version. These identify
different things: an app version or manufacturer reply alone does not attest to
the installed extension. Keep complete firmware, journals and captures private;
publish only the relevant acceptance summary.

## Install and restore

- Install the native package as a normal desktop user. Verify dependencies,
  menu launch, USB rule, official HTTPS download and permission/reconnect flow.
- Close all competing controllers and prevent their automatic reconnect.
- Follow Check → Prepare → Install. Verify all three controllers, Ready/Commit,
  fresh normal-mode identity and the expected DMR3 capabilities.
- Close the updater and check normal typing, existing settings, other keyboard
  apps and display-key operation.
- Restore stock through the native app; confirm the original Clock icon and all
  built-in functions. Reinstall DMR3 and repeat the screen checks.
- Verify app restart, keyboard reconnect and screen idle/wake. Record the precise
  stage and outcome of any interruption experiment so its limits are clear.

## Dashboard and companion

- Confirm the Dashboard icon, all selector highlights and unchanged other tiles.
- Open Dashboard without a companion: only Waiting… should appear.
- Send a complete first frame; no placeholder pixels should remain.
- Check Left/Right, ignored single Menu click, and double-click Menu to leave.
- On re-entry, confirm Waiting… and then a full companion redraw. Check accent
  changes and idle/wake for unexpected Clock graphics.
- Confirm manufacturer versions separately from `dmr_version=3` and features
  `dock_directdraw`, `dock_navigation`, `dashboard_view`. Features remain present
  outside Dashboard; only `selected` changes.
- After stock restoration, reopen a fresh session and confirm that the companion
  disables DirectDraw and offers the patcher. A transport failure must remain a
  connection problem, not a claim that the extension is missing.

## Release checks

Run the required host/build checks and inspect the exact release archives. Test
native packages on every platform claimed as physically verified. CachyOS has
maintainer-confirmed hardware results; Ubuntu 26.04 still needs its real-machine
acceptance. A Linux container launch does not validate a desktop USB session.
Retain precise limitations in the release notes. No automated test should flash
physical hardware.
