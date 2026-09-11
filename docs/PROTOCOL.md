# DMR volatile graphics and navigation

Transport uses the upstream QLink session, sequence, CRC16/MODBUS and status checks. Vendor HID is discovered by the normal USB identity `373f:0001` and report-descriptor prefix `0600ff0901a101`. One process must own the command session and sequence stream. The Dorkmount reference controller coordinates its instances with an advisory lock. Other vendor-control programs must be closed.

A read-only `03/01` model/revision/version query must confirm the supported baseline before the graphics command is enabled. It does not query a serial number.

All graphics requests use feature/command `21/00`, a single unfragmented 64-byte QLink report, and payload prefix `44 4d 52 01` (`DMR` + version byte 1). Fields are little-endian. The payload limit is 55 bytes.

| Opcode | Request after prefix/opcode | Reply / bound |
| --- | --- | --- |
| `00` | No fields | 12-byte capability structure: magic[4], width:u16=320, height:u16=240, max_pixels:u8=21, selected:u8=0/1, max_fill:u16=4096 |
| `01` | x:u16, y:u16, width:u16, height:u16, color:u16 | Solid RGB565 rectangle, 1..4096 pixels |
| `02` | x:u16, y:u16, width:u16, height:u16, RGB565 pixels | Exact `2*width*height` bytes, 1..21 pixels |

All rectangles must fit within 320×240 and have positive extents. RGB565 is transmitted least-significant byte first. Successful drawing returns an empty payload and QLink status zero. Malformed requests return status 3; drawing while Clock is inactive returns status 10. Nonzero commands in feature `21` retain the original dispatcher.

In DMR1, the active-view predicate is the original selected-view word at `0x200000f2 == 1` and Clock-ready flag at `0x200000dc == 1`. The receiver uses existing RX/TX buffers and bounded stack. Main forwarding changes address `0x0800f9e4` from `5a` to `38`. Dock overlays the Clock entry at `0x08009a60`, a 296-byte handler at `0x08009a64`, and one call at `0x0800c058`. These addresses belong only to the exact images in [FIRMWARE.md](FIRMWARE.md).

The Dorkmount reference controller queues the latest complete screen and serializes commands. It advances its diff base only after all acknowledgments. An interrupted or failed transfer invalidates that base; resume/reconnect sends a full screen. There is no persistent storage write, double buffer, atomic swap, lease or guaranteed frame rate. DMR1 has no host navigation; DMR2 uses the existing notification queue described below. The transport can display partially updated frames during a transfer.

## DMR2 navigation extension

The drawing request prefix remains `DMR\x01`; DMR2 replies to the same capability query with `DMR\x02` and the unchanged 12-byte layout/bounds. New clients accept only those two known magic values. Older strict DMR1 clients refuse DMR2 output. The DMR2 active predicate is selected view `0x200000f2 == 1`, without the Clock-ready subview flag.

Clock scan index 2 (Left) sends the existing Dock link `80/00` payload `03 01`; index 4 (Right) sends `03 00`. Original Main code translates these into CRC-checked, session-specific QLink `11/02` notifications with sequence zero: `79 00 00 08 04` for Left, `80 00 00 08 03` for Right. Releases do not navigate. The host uses the same QLink owner/reader as graphics and drains its bounded pending queue. No second HID reader, input-key capture, profile write or host key injection is used.

Only DMR2 continuously selected Clock periods deliver events to the enabled-view list; events during observed inactive periods and disconnects are discarded. Because this reuses Profiles' notification format and lacks a view-generation tag, a very fast Clock → Profiles → Clock round-trip entirely between capability probes can still misattribute a Profiles press. Normal exit/re-entry pauses, clears pending navigation and repaints. A future event source/generation field would remove this ambiguity.

Changing enabled views or pressing Left/Right modifies host state only. Menu/Select double-click retains the original selector transition; single-click inside the custom Clock container is ignored.
