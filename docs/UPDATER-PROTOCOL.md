# Update transport implemented by the Linux preview

This is the new native installer's protocol contract, not a recovery guarantee.
The preceding physical experiments used the official Web updater. This native
implementation must still be tested against a real keyboard.

The protocol was checked against the official
[IO Center Web application](https://iocenter.bequiet.com/) on 2026-09-11 and the
recorded lab flow. The implementation contains no copied manufacturer JavaScript.
Downloaded research code, firmware and local comparison results are not published.

QLink framing and session setup are specified in [DEVELOPERS.md](DEVELOPERS.md).
Normal USB identity is `373f:0001`; update mode is `373f:0009`, both vendor HID
interface 02. This preview requires one device and follows the same physical
USB port through both transitions. It starts only from a supported, responsive
normal-mode device with all three modules reporting the exact 1.29.0 baseline.

## Ordered exchange

All update requests use feature `02`, nonzero request IDs, a valid active session,
CRC16/MODBUS and no fragmentation. Notifications have request ID zero; their
command numbers overlap request numbers and cannot be treated as ACKs.

| Request | Command | Payload | Completion |
| --- | ---: | --- | --- |
| Sync | 01 | upgrade_id:u32le, count:u8=3, MCU bytes `00 01 02` | ACK has ID:u32le, count:u8, three resume-state bytes |
| Transfer | 02 | MCU:u8, image_crc:u16le, image_length:u32le | ACK, then device DataRequest notifications |
| WriteData | 03 | MCU:u8, 1…32 image bytes | A separate ACK for each report |
| Validate | 04 | MCU:u8 | ACK and ValidationComplete notification |
| Ready | 05 | empty | ACK and ReadyComplete notification |
| Commit | 06 | empty | ACK and CommitComplete notification, then normal USB return |

The application sends Sync to the normal-mode device after an explicit install
click. The firmware then restarts into update mode. Loss of the normal connection
during this transition allows only waiting for the same port in update mode;
it does not trigger another normal-mode Sync. The updater opens a new session
and synchronizes the same upgrade ID in update mode before transferring data.

The preview requires all three Sync resume states to be Transfer (0). It does
not resume an interrupted or partially completed update. It transfers Main (0),
Dock (1), then Numpad (2); the Numpad image is stock but is included because this
is the all-three-controller sequence validated in preceding experiments.

### Device requests and events

DataRequest (`02/02`, request ID zero) payload is exactly 11 bytes:
`MCU:u8, block_size:u16le, offset:u32le, byte_count:u32le`.
The client requires the current MCU, block size 1…32, a positive byte count,
the next expected contiguous offset, and a range inside the exact verified
image. It sends only that requested range, split by block size, with four
milliseconds of pacing after each acknowledged block. It never speculates
about another requested window.

TransferComplete (`02/03`) and ValidationComplete (`02/04`) carry one MCU byte.
ReadyComplete (`02/05`) and CommitComplete (`02/06`) have empty payloads in the
implemented contract. ResumePointChanged (`02/08`) carries MCU and state bytes;
these are recorded, not used to skip transfer/validation gates. ErrorOccurred
(`02/01`, request ID zero) is fatal even when frame status is zero.

States are Transfer=0, Validate=1, Ready=2, Commit=3, WriteData=4. Unknown states,
unexpected events, invalid CRC/session/fragments, failed status and timeouts
stop the current attempt. No automatic Abort or write replay occurs.

The engine waits for transfer completion before sending Validate and for each
successful validation before starting the next MCU. Ready requires all three
validations. Commit requires both Ready ACK and completion. Commit has a
30-second ACK timeout because a preceding physical run took over seven seconds.
It is never resent if either its ACK or completion is lost.

After completion the engine waits up to 60 seconds for normal USB return, opens
a fresh session and verifies model/revision/all three versions. DMR2 installation
also requires the exact DMR2 capabilities. A stock restoration expects the DMR
endpoint to be absent and rechecks normal identity if the query times out.
No screen test pattern is sent automatically as part of installation.

## Local state and failure handling

Before the first Sync, full stock restoration copies and exact candidate files
are written to a new private session directory. The journal records image hashes,
upgrade ID, port, requested ranges, validation/commit events and final verification.
It does not collect serial numbers or ordinary key input. All these files stay
under the user's XDG state directory, outside the repository and packages.

A sleep/idle inhibitor covers the update; the process releases it on exit. The
GUI prevents ordinary closing and action changes during work. Power loss, process
termination, kernel failure, forced suspend or disconnection can still interrupt
it. The interface never labels an uncertain update successful and disables its
retry button after an install failure. Follow [TESTING.md](TESTING.md) for the
hardware trial and failure evidence.

Known gaps: real bootloader acceptance/timing of this native implementation,
interruption recovery, nonbooting-device recovery, full configuration backups,
independent post-flash firmware readback, other hardware revisions and other OS
adapters. Exact-byte transfer plus device validation and a fresh capability probe
are the available verification; they are not complete firmware attestation.
