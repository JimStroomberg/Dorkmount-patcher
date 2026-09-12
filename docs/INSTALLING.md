# Install, update and restore

This updater only patches your keyboard. Widgets come from a separate compatible
app. [Dorkmount](https://github.com/JimStroomberg/Dorkmount), the companion app,
is **coming soon**; it is not included in this installer.

CachyOS installation and restoration have been confirmed on the supported test
keyboard. Ubuntu 26.04 packages pass container checks; real-machine verification
is still pending. See [compatibility](../README.md#compatibility) and
[validation](VALIDATION.md). Other Linux distributions can [build from source](BUILDING.md).

## Install the desktop app

Download the package for your system from
[Releases](https://github.com/JimStroomberg/Dorkmount-patcher/releases).
Use **0.2.0-beta.1 or newer** for Dashboard. Verify the download against the
release's `SHA256SUMS` if transferring it between computers.

On CachyOS, open a terminal in the download folder:

```sh
sudo pacman -U ./dorkmount-patcher-0.2.0beta1-1-x86_64.pkg.tar.zst
```

On Ubuntu 26.04, open the `.deb` with the system package installer, or use:

```sh
sudo apt install ./dorkmount-patcher_0.2.0-beta1-1_amd64.deb
```

For later releases, use their exact filenames. The package manager installs the
app's required libraries, menu shortcut and USB-access rule. Installing a package
does **not** update the keyboard. Reconnect the keyboard, then launch
**Dorkmount Patcher** from your application menu. The app runs as your normal user.

The portable Linux archive contains the app but does not install system
libraries or device rules. Prefer the native package on CachyOS or Ubuntu.
[Portable/source dependencies](DEPENDENCIES.md)

## Add Dashboard

1. Connect the keyboard directly by USB, with its screen and number pad attached.
   Keep stable power and another way to control the computer available.
2. Close Dorkmount, IO Center, browser keyboard-control tabs and background
   controllers. Keep their automatic reconnect/startup stopped until verification finishes.
3. Leave **Add Dashboard to my screen** selected and choose **Check keyboard**.
4. Choose **Prepare update**. The app downloads and verifies the supported
   official files and prepares stock restoration copies. This does not flash the keyboard.
5. Read the result, acknowledge the update risk and choose **Install Dashboard**.
   Keep power and cables connected while the app installs and verifies the update.
6. After success, close the updater. Select the dashboard icon on the keyboard
   and start a compatible widget app. **Waiting…** stays on screen until the app draws.

If access is denied, choose **Set up USB access**, approve the administrator
prompt and reconnect the keyboard. The app itself does not need to run as root.
Internet access is needed for the initial official download; verified cached
files can be reused offline. The updater refuses unsupported hardware/firmware.

Left/Right changes companion views; double-click Menu returns to the selector.
Dashboard replaces the Clock/timer/stopwatch submenu. When you close the widget
app, its last image may stay on the screen. Reopening Dashboard shows Waiting…
again. Older companion apps may need updating to work with Dashboard.

## Restore the original keyboard functions

Close the companion and reopen Dorkmount Patcher. Choose **Restore original
keyboard firmware**, then **Check keyboard → Prepare update → Restore original
firmware**. Keep everything connected until fresh verification finishes.
The original Clock icon and built-in functions should return.

Restoration writes the exact supported stock 1.29.0 set. It requires a responsive,
supported keyboard. It is not an emergency recovery tool for a device that no
longer starts. The app does not back up every profile, macro or configuration setting.
If an update stops, follow [Troubleshooting](TROUBLESHOOTING.md#an-update-stopped).

## Uninstall the desktop app

On CachyOS use `sudo pacman -R dorkmount-patcher`; on Ubuntu use
`sudo apt remove dorkmount-patcher`. For a portable archive, remove its extracted
app folder. Uninstalling the app does not undo the keyboard extension or remove
local restoration files. Restore the keyboard first if that is your intention.

A rule installed separately by **Set up USB access** remains after package
removal. To remove only that fallback rule:

```sh
sudo rm /etc/udev/rules.d/70-dorkmount-patcher.rules
sudo udevadm control --reload-rules
```

Reconnect afterward. Other device rules may independently grant access.
