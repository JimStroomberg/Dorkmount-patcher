# Firmware implementation notes

[DEVELOPERS.md](DEVELOPERS.md) is the canonical DirectDraw protocol reference:
framing, sessions, capability layouts, drawing bounds, acknowledgments,
feature/version detection, frame lifecycle and navigation. The updater transport
is separate and documented in [UPDATER-PROTOCOL.md](UPDATER-PROTOCOL.md).
This page retains firmware-specific details without duplicating those contracts.

## Exact image boundary

These addresses apply only to the pinned 1.29.0 images in
[FIRMWARE.md](FIRMWARE.md). The Main routing byte at `0x0800f9e4` changes from
`5a` to `38`. DMR overlays the Clock renderer entry at `0x08009a60` and the
custom dispatcher call at `0x0800c058`. DMR1 uses a 296-byte handler at
`0x08009a64`; DMR2's handler is 288 bytes. DMR3 reuses additional bounded Clock
regions for Dashboard entry, artwork and wrappers; its target manifest lists
all extents and preimages.

DMR1 requires selected view `0x200000f2 == 1` and Clock-ready flag
`0x200000dc == 1`. DMR2/DMR3 require only selected view 1. They use the existing
receive/reply buffers and LCD routines, with no new global RAM or framebuffer.
Nonzero commands in feature `21` retain the original dispatcher.

## Navigation reuse

DMR2/DMR3 Dock scan index 2 (Left) sends link `80/00` payload `03 01`;
index 4 (Right) sends `03 00`. Existing Main code translates them into the
CRC-checked, session-specific QLink notifications described in the developer
guide. Releases do not navigate. The notification format is shared with Profiles
and has no source/generation tag; the documented rapid leave/re-enter ambiguity
still applies. Double-click Menu retains the selector transition; single-click
inside the custom view is ignored.

## Dashboard rendering

DMR3 replaces the former Clock selector tile through full-image/crop wrappers,
without rewriting the external image store. Entry clears the display and draws
Waiting... once. Old Clock-sheet/periodic renders are suppressed, including the
accent callback. The companion must repaint completely after entry. There is no
present command, heartbeat or automatic return to Waiting... after a companion stops.

[Validation](VALIDATION.md) separates original-instruction checks, container
package checks and maintainer-reported hardware results. These notes do not
establish support for another firmware image or guarantee recovery.
