# Issues log

Append as things break. One entry per real problem — the point is that the
second occurrence costs minutes, not hours.

**When an entry resolves, add the symptom to
`troubleshooting/symptom-index.md`** so it is findable at 2am.

---

## Template

```
## YYYY-MM-DD · <short title>

**Day / step:**
**Symptom:** what you actually observed, verbatim where possible
**Suspected:** what you thought it was first
**Actual cause:**
**Fix:**
**Time lost:**
**Prevented by:** what would have caught this earlier
```

---

## Known issues carried in from before the board died

### Firmware runaway output — *not reproduced in the rewrite, watch for it*

**Symptom:** under the **previous, ported** firmware, any single serial command
caused an endless stable flood of output afterward (e.g. `4095` repeating,
`Invalid Command` repeating) — always the value the just-processed command
legitimately printed once.

**Ruled out:** TX→RX hardware loopback; the serial-parsing code path itself
(instrumentation showed the read loop was never re-entered).

**Not ruled out:** silent reboot loop, watchdog panic loop, ISR/task interaction
from the old `attachInterrupt` encoders.

**Status:** the rewrite removed the most likely cause by construction — encoders
use the PCNT peripheral, so there are no GPIO ISRs at all. A 3-second quiet
window after `e`/`r` was clean, and `esp_reset_reason()` reported `1`
(`ESP_RST_POWERON`), so no reboot loop. **But it was never exercised under motor
load or with the PID running.**

**If it recurs:** print `esp_reset_reason()` at the top of `setup()`, and use a
crash-backtrace-capable monitor rather than a bare pyserial read loop — a real
crash prints to UART via ROM/IDF logging, bypassing Arduino's `Serial` buffering
entirely, which would explain why instrumentation never saw it coming.

### `micro_ros_agent` holding the serial port

**Symptom:** `esptool` upload fails with a generic pyserial disconnect error that
looks like a permissions problem but is not.

**Cause:** a `micro_ros_agent` running as root (systemd or docker) holding
`/dev/ttyUSB0` open.

**Fix:** `sudo fuser -v /dev/esp32` before every upload. Stop the service.

### GPIO12 strapping pin — unverified

`RIGHT_MOTOR_BACKWARD` is on GPIO12, the MTDI strapping pin, which selects flash
voltage if pulled high at reset. Never confirmed harmless in practice.

**Test:** five power cycles, not a drive test. If it glitches, move the signal to
a free non-strapping GPIO and reflash.

### Nav2 would not install from `packages.ros.org` — *unresolved, will recur*

*Found 8 Sep 2026 by reading `recoverable/mount/.bash_history`, not by
experiencing it. Recorded here so Day 4 does not rediscover it under pressure.*

**Symptom:** on the old board, `sudo apt install -y ros-humble-navigation2
ros-humble-nav2-bringup ros-humble-twist-mux` failed repeatedly — history lines
1391–1431 show it retried ~12 times over what looks like an hour, with
`apt update`, `apt-get update`, `apt list --upgradable` and dropping packages
from the command line one at a time in between. The exact apt error is **not**
in the history (only the commands survive, not their output).

**Escalation path taken, in order:**
1. Retry with/without `twist_mux`, with/without `nav2-bringup` — no.
2. Install a **ros2-snapshot** apt source (`/etc/apt/sources.list.d/ros2-snapshot.sources`,
   staged from a Claude scratchpad) — no; **removed again** along with
   `ros2-snapshot-keyring.gpg` a few lines later. It did not work; do not retry it first.
3. `sudo apt install /home/jetson/nav2_debs/*.deb` — this is the one that stuck.
   `--fix-missing` appears on its own on the next lines, so it was not clean even then.

**Actual cause:** unknown. Most likely a `packages.ros.org` arm64 dependency
skew at that date (Humble sync mid-flight), not something about this robot.

**Consequence for the rebuild:** `~/nav2_debs/` died with the board — it is not
in the NVMe dump. If apt fails again there is no cached fallback, and rebuilding
one means finding the same debs from a working mirror or a snapshot date.

**Prevented by:** installing Nav2 on **Day 1**, not Day 4. That is why
`scripts/bootstrap-ros-humble.sh` installs it in its own non-fatal step and
shouts if it fails — three days of slack instead of none.

**If it fails now:** capture the verbatim apt error into this file first. Then
try, in this order: `apt-cache policy ros-humble-navigation2`; installing
`ros-humble-nav2-*` component packages individually to find which dependency is
unsatisfiable; only then a dated snapshot mirror. Log whatever works.

---

## 2026-09-08 · `/dev/esp32` and `/dev/ydlidar` were crossed

