# ESP32 firmware — the serial contract

**Source of truth:** `github.com/mairuu/esp-motor-firmware` @ `b0b762b` (main).
Read from that tree directly, not from memory. This file is the summary the
ROS side needs.

The ESP32 is **not** a ROS 2 node and does **not** use micro-ROS. A host-side
`ros2_control` hardware interface translates `/cmd_vel` and `/odom` to and from
this protocol.

---

## Wire format

**57600 baud, 8N1.** One command letter, optional space-separated arguments,
terminated by **carriage return** (`\r`). Bare `\n` is ignored rather than
answered, so a host sending CRLF gets one reply, not two.

| Cmd | Args | Reply | Meaning |
|---|---|---|---|
| `e` | — | `<left> <right>` | Accumulated encoder counts |
| `r` | — | `OK` | Zero both encoders, reset the PID |
| `o` | `<pwm_l> <pwm_r>` | `OK` | Raw PWM, −255..255. **Bypasses the PID.** |
| `m` | `<ticks_l> <ticks_r>` | `OK` | Closed-loop target, **ticks per PID frame** |
| `u` | `<Kp>:<Kd>:<Ki>:<Ko>` | `OK` | Replace PID gains (colon-separated) |

Anything else replies `Invalid Command`. A malformed `u` leaves the gains
untouched.

### Boot banner

On reset the board prints one line before anything else:

```
# boot reset=1 encoders=ok
```

`reset=1` is `ESP_RST_POWERON`. `encoders=FAIL` means the PCNT units would not
configure — a pin problem, see the pin conflict below. **The host must discard
this line on first connect.** Garbage before it is the ROM bootloader logging at
115200 regardless of our baud rate; that is expected, not a fault.

---

## The unit that matters

`m` takes **ticks per PID frame**, and the PID frame is **1/30 s**
(`PID_RATE_HZ = 30`). It is a rate, not an increment — the host does not have to
send at 30 Hz for the target to mean the same thing.

```
ticks_per_frame = ω_rad_s × ticks_per_rev / (2π × 30.0)
position_rad    = ticks × 2π / ticks_per_rev
```

`ticks_per_rev` is **not known** and must be measured — see
`records/calibration.md`. The encoders are 4× quadrature (PCNT hardware), so
expect `4 × CPR × gear_ratio`.

Set `controller_manager: update_rate: 30` to match. At 30 Hz an `e` round-trip
plus an `m` write is roughly 720 bytes/s against 5760 available — comfortable.

## Auto-stop

If **2000 ms** pass with no `o` or `m`, the motors stop and the PID is disabled.
So the hardware interface must send `m` **every cycle, including zeros**.
`diff_drive_controller` commands zero on `cmd_vel` timeout, which is exactly the
behaviour we want to reach the motors — keep `cmd_vel_timeout: 0.5` well under
the 2 s window.

---

## Pins — and the conflict

> ✅ **RESOLVED 2026-09-08 — the right encoder is on 23 / 22.** Driven under
> `o` with the robot on blocks, the right encoder returns changing counts with
> `config.h`'s 23/22 flashed, so `config.h` was right and `ARCHITECTURE.md`'s
> "as wired" heading was not. `ARCHITECTURE.md` has been corrected in
> `esp-motor-firmware` `52cf077`; the two files now agree. The table below is
> kept as the record of what the conflict was.

`ARCHITECTURE.md` and `config.h` **disagreed about the right encoder.** The
robot survived, so the physical wiring was ground truth.

| Signal | `config.h` (compiles) | `ARCHITECTURE.md` (claimed "as wired") |
|---|---|---|
| `LEFT_ENC_PIN_A` / `B` | 34 / 35 | 34 / 35 — agree |
| `RIGHT_ENC_PIN_A` / `B` | **23 / 22 — correct** | 32 / 33 — **stale, corrected** |
| `RIGHT_MOTOR_FORWARD` / `BACKWARD` / `ENABLE` | 14 / 12 / 13 | same |
| `LEFT_MOTOR_FORWARD` / `BACKWARD` / `ENABLE` | 25 / 26 / 27 | same |

Notes carried from the firmware repo:

- **GPIO 34/35 are input-only** with no internal pull-ups — the encoder must
  drive them actively. True of typical hall-effect motor encoders. This is also
  why every boot prints **four** `gpio_pullup_en(85): GPIO number error` lines
  before the banner: 4x quadrature gives the left encoder two PCNT channels,
  each pulling up a pulse pin and a control pin. Expected, not a fault — the
  banner still reads `encoders=ok`. A **fifth** would mean something moved onto
  an input-only pad.
- **GPIO12 is the MTDI strapping pin** (selects flash voltage at reset) and is
  wired to `RIGHT_MOTOR_BACKWARD`. Unverified in practice. Test by
  power-cycling five times, not by driving.
- Motor PWM is applied to the **direction inputs** with enables held high, at
  20 kHz via LEDC. That is how the robot is already wired.

## Encoder sign — the one dangerous setting

```c
static const bool LEFT_ENC_INVERT  = false;
static const bool RIGHT_ENC_INVERT = false;   /* was true -- see below */
```

> ⚠ **`RIGHT_ENC_INVERT` was `true` here, and `true` was wrong.** Measured
> 2026-09-08: with `true` flashed, the right encoder counted **backwards
> against its own motor** — precisely the runaway condition. `false`,
> reflashed, both sides agree and both wheels turn forward. The firmware's own
> history argues for the old value (`8b745d3`, *"Invert RIGHT_ENC_INVERT to
> true"*), so `config.h` now carries a dated comment saying not to restore it.
> **Two documents and a commit message said `true`; the robot said `false`.**

**If a wheel's count runs backwards relative to the direction it is driven, the
PID sees the error growing as it pushes and runs away to full PWM.** This is the
highest-consequence check in the whole build.

**Verify by driving, not by hand-rotating.** Hand-spinning tests the encoder
against your arm; what actually destroys the robot is the encoder disagreeing
with its own *motor*. `o` bypasses the PID, so driving under it measures that
directly and cannot run away while doing so — which makes it safe to do
*before* the first `m`, not after. `cap_ws/src/my_bot/scripts/motor_check.py`
does this and refuses to reach `m` until it passes on both sides. The one thing
it cannot see is whether "forward" is forward: two backwards wheels still agree,
and that needs eyes and a motor-pin swap, not an invert flip.

---

## Validation status — 2026-09-08

~~**The firmware has never turned a motor.**~~ It has now. Robot on blocks,
`motor_check.py`:

- [x] `o 50 50` → motors spin (on blocks)
- [x] `m 20 20` → closed-loop PID engages, both sides settle near the
      commanded **600 ticks/s** (20 ticks per 1/30 s frame)
- [x] auto-stop **at 2.0 s**, matching `AUTO_STOP_MS`
- [x] wheels move forward on positive speed — watched, not inferred
- [x] encoder counts increase when wheels move forward
- [x] encoder sign agrees with motor sign — **after** flipping
      `RIGHT_ENC_INVERT` to `false`
- [ ] boots reliably across several power cycles (GPIO12) — **still open**

Trust the protocol. Do not trust the tuning.

## Historical bug to watch for

Under the **previous, ported** firmware (not the current rewrite), any single
command triggered an endless stream of unsolicited output. Never root-caused.
The rewrite removed the most likely cause by construction — encoders use the
PCNT peripheral, so there are no GPIO ISRs at all — and a 3-second quiet window
after `e`/`r` was clean. **But it was never exercised under motor load or with
the PID running**, which is where an ISR/task interaction would show up. If it
recurs, the next step is `esp_reset_reason()` at the top of `setup()` and a
crash-backtrace-capable monitor rather than a bare pyserial read loop.

## Flashing

```bash
sudo fuser -v /dev/esp32     # MUST be empty first
arduino-cli compile --fqbn esp32:esp32:esp32doit-devkit-v1 ~/firmware
arduino-cli upload -p /dev/esp32 --fqbn esp32:esp32:esp32doit-devkit-v1 ~/firmware
```

A `micro_ros_agent` running as root held the port open on the old board and
produced a generic pyserial disconnect error that looked like a permissions
problem but was not. Check `fuser` first, always.
