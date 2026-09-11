# Build an app for the Dark Mount screen

DirectDraw lets your application send its own pixels to the keyboard's 320×240
Media Dock screen. Your application owns its layout, data sources and widgets.
Nothing in the protocol requires Dorkmount, Qt, MangoHud or a particular operating
system. The reference connection adapter currently supports Linux.

The keyboard needs the supported DMR1 or DMR2 firmware extension. DMR2 is the
current target. On stock firmware, custom Dock graphics are unavailable.
The extension repurposes **Clock**, including its normal clock/timer content.
Other stock views remain available. The eight display keys are a separate device
feature; this extension does not provide live drawing on them.

## First pixels in Python

Install the source package in a Python 3.11+ environment; the desktop extra is
not needed for clients:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install .
.venv/bin/python examples/first_pixels.py
```

Close all other vendor-HID keyboard controllers, including the updater. Select
**Clock** on the screen. The example opens only the vendor interface, verifies
the supported device, negotiates DMR capabilities, and draws three coloured bands.
It never enables firmware commands or writes persistent images/settings.

```python
from dorkmount_patcher.directdraw import open_keyboard

with open_keyboard() as screen:
    caps = screen.capabilities()
    if not caps["selected"]:
        raise SystemExit("Select Clock on the keyboard screen, then try again.")
    screen.fill(0, 0, 320, 240, 0x0000)
    screen.fill(20, 30, 280, 45, 0xF800)  # red
    screen.fill(20, 95, 280, 45, 0x07E0)  # green
    screen.fill(20, 160, 280, 45, 0x001F) # blue