**Day / step:** Day 1 §4 → caught at §5.1
**Symptom:** the first read of `/dev/esp32` never returned. The port streamed
~4.5 kB/s of binary with no command sent — 13568 bytes in 3 s at 57600, ~78% of
line capacity — and never went quiet. No boot banner, no reply to `e`.
**Suspected:** the historical firmware runaway-output bug logged at the top of
this file, or a baud mismatch.
**Actual cause:** the symlinks named the wrong adapters. `make udev` was
answered with the two devices swapped, so `/dev/esp32` pointed at the YDLidar.
What was streaming was lidar frames — `0xAA 0x55` headers, at 115200, read at
57600.

Measured, one port at a time:

| Port path | tty | Device | Evidence |
|---|---|---|---|
| `1-2.2.1` | `ttyUSB1` | **ESP32** | `ets Jul 29 2019 12:21:46`, then `# boot reset=1 encoders=ok` at 57600; `e` → `0 0`; `r` → `OK` |
| `1-2.2.4` | `ttyUSB0` | **YDLidar X2** | 18432 bytes in 2 s at 115200, 236 × `0xAA55`, unprompted, never stops |

**Fix:** swapped the two `KERNELS` values in
`cap_ws/src/my_bot/udev/99-my-bot-serial.rules`, with the evidence in the file
header. ~~Installing needs sudo, so it is the operator's step.~~ **Installed and
verified 8 Sep**, including the replug test: both adapters were returned in the
opposite order, re-enumerated the other way round, and the names did not follow
the numbers.

**Why it was silent, and would have stayed silent:** both adapters are
`10c4:ea60` and both report the same serial, `0001` — non-unique, so
`setup_udev.sh` correctly fell back to USB port path. Port-path rules cannot
tell you they are on the wrong port. Downstream, the failure has no error
message either: the lidar driver would see silence on a port that opens fine,
and `ros2_control` would see lidar frames where it expects counts.

**Time lost:** ~20 min, and only that because the symptom was a hang rather
than a wrong number.

**Prevented by:** three things, all now in place.

1. `setup_udev.sh` now checks the operator's answers against the wire before
   installing and refuses on a contradiction. Its old comment claimed
   autodetection was impossible because "poking the lidar's port spins its
   motor" — wrong on both halves: the motor spins whenever it has power (that
   is why there is a stream), and the X2 has no command interface to poke.
2. `scripts/encoder_report.py` refuses to run against a port that never goes
   quiet, and says why.
3. `scripts/serial_probe.py` caps its drain instead of waiting for quiet
   forever — the hang above was the script, not the hardware.

**Related finding, worth knowing before you debug encoder counts.** Whether
opening the port reboots the ESP32 is **not** fixed. Clearing DTR/RTS before
`open()` only stops pyserial from driving those lines; the kernel drives them
as the tty opens, and whether that is a transition depends on what the previous
close left behind (`hupcl`). Measured both ways within ten minutes: pyserial
with `dtr=False, rts=False` produced a ~506-byte boot burst and the banner on
three consecutive opens, while a plain `bash` redirect after `stty -hupcl`
produced **zero** bytes and no reset. So do not assume encoder counts survive
between two invocations of anything, and do not read a missing banner as a dead
board.


---

## 2026-09-08 · `RIGHT_ENC_INVERT` was documented wrong, and it is the dangerous one

**Day / step:** Day 1 §5.3–5.4
**Symptom:** driven forward under `o 50 50`, the right wheel turned forward
while its encoder counted **down**. Left wheel agreed with itself.
**Consequence if missed:** this is the PID runaway condition exactly. Under
`m`, the controller would have read the error as growing while it pushed, wound
to full PWM and held it. Caught on blocks, before the first `m`.

**Cause:** `RIGHT_ENC_INVERT = true` in the firmware's `config.h`. The robot
needs `false`.

**What makes this one worth writing down** is that *every written source said
`true`*:

| Source | Said |
|---|---|
| `config.h`, as flashed | `true` |
| firmware commit `8b745d3` | *"Invert RIGHT_ENC_INVERT to true"* — a deliberate change |
| `reference/firmware-protocol.md` | `true` |
| The robot | **`false`** |

A commit message that states an intent is not evidence that the intent was
right, and two documents agreeing usually means one copied the other. There is
no way to reach this by reading, only by driving.

**Fix:** `false`, reflashed, retested — both sides agree, both wheels forward,
`m 20 20` settles near the commanded 600 ticks/s with no wind-up.
`esp-motor-firmware` `52cf077`. `config.h` now carries a dated comment saying
not to restore `true` on the strength of the old commit, because someone
reading the history will otherwise "fix" it back.

**Found by:** `cap_ws/src/my_bot/scripts/motor_check.py`, which drives under
`o` — PID bypassed, so it cannot run away while measuring — instead of the
checklist's hand-spin. Hand-spinning tests the encoder against your arm; the
failure is the encoder disagreeing with its own *motor*.

**Same run settled §5.9:** the right encoder is on `config.h`'s **23/22**, so
`ARCHITECTURE.md`'s 32/33 was stale. Both files now agree.

**Time lost:** none — the check exists precisely to find this.
