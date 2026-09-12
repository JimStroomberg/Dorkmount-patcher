# First hardware trial

Both the new DMR3 Dashboard firmware and native installer have offline coverage
but **have not been tested on a real keyboard**. The earlier DMR2 hardware results
do not validate this candidate. Recovery from nonbooting firmware remains unproven.

## Prepare and install

1. Keep another way to control the computer available; the keyboard disconnects
   during updates. Use stable power and a direct USB connection.
2. Keep the Media Dock and Numpad attached. Close Dorkmount, IO Center, browser
   keyboard-control tabs and background controllers. Automatic-start controllers
   must stay stopped until verification finishes.
3. Use the 0.2.0a3 candidate from this checkout: [run from source or build a local
   package](BUILDING.md). Published alpha.2 packages contain the older Clock-based
   patch. For a local native package, reconnect the keyboard after installation
   and open **Dorkmount Patcher** from the application menu.
   If access is denied, choose **Set up USB access**, approve the password prompt
   and reconnect the keyboard. The portable bundle requires this access setup too.
4. Choose **Check keyboard**, then **Prepare update**. Preparation downloads and
   verifies fixed official files; it sends no update commands.
5. Review the result, acknowledge the test-release risk and choose **Install
   Dashboard**. Firmware changes begin at this point.

Keep power and cables connected throughout. The app requests a sleep inhibitor
and prevents normal closing during work. Allow several minutes, including
finishing and reconnection.

## Acceptance

The app must verify all three parts, Ready/Commit completion, a fresh normal-mode
identity read and the exact DMR3 capabilities. Progress alone is not success.

Close the updater. Before starting a companion, check that the Clock tile is a
dashboard icon and that opening it shows only **Waiting…**. Confirm the icon
survives selection/highlight changes and the other selector tiles remain intact.
The clock/timer/stopwatch submenu should never appear.

Start an updated DMR3-compatible application and confirm that its complete first
frame replaces all waiting text. Check Left/Right switching, double-click Menu to
leave, and Waiting… followed by a full redraw when returning. A single Menu click
must not open Clock controls. Check accent-colour changes, screen idle/wake,
reconnect, ordinary typing, other keyboard apps and the existing images/settings.
No Clock graphics should reappear over companion pixels. Stopping the companion
does not restore Waiting… automatically; DMR3 has no heartbeat.
The updater does not back up or read back all profiles, macros and settings.

Developers can use `examples/first_pixels.py` with the source package installed
in a Python environment. The updater bundle itself needs no Python setup.
Run only one controller or example at a time.

After those checks pass, close the companion app and reopen the updater. Choose
**Restore original keyboard firmware**, repeat Check → Prepare → Restore → Verify,
and physically confirm the original Clock icon and all three built-in functions.
If desired, reinstall Dashboard
and repeat the checks. Restoration requires a responsive supported normal-mode
keyboard; it is not emergency recovery for a nonbooting device.

For companion integration, record manufacturer versions separately from
`dmr_version` and `features`. The reference client should report `dock_directdraw`
and `dock_navigation` plus `dashboard_view` for DMR3 both inside and outside
Dashboard; only `selected` changes. After restoration, reconnect with a fresh session and confirm custom
functions are disabled and the companion offers setup through the patcher. A
dropped capability reply with failed ordinary identity traffic must appear as a
connection problem. These integration checks remain unverified on real hardware.

## Failure handling

Before installation, Help & details explains missing access, unsupported firmware
or a failed download. Correct that issue and check again.

After installation starts, **keep the keyboard connected, preserve the session
folder and stop**. The app disables retry: losing an acknowledgment does not prove
whether the operation occurred. Do not switch images or MCU selections, use an
unrelated flasher or repeatedly resend commands.

The journal identifies the last stage and Commit evidence. Version 1.29.0 alone
cannot establish success because DMR retains that version. Fresh capabilities
and transfer evidence matter. The official updater may recognize an enumerated
update-mode device, but that does not establish recovery from every failed state.

## Local evidence and privacy

Sessions normally live under `~/.local/state/dorkmount-patcher/`, respecting
`XDG_STATE_HOME`. Each attempt retains stock/patched files, a manifest and
`session.json`. The journal records local USB port and update events, not ordinary
keystrokes or a serial-number query.

Keep full firmware, captures and machine-specific notes private. Review diagnostic
excerpts before sharing. Public issues should contain app version, distribution,
stage, error text and whether normal USB returned. Never upload firmware or a
complete session directory. Maintainer checklists/results belong in ignored
`.local/` or the private lab.

## Uninstall

Uninstall with your package manager: `sudo apt remove dorkmount-patcher` on Ubuntu,
or `sudo pacman -R dorkmount-patcher` on CachyOS. The launcher and packaged USB
rule are removed. For the portable bundle, remove the extracted app folder.
Local restoration files remain. Uninstalling does not restore keyboard firmware.

If you used the app's **Set up USB access** fallback, that separate local rule
remains after uninstalling. To remove it:

```sh
sudo rm /etc/udev/rules.d/70-dorkmount-patcher.rules
sudo udevadm control --reload-rules
```

Reconnect afterward. Other rules may independently grant vendor access.