```

`fill(x, y, width, height, color)` and `pixels(x, y, width, height, data)` split
larger rectangles into the small supported operations. `pixels` accepts tightly
packed, row-major little-endian RGB565 bytes. `frame(data, previous=None)` accepts
exactly 153,600 bytes and returns the acknowledged frame as a possible next diff
base. `capabilities()` refreshes the client's selected-view state.

There is no `present()` or atomic swap. A frame is a sequence of acknowledged
rectangle writes, and partially updated images can be visible while it transfers.

## Implement the transport in any language

Discover USB vendor `0x373f`, product `0x0001`, vendor HID interface **02**, usage
page `0xff00`, with descriptor prefix `06 00 ff 09 01 a1 01`. Do not select the
ordinary keyboard, consumer-input or LampArray interfaces. Linux uses `hidraw`;
WebHID or HIDAPI could provide equivalent platform adapters, but are not supplied
or hardware-validated by this reference package.

One owner must manage the session, request sequence, replies and notifications.
Serialize requests. Stop competing keyboard-control programs. The Linux adapter
uses a per-USB-port patcher lock and the Dorkmount controller's per-HID lock;
unrelated apps are not forced to honour these advisory locks.

Every report has 64 bytes, with no HID report ID. With Linux `hidraw`, prepend
one zero report-ID byte on **writes** (65 bytes passed to `write`). Reads return
the 64-byte frame. With WebHID's equivalent call, report ID is a separate zero
argument and the data would remain 64 bytes.

| Offset | Bytes | Meaning |
| --- | ---: | --- |
| 0 | 1 | `6 + payload_length` |
| 1 | 1 | Fragment field, must be zero for these operations |
| 2 | 1 | Session ID |
| 3 | 1 | Status; requests use 0, successful replies use 0 |
| 4 | 1 | Request ID, 1…255; unsolicited notifications use 0 |
| 5 | 1 | Feature |
| 6 | 1 | Command |
| 7 | 0…55 | Payload |
| after payload through 61 | variable | Zero padding on requests |
| 62 | 2 | CRC16/MODBUS over bytes 0…61, little-endian |

CRC16/MODBUS starts at `0xffff`, uses reflected polynomial `0xa001`, and has no
final XOR. The standard `123456789` check value is `0x4b37`. Increment request
IDs and wrap 255 → 1. Validate frame size, CRC, fragment field, session, command,
request ID and status before consuming a reply. Notifications may arrive before
an ACK; queue them separately. A notification is never a request acknowledgment.

### Open a session and identify the device

1. Send feature/command `01/01`, session 0, payload `nonce:u32le, client_type:u8=2`.
   Use a fresh nonce (the reference uses a random integer from 10000 through 99999).
2. The seven-byte response contains `nonce:u32le, session:u8, state:u8, timeout:u8`.
   Require the same nonce, a nonzero session and active state 1. Use the returned
   session for subsequent requests. Do not take a session ID from a capture.
3. Send `03/01` with an empty payload. The supported reply has
   `model:u16le=1, revision:u8=1, count:u8=3`, then three four-byte versions.
   Version bytes are BCD in build/patch/minor/major order. This target expects
   `00 00 29 01` for each controller. No serial-number query is required.
4. Query DMR capabilities before drawing. A manufacturer version string cannot
   tell you whether the extension is installed.
5. Close a healthy session with `01/02`, empty payload. Close the local device
   descriptor even if that command fails. Long idle applications should close
   and reopen rather than assume their old session is still active; root
   `01/03` keepalive is not implemented in this small reference adapter.

### Negotiate DirectDraw

All requests use feature/command **`21/00`**. Payload starts with
`44 4d 52 01` (`DMR` + byte 1), including on DMR2. Query payload:

```text
44 4d 52 01 00
```

The capability reply is exactly 12 bytes:

| Field | Type | Supported value |
| --- | --- | --- |
| Magic/version | 4 bytes | `44 4d 52 01` or `44 4d 52 02` |
| Width | u16le | 320 |
| Height | u16le | 240 |
| Maximum pixel block | u8 | 21 pixels |
| Clock selected | u8 | 0 or 1 |
| Maximum solid fill | u16le | 4096 pixels |

Example DMR2 reply while Clock is selected:
`44 4d 52 02 40 01 f0 00 15 01 00 10`.
Accept only the implemented versions and limits; unknown values are not a
promise of compatibility. Capability checks are not full firmware attestation.

### Versions and feature detection

Keep three identities separate: manufacturer firmware from `03/01`, the DMR
extension version from the capability reply, and your application's own version.
The current extension leaves all three manufacturer versions at **1.29.0**.
It already reports **DMR1** or **DMR2** independently; no extra firmware field or
query is needed for those versions. DMR identifies the supported extension
contract, not a unique firmware build. Exact image hashes identify the build.

The reference client's `capabilities()` now exposes `dmr_version` and `features`:

| DMR version | `features` | Meaning |
| --- | --- | --- |
| 1 | `dock_directdraw` | Volatile drawing on the 320×240 Media Dock |
| 2 | `dock_directdraw`, `dock_navigation` | The same drawing plus Dock Left/Right notifications |

These names are derived by the client from the two known firmware contracts;
they are **not additional bytes or feature flags in the reply**. Existing return
fields, including `navigation`, remain available. The feature list is a tuple
in Python and becomes an array when saved as JSON.

```python
caps = screen.capabilities()
dmr_version = caps["dmr_version"]
can_draw = "dock_directdraw" in caps["features"]
can_navigate = "dock_navigation" in caps["features"]
```

Use feature membership to enable app functions. `selected=False` means Clock is
inactive; it does not mean support is missing. Capability detection works while
another view is selected. Navigation still needs the event handling below.

A future additive extension should retain existing operations and introduce a
new documented DMR version and feature mapping. Do not accept unknown versions
with a bare `version >= 2` check: validate a known contract first. If future
hardware variants support different features under one version, add explicit
on-device feature discovery before supporting them. No DMR3 contract or live
drawing on the eight display keys is defined or implemented here.

### Detecting removal of the extension

After every reconnect or firmware update, reread manufacturer identity and
negotiate capabilities; discard previous feature state and frame history.
A stock update that overwrites the extension removes its DMR reply, even if the
manufacturer version stays the same. An installation record on the computer is
not evidence that the extension is still present.

Treat a missing reply as **unconfirmed support**, not proof of stock firmware.
A timeout can also mean a lost connection: check ordinary identity traffic
again. Surface permission, busy-device and transport errors separately. Unknown
DMR versions mean unsupported by this client, not unpatched; unsupported
manufacturer versions need a compatibility check, not an automatic downgrade.

`capabilities()` raises on failed or unsupported replies and clears the client's
cached version, features, selection and navigation state, blocking drawing until
a successful check. A previously returned dictionary is only a snapshot; the app
must discard it after failure or disconnect. This client does not reconnect or
launch the updater automatically.

When communication is healthy but custom support cannot be established, a
companion can say **“Custom screen support isn't available. Open Dorkmount
Patcher to check setup options.”** Before handing over, stop all vendor-HID
traffic, close the session, release locks and suspend automatic reconnect until
the updater has finished. Then establish a fresh session and check again.

This detection flow is covered by synthetic tests. Its behaviour after a real
native install/restoration still requires the [hardware trial](TESTING.md).

### Draw rectangles

Coordinates begin at the top left: x increases rightward, y downward. Rectangle
extents must be positive and entirely inside 320×240. All integers are
little-endian. RGB565 packs five red bits, six green bits and five blue bits:

```python
value = ((red >> 3) << 11) | ((green >> 2) << 5) | (blue >> 3)
pixel_bytes = value.to_bytes(2, "little")
```

**Solid fill:** prefix, opcode `01`, x/y/width/height as four u16le values,
color:u16le. At most 4096 pixels per request. Example: red 10×10 square at (0,0):

```text
44 4d 52 01 01 00 00 00 00 0a 00 0a 00 00 f8
```

**Pixel block:** prefix, opcode `02`, x/y/width/height, then exactly
`2 × width × height` pixel bytes. At most 21 pixels per request. Example: red,
green and blue pixels at (0,0), (1,0), (2,0):

```text
44 4d 52 01 02 00 00 00 00 03 00 01 00 00 f8 e0 07 1f 00
```

Successful drawing returns an empty payload with status 0. Status 3 rejects an
invalid request. Status 10 means Clock is not active; stop drawing and query
capabilities until it is selected. Other errors stop the transfer.

## Frame lifecycle and navigation

Keep only the latest pending screen to avoid building a growing output queue.
Poll capabilities while active and while waiting for Clock. After exit/re-entry,
USB reconnect, timeout, lost reply or any interrupted frame, discard the diff
base and repaint fully. Advance the base only after every operation succeeds.
Do not blindly retry writes after losing a reply. Existing Dorkmount polls
capabilities about every 250 ms and repaints fully every five seconds to repair
a quick exit/re-entry missed between probes. These are host policies, not
firmware guarantees.

DMR2 sends Left/Right as QLink **`11/02` notifications**, request ID zero:

| Button | Payload |
| --- | --- |
| Left | `79 00 00 08 04` |
| Right | `80 00 00 08 03` |

Verify CRC, session, zero request/fragment fields and exact payloads. Consume
events through the same QLink reader that owns drawing. Route them to your host
view list only during continuously observed active Clock periods; discard them
on exit, disconnect and re-entry. A reference application can implement this using `qlink.Link` directly.

The notifications reuse the Profiles format. A complete Clock → Profiles → Clock
round trip between probes can misattribute a Profiles button press. DMR2 has
no event-source/view-generation tag to remove that ambiguity. Releases do not
navigate. Single Menu in Clock is ignored; double-click Menu returns to the
stock selector. DMR1 has no host-navigation events.

## Scope and conformance

The host reference modules are `directdraw.py` (renderer-independent sender),
`qlink.py` (framing/session), and `device.py` (Linux adapter). Importing them does
not open a keyboard. The update engine is separate and is never enabled by
`open_keyboard()`.

Run `pytest tests/test_directdraw.py tests/test_protocol.py` for capability,
pixel-reconstruction, bounds, session, CRC and notification tests. They use
synthetic receivers and contain no vendor firmware or captures. The protocol
examples above are also asserted by tests.

This is an early reference API, not a stable plugin ABI. No framebuffer, atomic
present, guaranteed frame rate, concurrent clients, bulk streaming, device-side
widgets or live display-key animation is implemented. The recorded roughly
one-second test-pattern transfer is not a general video or full-frame rate.
The wire format is portable; other OS transports and keyboard revisions need
their own validation.
