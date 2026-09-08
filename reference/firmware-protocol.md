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

`ARCHITECTURE.md` and `config.h` **disagree about the right encoder.** The robot
survived, so the physical wiring is ground truth. Resolve on hardware
(`checklists/day-1-foundation.md`, step 5), then make both files agree and push.

| Signal | `config.h` (compiles) | `ARCHITECTURE.md` (claims "as wired") |
|---|---|---|
| `LEFT_ENC_PIN_A` / `B` | 34 / 35 | 34 / 35 — agree |
| `RIGHT_ENC_PIN_A` / `B` | **23 / 22** | **32 / 33** — conflict |
| `RIGHT_MOTOR_FORWARD` / `BACKWARD` / `ENABLE` | 14 / 12 / 13 | same |
| `LEFT_MOTOR_FORWARD` / `BACKWARD` / `ENABLE` | 25 / 26 / 27 | same |

Notes carried from the firmware repo:

- **GPIO 34/35 are input-only** with no internal pull-ups — the encoder must
  drive them actively. True of typical hall-effect motor encoders.
- **GPIO12 is the MTDI strapping pin** (selects flash voltage at reset) and is
  wired to `RIGHT_MOTOR_BACKWARD`. Unverified in practice. Test by
  power-cycling five times, not by driving.
- Motor PWM is applied to the **direction inputs** with enables held high, at
  20 kHz via LEDC. That is how the robot is already wired.

## Encoder sign — the one dangerous setting

```c
static const bool LEFT_ENC_INVERT  = false;
static const bool RIGHT_ENC_INVERT = true;
```

**If a wheel's count runs backwards relative to the direction it is driven, the
PID sees the error growing as it pushes and runs away to full PWM.** Verify by
hand-rotating each wheel *before* the first `m` command, with the robot on
blocks. This is the highest-consequence check in the whole build.

---

## Validation status — incomplete

`ROADMAP.md` step 5 is checked only through `e` and `r`. **The firmware has
never turned a motor.** Outstanding:

- [ ] `o 50 50` → motors spin (on blocks)
- [ ] `m 20 20` → closed-loop PID engages
- [ ] auto-stop after ~2 s
- [ ] wheels move forward on positive speed
- [ ] encoder counts increase when wheels move forward
- [ ] encoder sign agrees with motor sign
- [ ] boots reliably across several power cycles (GPIO12)

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
