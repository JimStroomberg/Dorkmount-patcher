# Troubleshooting

Start with [Installing](INSTALLING.md) for setup and restoration steps.
The app's **Help & details** shows error messages and where it saves local files.

## The keyboard cannot be checked

| Message or symptom | What to try |
|---|---|
| USB access denied | Choose **Set up USB access**, approve the password prompt and reconnect the keyboard. Run the app as your normal user. |
| Another app owns the keyboard | Close Dorkmount, IO Center and browser control tabs. Check for keyboard apps still running in the background. |
| Keyboard or module missing | Attach the screen and number pad and connect the keyboard directly by USB. |
| Unsupported hardware or firmware | Check [the supported model and firmware](FIRMWARE.md). The patcher needs an exact match to prepare the right update. |

## Download or preparation failed

Your keyboard has not been updated at this stage. Check your internet connection
and system date, then try preparing again. Version 0.2.0-beta.1 fixes certificate
lookup in the packaged Linux app. If certificate errors persist, check that your
system's CA certificates are installed and up to date.

The app checks each firmware file before using it. If a file fails verification,
leave the checks enabled and report the error. Previously downloaded, verified
files can be reused offline. Custom certificate settings are covered in
[Building](BUILDING.md#build-the-downloadable-packages).

## Dashboard stays on Waiting…

Waiting… means the keyboard is ready for a widget app to draw on it. The patcher
only adds Dashboard support; it does not provide widgets.
[Dorkmount](https://github.com/JimStroomberg/Dorkmount), the companion app, is
**coming soon**.

If you already have a compatible app, close the updater, select Dashboard on the
keyboard and start that app. Older companions may need an update for DMR3.
Developers can check drawing with the [Python example](../examples/first_pixels.py)
and [developer guide](DEVELOPERS.md).

When a companion stops, its last image may stay on the screen. Reopening Dashboard
shows Waiting… again; the companion then needs to draw a fresh image.

## An update stopped

Keep the keyboard connected and save the error details before trying anything
else. Avoid repeated installation attempts or switching to an unrelated flashing
tool: a missing reply can mean the update's outcome is uncertain.

The app keeps stock firmware copies and a record of each update attempt. Share
the relevant error text and the stage shown when reporting the problem.
Restoration through the app requires a responsive, supported keyboard. Recovery
from a keyboard that no longer starts has not been verified.
[Testing results and limits](VALIDATION.md)

## Report a problem

Open a [GitHub issue](https://github.com/JimStroomberg/Dorkmount-patcher/issues)
with the app version, operating system, what you were doing and the error message.
Let us know whether the keyboard still works. For security problems, please use
[private reporting](../SECURITY.md).

Update files normally live in `~/.local/state/dorkmount-patcher/` (or under your
configured `XDG_STATE_HOME`). This folder contains firmware, restoration copies
and update logs. Please keep the full folder private and check any screenshots
or error excerpts for personal information before sharing them.
