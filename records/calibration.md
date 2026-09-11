# Calibration record

> **This is the file whose loss cost the most.** Every number goes in here the
> moment it is measured — not at the end of the day. With the date and the
> method, so it can be re-derived or challenged later.
>
> Mirror the headline values into `STATE.md`'s "Live numbers" table.

---

## Devices — `make udev`

**MEASURED on the rebuilt board 2026-09-08.** Supersedes the recovered values
below. Both adapters are `10c4:ea60` Silicon Labs CP210x — **the predicted
VID:PID collision is confirmed** — and both report the **same** serial, `0001`,
which is worse than none: `ATTRS{serial}` matches both, so `setup_udev.sh`
correctly fell back to USB port path on both, exactly as it did before.

> ⚠ **The first version of these rules had the two devices backwards** — the
> port paths below are the corrected ones, established on the wire and not from
> the `make udev` session. Full account in `records/issues.md`.

| | ESP32 | Lidar |
|---|---|---|
| Symlink | `/dev/esp32` | `/dev/ydlidar` |
| Baud | 57600 | 115200 |
| VID:PID | `10c4:ea60` | `10c4:ea60` — **collides** |
| Unique serial? | **no** — reports `0001` | **no** — reports `0001` |
| Old `KERNELS` (2026-09-04) | `1-2.1` | `1-2.2.4` |
| `KERNELS` (2026-09-08, 16:06) | `1-2.2.1` | `1-2.2.4` |
| **Current `KERNELS` (2026-09-08, 19:12)** | **`1-2.2.3`** | **`1-2.2.4`** |
| Resolved to, first boot | `/dev/ttyUSB1` | `/dev/ttyUSB0` |
| Resolved to, **after replug** | **`/dev/ttyUSB0`** | **`/dev/ttyUSB1`** |
| Rules file corrected | [x] repo copy | [x] repo copy |
| Rules file installed | **[x]** 2026-09-08 | **[x]** 2026-09-08 |
| **Survives a replug** | **[x]** 2026-09-08 | **[x]** 2026-09-08 |
| **Confirmed as the right *device*** | **[x]** `# boot reset=1 encoders=ok` at 57600, `e` → `0 0`, `r` → `OK` | **[x]** 18432 bytes / 2 s at 115200, 236 × `0xAA55`, unprompted |

**How to re-confirm in ten seconds**, since the rules match on port path and a
replug into the wrong socket is silent:

```bash
scripts/encoder_report.py --seconds 2     # refuses a port that streams
```

> ⚠ **`1-2.2.4` changed meaning between boards.** It was the **lidar** on the
> old board and it is the **ESP32** on this one. Copying the recovered
> `udev/99-my-bot-serial.rules` across would therefore not fail loudly — it
> would silently name the ESP32 `/dev/ydlidar`. The rules file in
> `cap_ws/src/my_bot/udev/` is the newly generated one; the recovered copy under
> `recoverable/` must never be installed.

**The replug test passed, and it is the one that mattered.** Both adapters
were unplugged and returned in the opposite order on 2026-09-08 17:37. They
re-enumerated the other way round — `ttyUSB0` became `1-2.2.1` and `ttyUSB1`
became `1-2.2.4`, the reverse of the first boot — and **the names did not
follow the numbers**: `/dev/esp32` stayed on `1-2.2.1` and `/dev/ydlidar` on
`1-2.2.4`. That is exactly what a `KERNELS` rule is supposed to do, and until a
replug reverses the enumeration it is untested, because a rule matched on
anything else looks identical while the order happens to hold.

> The symlinks prove the *rules* are right. They do not prove the ESP32 is on
> the port the script thinks — the script probes one adapter at a time, so it
> should be, but the first real confirmation is §5.1's `# boot reset=1
> encoders=ok` banner arriving on `/dev/esp32`. Tick the second row then.

**Method:** `cd ~/cap_ws && make udev` → `scripts/setup_udev.sh` (recovered,
interactive, both devices plugged in). Installs
`/etc/udev/rules.d/99-my-bot-serial.rules`, keeps a copy at
`src/my_bot/udev/99-my-bot-serial.rules`. Access is `GROUP="dialout",
MODE="0660"`.

**Physical sockets are now load-bearing.** Both rules match on port path, so
moving either adapter to another USB socket silently breaks its name. Label the
two sockets.

> **And it happened the same day.** The ESP32 moved socket between 16:06 and
> 19:12 — `1-2.2.1` → `1-2.2.3` — so `make udev` had to be re-run. Verified on
> the wire afterwards: `/dev/esp32` answers `e` → `0 0`, `/dev/ydlidar` streams
> `0xAA55` unprompted. **Any `KERNELS` value written down here is only true
> until someone moves a cable.** Re-derive rather than trusting this table, with
> `make udev` (which now checks answers against the wire) or
> `motor_check.py --seconds 2.5`.

### Camera — 2026-09-08

| | |
|---|---|
| Model | **Logitech HD Webcam C615** (`046d:082c`) |
| Node | `/dev/video0` (`/dev/video1` is the same device's metadata node) |
| Group/mode | `video`, `0660` — `mic-711` **is** in `video` |
| Driver | `cam2image` (`ros-humble-image-tools`), publishes `/image`, **RELIABLE** QoS |

No udev rule needed — it is the only video device. Intrinsics are still lost;
see "Camera intrinsics" below.

## Firmware — `RECOVERY.md` §5.2, §5.3

| | Value | Date |
|---|---|---|
| `LEFT_ENC_INVERT` | **false** | 2026-09-08 |
| `RIGHT_ENC_INVERT` | **false** — was `true`, and `true` was wrong | 2026-09-08 |
| Correct right-encoder pins | **23/22** (`config.h`) | 2026-09-08 |
| GPIO12 boot reliability | **50/50 EN resets clean**; real power cycles still owed | 2026-09-08 |
| Firmware commit after fixes | `52cf077` — **not pushed**, no creds | 2026-09-08 |

**`RIGHT_ENC_INVERT` is the one to be careful about.** It was `true` in the
firmware (commit `8b745d3`, *"Invert RIGHT_ENC_INVERT to true"*), and
`reference/firmware-protocol.md` recorded `true` as well. With `true` flashed,
the right count ran **backwards against its own motor** — the runaway
condition. `false`, reflashed, both sides agree. Two documents and a commit
message all say `true`; the robot says `false`. `config.h` now carries a dated
comment saying not to restore it on that evidence.

### What the board says on boot — 2026-09-08

Day 1 §5.1 and §5.2 pass. Verbatim, on `/dev/ttyUSB1` at 57600 (the port the
corrected rules name `/dev/esp32`):

```
ets Jul 29 2019 12:21:46
rst:0x1 (POWERON_RES...
E (12) gpio: gpio_pullup_en(85): GPIO number error (input-only pad has no internal PU)
E (12) gpio: gpio_pullup_en(85): GPIO number error (input-only pad has no internal PU)
E (20) gpio: gpio_pullup_en(85): GPIO number error (input-only pad has no internal PU)
E (36) gpio: gpio_pullup_en(85): GPIO number error (input-only pad has no internal PU)
# boot reset=1 encoders=ok
```

- **`encoders=ok`** — the PCNT units configured. §5.9's "right encoder reads
  zero" branch is not in play before it is tested.
- `e` → `0 0`, `r` → `OK`. §5.2 done.
- **The four `gpio_pullup_en` errors are expected and harmless.** `(85)` is a
  line number in the IDF's `gpio.c`, not a pin. GPIO 34–39 are input-only pads
  with no internal pull-up, and the firmware asks for one anyway; the call fails
  and the PCNT setup continues. `LEFT_ENC_PIN_A/B` are 34/35 — two pins, two
  calls each (pulse and control), four errors.
- The four errors were **weak early evidence for `config.h`'s 23/22** over
  `ARCHITECTURE.md`'s 32/33, all of them attributable to the left pair while
  ordinary pads like 32/33 would have accepted a pull-up silently. **Now
  confirmed the hard way** — see §5.9 below. `ARCHITECTURE.md` has been
  corrected and the two files agree.

### Motors and encoder signs — 2026-09-08, §5.3–5.7

Robot on blocks. Measured with `cap_ws/src/my_bot/scripts/motor_check.py`,
which drives under `o` (raw PWM, PID bypassed, so it cannot run away) and
watches each side's own count.

| Step | Result |
|---|---|
| 5.3 / 5.4 — encoder vs motor sign | **AGREE both sides**, and both wheels physically forward |
| 5.5 — `o 50 50` | **pass** — both wheels turn forward |
| 5.6 — auto-stop | **pass at 2.0 s**, matching `AUTO_STOP_MS = 2000` |
| 5.7 — `m 20 20` | **pass** — both sides settle near **600 ticks/s**, the commanded rate, no wind-up |
| 5.9 — right encoder pins | **23/22** — returns changing counts as flashed |

`m 20 20` = 20 ticks per 1/30 s frame = 600 ticks/s commanded, so settling
*near* 600 means the PID is closing the loop rather than merely not exploding.

> **Why driving beats hand-spinning here.** The checklist reaches 5.3/5.4 by
> turning each wheel by hand, which tests the encoder against your arm. The
> condition that destroys the robot is the encoder disagreeing with its own
> *motor*. Driving under `o` measures that directly, and cannot run away while
> doing it. What it cannot see is whether "forward" is forward — two backwards
> wheels still agree — so the operator watched the wheels.

### GPIO12 boot reliability — 2026-09-08, §5.8 (partial)

`cap_ws/src/my_bot/scripts/boot_check.py`, 50 EN resets: **50/50 clean**. Every
cycle gave the banner with `encoders=ok`, exactly four `gpio_pullup_en` errors,
`e` → `0 0`, `r` → `OK`, and a boot time of **0.55 s to the centisecond**.

**Why an EN reset is the right test here.** GPIO12 (MTDI) is latched on *chip
reset*, and the strapping pins are re-sampled on an EN reset exactly as on
power-on — the ESP32 cannot distinguish the two, which is why the banner reads
`reset=1` either way. So for the strapping question this is the same test, run
ten times more often than anyone would by hand.

> ⚠ **§5.8 is not closed.** An EN reset does not re-run the supply ramp, so it
> cannot see a brown-out as the motor rail comes up or a regulator that only
> misbehaves from cold. **A couple of real power cycles are still owed.** The
> automation replaces the tedium, not the last word.

## Odometry — `RECOVERY.md` §5.4

### (a) Encoder counts per revolution — **RECOVERED**

Two parameters, not one. In `description/ros2_control.xacro`.

| Param | Value | Note |
|---|---|---|
| `enc_counts_per_rev_left` | **2475** | |
| `enc_counts_per_rev_right` | **2470** | near-equal **on purpose** |

**Why near-equal:** `~/firmware/calibation` recorded `l:2473 r:2556`. That 3.4%
split was **wrong, not imprecise** — counts/rev is a property of the disc and
gearbox, and both sides are the same parts. Only tyre diameter differs, and that
belongs in the radius multipliers.

**Evidence (2026-08-28, `calibrate_straight.py`):** a 3 m closed-loop run ended
**62 cm left** of the line while odom reported 0.0000 m lateral drift. Predicted
drift from the split alone: 57 cm. The split explained **93%** of it.

> ⚠ The xacro comment says "2514 is the mean", but the installed values are
> 2475/2470 — re-derived after the comment was written. **Trust the values.**
> Re-confirm with `calibrate_correct.py` if a straight run drifts.

### (b) Effective wheel radius — **RECOVERED**

**`wheel_radius` = 0.0327 m**

Free diameter is 68 mm (→ 0.034 m), but the loaded rolling radius is ~4%
smaller, and any error in `enc_counts_per_rev_*` lands here too. Calibrated
against a tape with `calibrate_straight.py`, not measured with calipers.

`corrected_radius = wheel_radius × (tape distance / odom distance)`

> **Duplicated in two files and they must agree:** `config/my_controllers.yaml`
> (the copy `diff_drive_controller` actually reads — this one scales odometry)
> and `description/robot_core.xacro` (drives the URDF ground plane and lidar
> height). Change one, change the other, or sim and real diverge.

| Re-verify on new board | Tape | Odom | New `r` | Date |
|---|---|---|---|---|
| | | | | |

### (c) Wheel separation — **RECOVERED**

**`wheel_separation` = 0.25 m** — measured contact-patch to contact-patch,
confirmed. Must equal `2 × wheel_offset_y` (0.125) in `robot_core.xacro`.

Method: `calibrate_spin.py --turns 10`, both directions. A separation error is
symmetric — CW and CCW must give the same size of error, opposite in sign. If
they differ, something asymmetric is dragging and fitting a separation number
would just paper over it.

| Re-verify | Turns | Odom rotated | Residual angle | Implied `sep` | Date |
|---|---|---|---|---|---|
| first run (direction not recorded) | 10 | +3600.32° | **−22°** (under) | **0.25154** | 9 Sep 2026 |
| the other direction | 10 | | | | ⚠ **still to do** |

**Odom over-reports yaw by 0.61 %.** Installed 0.25 → implied **0.25154**, a
1.5 mm change, worth 0.6° on a 90° turn.

> ⚠ **Do not apply this yet — one direction cannot tell the two faults apart.**
> A wheel_separation error is symmetric: CW and CCW under-rotate by the same
> fraction. A wheel *asymmetry* is antisymmetric: it under-rotates one way and
> over-rotates the other. A single run sees only their sum, so this −22° could
> be either, and fitting `wheel_separation` to it would paper over a dragging
> wheel. `calibrate_spin.py`'s own docstring says to do it both ways for exactly
> this reason.
>
> - Other direction also ≈ **−0.6 %** → it is the separation. Apply **0.25154**.
> - Other direction ≈ **+0.6 %** → it is asymmetry. **Leave 0.25 alone** and
>   take it to `calibrate_correct.py --floor-lateral` instead.
>
> Also record which direction each run was; the first one's was not written down.

**This retires the 0.2325 prediction.** Day 2's eyeballed 90° hand-turn implied
`wheel_separation` ≈ 0.2325 — a 7 % error. Ten machine-counted turns say
**0.61 %**, an order of magnitude smaller and the *other* sign of correction.
The eyeball was the error, not the parameter. 0.25 was right.

### (d) Chassis geometry — **RECOVERED**

| Property | Value | Confidence |
|---|---|---|
| `wheel_offset_x` (axle → chassis rear) | 0.255 | measured |
| `wheel_offset_y` | 0.125 | measured (= sep/2) |
| `wheel_thickness` | 0.028 | |
| `chassis_length` | 0.295 | **unverified** — so chassis front edge is derived |
| `chassis_width` | 0.21 | |
| `chassis_height` | 0.138 | |
| `caster_wheel_radius` | 0.038 | measured — **larger than the 34 mm drive wheels** |

> ⚠ The caster is 4 mm taller than the drive wheels. The URDF formula drops its
> contact point onto the drive wheels' ground plane so the *model* stays level.
> **Verify the real robot is level too** — if the caster bolts flat to the same
> deck as the motors, the rear sits 4 mm high and the robot pitches nose-down by
> ~1.3°, tilting the lidar with it.

**Nav2 footprint** (do **not** replace with `robot_radius` — a circle needs
r=0.265 and refuses doorways it fits through):

```
[[0.09, 0.147], [0.09, -0.147], [-0.265, -0.147], [-0.265, 0.147]]
```

## Lidar — **RECOVERED**

> ⚠ **READ THE 11 SEP ENTRY BELOW FIRST — "The lidar is a YDLidar X3 Pro, not
> an X2".** Everything in this section down to that entry was written believing
> the sensor was an X2. The mounting and geometry figures are unaffected and
> still good; the **range figures in this table are not**, and every dated
> dropout note below was measured with `range_max` declared at 12.0 for a
> sensor rated to 8.0.

| | Value | Source |
|---|---|---|
| `lidar_height_above_ground` | **0.22 m** | measured |
| `lidar_offset_behind_axle` | **0.034 m** | measured |
| `laser_frame` in `base_link` | **(−0.034, 0, 0.186)** | derived |
| **Dropout fraction** | ~~~50% of 400 rays~~ **superseded 9 Sep — 350 rays, 27.9%**, see below | bench-measured |
| Measured scan rate | **~11.6 Hz** (config says 10.0) — **confirmed 11.57 Hz, 9 Sep** | measured |
| `reversion` | **true** — puck 0° points at robot BACK | |
| `inverted` | **true** — the unit is CW, ROS needs CCW | ✅ **verified on this board 11 Sep** |
| ~~`range_min` / `range_max`~~ | ~~0.1 / 12.0~~ → **0.12 / 8.0** | ⚠ **corrected 11 Sep with the model** |
| `invalid_range_is_inf` | **false** → dropouts are `0.0`, **below** `range_min` | |
| `/scan` QoS | **BEST_EFFORT** — a RELIABLE subscriber gets nothing, silently | |

> `laser_frame` is the **scan plane**, not the centre of the puck. The visual
> cylinder is drawn centred on it, so the rendered puck is a couple of cm off.

**Both orientation flags must stay `true`, and neither shows up in simulation.**
Failure modes are written out in `reference/nvme-recovery-audit.md`. Verify with
`check_scan_world_fixed.py` after any change.

| Re-verify on new board | Result | Date |
|---|---|---|
| Dropout fraction | **27.9 % of 350 rays** — see below | 9 Sep 2026 |
| Scan rate | **11.57 Hz** — recovered ~11.6 Hz confirmed | 9 Sep 2026 |
| `check_scan_world_fixed.py` | | |

### Dropout re-measured 9 Sep 2026 — and the recovered figure was wrong twice

Method: `scripts/scan_dropout_report.py --scans 100`, robot stationary, lidar
driver alone (no base), ordinary indoor room. 35,000 rays counted.

| | Recovered figure | Measured 9 Sep |
|---|---|---|
| Rays per scan | 400 | **350** |
| Dropout fraction | ~50 % | **27.9 %** |
| Scan rate | ~11.6 Hz | **11.57 Hz** |
| Dropout marker | `0.0` | **`0.0`, all 9,780 of them** — no inf/nan |

**350, not 400.** The driver prints it on startup: `Fixed Size: 720` then
`Single Fixed Size: 350`. 400 was inherited, never counted. `angle_increment`
is 1.032°, which is 350 rays over 360°, so the message and the scan agree.

**Neither is a constant, and the average hides the shape of it.** Per-sector,
0° = ahead:

| Sector | Dropout | Sector | Dropout |
|---|---|---|---|
| −165° BEHIND | 13.3 % | +15° AHEAD | **59.0 %** |
| −135° rear-right | 10.4 % | +45° front-left | **46.3 %** |
| −105° RIGHT | 27.8 % | **+75° LEFT** | **69.6 %** |
| −75° RIGHT | 12.7 % | +105° LEFT | **47.0 %** |
| −45° front-right | **5.3 %** | +135° rear-left | 19.3 % |
| −15° AHEAD | 13.0 % | +165° BEHIND | 12.8 % |

The robot's **left half drops three to five times as many rays as its right
half** in this spot. Per-scan spread was tight (22–32 %), so this is the room,
not noise. An ASCII top-down of the same scans shows a wall ~4 m to the left and
~1 m behind, with open space ahead and right — bearings with nothing inside
`range_max` 12.0 m return `0.0` exactly like a true dropout, and cannot be told
apart from one in the message.

> ⚠ **So 27.9 % is a number about this corner of this room, not about the X2.**
> Re-run it in the room the Day 3 map is made in before it is used for anything.
> It is entered here because it was measured, not because it is the answer.
>
> If the left-side deficit survives a move to open floor, then it is the sensor
> or the mounting — look for chassis clipping the beam on that side, or a dark
> or glazed surface — and that is worth knowing before Day 6 blames the camera.

**What it implies for `detection.min_returns` (Day 6)**, at 27.9 % dropout — a
0.3 m object subtends 17 rays at 1 m (≈12 live), 8 at 2 m (≈6), 6 at 3 m (≈4).
`min_returns: 3` clears 3 m here. At the recovered 50 % it would not have, which
is exactly the trade the Day 3 checklist says to make knowingly.

### Dropout re-measured 10 Sep 2026 — **the deficit is the room, and the sensor is cleared**

Method: same script, 100 scans, robot stationary, **full stack running**
(`make real` + `slam` + `nav`) in a different spot in the same room. This is the
re-run the 9 Sep note asked for.

| | 9 Sep | **10 Sep** |
|---|---|---|
| Rays per scan | 350 | **350** |
| Dropout fraction | 27.9 % | **25.7 %** (8,990 of 35,000) |
| Per-scan spread | 22–32 % | **22.6–28.6 %** |
| Rate | 11.57 Hz | **11.58 Hz** by header stamp |
| Dropout marker | `0.0`, no inf/nan | **`0.0`, no inf/nan** |
| Worst sector | **+75° LEFT, 69.6 %** | **−15° AHEAD, 43.8 %** |
| Best sector | −45° front-right, 5.3 % | −165° BEHIND, 2.3 % |

**The overall fraction is stable at ~26–28 %; the asymmetry is not.** Full
per-sector, 0° = ahead:

| Sector | Dropout | Sector | Dropout |
|---|---|---|---|
| −165° BEHIND | **2.3 %** | +15° AHEAD | 36.9 % |
| −135° rear-right | 27.9 % | +45° front-left | 36.2 % |
| −105° RIGHT | 35.9 % | +75° LEFT | 24.2 % |
| −75° RIGHT | 14.7 % | +105° LEFT | **5.5 %** |
| −45° front-right | 38.1 % | +135° rear-left | 40.2 % |
| −15° AHEAD | **43.8 %** | +165° BEHIND | 4.0 % |

> ✅ **This closes the question the 9 Sep entry left open.** The left-side
> deficit was 46–70 % then and is 5–24 % now; +75° LEFT went 69.6 % → 24.2 %,
> and +105° LEFT went 47.0 % → 5.5 %. **It did not follow the robot.** So it is
> not chassis clipping and not a glazed surface on that side — it was open floor
> beyond `range_max` 12 m, exactly as the ASCII top-down suggested. **The X2 and
> its mounting are cleared, and Day 6 has one fewer thing to blame the camera
> for.**
>
> What follows the *room* now points behind: −165° and +165° both read 2–4 %,
> so the robot is near a wall at its back this time, and the open direction has
> rotated to the front. The number to trust is the **overall 26 %**, which has
> now held across two spots.

**Day 6 `detection.min_returns` is unchanged and now rests on this room's own
figure:** a 0.3 m object subtends 17 rays at 1 m (≈12 live), 8 at 2 m (≈6), 6 at
3 m (≈4). **`min_returns: 3` still clears 3 m.**

> ⚠ Note the sector spread is what bites, not the mean. At −15° AHEAD's 43.8 %,
> that 3 m object drops to ~3.4 live returns — right on the threshold. An object
> dead ahead at 3 m is the marginal case, and dead ahead is where the robot
> drives.

### The two orientation flags — **VERIFIED ON THIS BOARD 2026-09-11**

**Both were inherited, and neither had ever been checked on this hardware.**
`reversion` and `inverted` describe how the puck is **bolted on**, not how the
sensor behaves, so `true` is only correct while the mounting is. The NVMe audit
calls them the most expensive thing in the dump; until today they were trusted,
not measured.

**Method:** `scripts/check_scan_bearing.py`, written 10 Sep for this. Robot
stationary, nothing commanded, an object placed ~0.5 m away in a known
direction. Each flag combination gives a different bearing, so two placements
settle the pair:

| Object placed | correct | `reversion` wrong | `inverted` wrong | both wrong |
|---|---|---|---|---|
| IN FRONT | 0° | 180° | 0° | 180° |
| to its LEFT | +90° | −90° | −90° | +90° |

**Measured:**

| Placement | Readings | Verdict |
|---|---|---|
| **in front**, 0.55 m | **+1.5°, −0.5°, +2.6°** | ~0° → **`reversion: true` is CORRECT** |
| **robot's left**, 0.53 m | **+91.3°, +89.2°** | ~+90° → **`inverted: true` is CORRECT** |

**Both stay `true`.** They are now measured on this board, not inherited.

> **Why this needed a new script.** `check_scan_world_fixed.py` rotates the
> robot and checks the scan stays world-fixed. That catches `inverted` — a
> mirrored scan counter-rotates at twice the yaw rate — but **cannot catch
> `reversion`**, because a scan rotated by π is still world-fixed under
> rotation. `reversion`'s only symptom is that driving *forward* smears the
> map, by which point you are debugging SLAM instead of the sensor. The static
> bearing test catches both in thirty seconds with the robot switched off.

> **Consequence for the 10 Sep forward smear:** `reversion` was the standing
> suspect and is now **eliminated**. The remaining explanation is the
> user-reported speed increase partway through that run — see the note below on
> why a brief fast segment is not brief in its effects.

### A brief fast segment permanently contaminates the map — 2026-09-10

The 10 Sep gate run was driven at `make teleop-nav`'s 0.10 m/s **except for one
short stretch** where the speed was raised. The resulting map smeared on
straight sections, which had been clean at a constant 0.10 m/s on 9 Sep.

**Slowing back down does not undo it.** `slam_toolbox` builds a pose graph, and
scans taken during the fast stretch enter it already sheared — 8.7 cm per sweep
at 0.5 m/s, against 1.0 cm at Nav2's 0.055. Graph optimisation can move a
scan's *pose*; it cannot un-shear the scan itself, so the thick or doubled wall
those scans drew stays drawn. If scan matching latched onto one of them, the
pose error propagates into everything mapped afterwards.

> ⚠ **`teleop_twist_keyboard`'s `q` raises speed permanently**, until `z` lowers
> it, and the current value is only displayed in the teleop terminal — which
> nobody is looking at while watching RViz. `make teleop-nav` now starts at
> `SPEED=0.10` for this reason, but `q` still overrides it at runtime.
>
> **A map built with any fast segment in it is not a valid gate artefact.**
> `~/maps/day3-reference` (10 Sep, 255×557) is kept as a file but must not be
> used as the Day 3 reference.

### The lidar is a YDLidar **X3 Pro**, not an X2 — **CORRECTED 2026-09-11**

**Every document in this project said X2 until today.** `ydlidar.yaml`'s header,
`reference/nvme-recovery-audit.md`, `STATE.md`, the dropout entries above, the
scripts' docstrings, `description/lidar.xacro`. The unit is an **X3 Pro**,
confirmed off the label by the user.

> **There is no software route to the model, which is why this survived so
> long.** The SDK's `YDLIDAR_MODLES` enum contains **no X2 and no X3 at all** —
> `YDLIDAR_X4 = 6` is the only X-series entry. And the
> `Fail to get baseplate device information!` error on every startup, filed in
> the symptom index as expected noise, *is the reason*: single-channel units do
> not answer the device-info query, so `di.model` is never populated. **Read the
> label; nothing will tell you.**

**The driver settings do not change with the model.** Upstream's `X2.yaml` and
`X3.yaml` are byte-identical apart from key ordering — same baudrate,
`lidar_type`, `device_type`, `isSingleChannel`, `abnormal_check_count`,
`fixed_resolution`. What changes is the **physical spec**, and both figures we
had were wrong:

| | Was (X2 values) | **Now (X3 Pro)** | How known |
|---|---|---|---|
| `range_max` | 12.0 m | **8.0 m** | rated spec |
| `range_min` | 0.1 m | **0.12 m** | rated spec |
| `sample_rate` | 3 (3K) | **4 (~4K)** | **measured**, see below |

**Sample rate, measured 11 Sep.** The SDK prints it at startup for
single-channel units because it computes it rather than reading it:

```
Single Fixed Size: 350
Sample Rate: 4.57K
```

Subtract the `+0.5` rounding term the code adds
(`m_SampleRate = count/scan_time/1000 + 0.5`, `CYdLidar.cpp:1111`) for a true
**~4.07K**. It cross-checks against the scan: 350 points/rev × 11.57 rev/s =
4050/s. **X2 and X3 are 3K; ~4K is the X3 Pro.** This was the first
hardware-side evidence that the model was wrong.

> **`350` is also measured, not configured.** `m_FixedSize` for a single-channel
> unit is the observed mean points per revolution rounded to the nearest 10
> (`CYdLidar.cpp:1125`). It will move if the spin rate does.

**Everything downstream that declared a range was corrected with it**, because
all of it was keyed to a sensor that does not exist:

| File | Was | Now |
|---|---|---|
| `config/ydlidar.yaml` | 0.1 / 12.0 | **0.12 / 8.0** |
| `config/mapper_params_online_async.yaml` | `min_laser_range` 0.1, `max_laser_range` 12.0 | **0.12 / 8.0** |
| `config/nav2_params.yaml` ×2 costmaps | `raytrace_max_range` 12.0, `obstacle_max_range` 10.0 | **8.0 / 6.5** |
| `description/lidar.xacro` (Gazebo sensor) | 0.1 / 12.0 | **0.12 / 8.0** |

Nav2 keeps `obstacle` below `raytrace` as it did before (10/12 → 6.5/8): clear
stale obstacles out to the sensor's limit, but only *mark* where the beam is
still dense. At 8 m the 1.032° ray spacing is 14 cm, so a chair leg falls
between rays. `lidar.xacro` matters because its header promises sim and real
agree on range — leaving it at 12 m would have given the simulated robot four
metres the real one does not have.

`range_min` 0.1 → 0.12 discards nothing real: 0.12 m from `laser_frame` is
inside the robot's own footprint (half-width 0.147), so those readings are the
robot seeing itself. The old comment in `mapper_params` advising *against* 0.12
because it "throws away 2 cm of range" had it backwards — 0.1 was claiming 2 cm
the sensor does not have.

### ⚠ What the correction did NOT do — three same-spot A/B runs, 11 Sep

**Dropout has now read 27.9 % (9 Sep), 25.7 % (10 Sep) and ~19 % (11 Sep), and
that downward trend is NOT the config fix.** All three were measured in
different places. Position dominates this figure — the worst sector has already
moved from +75° LEFT to −15° AHEAD between two of those runs. Only a same-spot
A/B says anything about a parameter, so that is what was run:

| Configuration | Dropout | Live returns/scan | Per-scan spread |
|---|---|---|---|
| `range_max` **8.0**, `sample_rate` **4** | **19.0 %** | 284 | 17.1–21.7 % |
| `range_max` **8.0**, `sample_rate` **3** | **18.3 %** | 286 | 15.7–22.6 % |
| `range_max` **12.0**, `sample_rate` **4** | **19.5 %** | 282 | 16.3–22.6 % |

**All three are indistinguishable** — the differences are far inside the
per-scan spread of any one run. Two conclusions, both worth having:

1. **`sample_rate` is genuinely inert on a single-channel unit**, confirmed by
   measurement rather than by reading the code. The SDK measures the rate at
   startup and overwrites the configured value. It is set to 4 because it is
   the number a human reasons from, not because the driver needs it.
2. **`range_max: 8.0` buys nothing in this room**, because the longest return
   here is **6.30 m** — no bearing ever fell in the 8–12 m band, so the declared
   ceiling could not matter. The correction is about being right *where it will
   matter*: a corridor, or the far side of a larger room, where declaring 12 m
   counts genuinely out-of-range bearings as dropouts and tells Nav2 and
   `slam_toolbox` to trust ranges the hardware cannot deliver.

> **The honest summary:** the model was wrong, the config now tells the truth,
> and the demo room is too small for it to show. Do not quote a dropout
> improvement from this change.

## Scan timing and drive speed — **MEASURED 2026-09-09**

Taken off the live stack (`make real` + `make slam` running), by subscribing to
`/scan` and timing 12 consecutive messages.

| Quantity | Measured | Note |
|---|---|---|
| Sweep period | **86.2 ms** → **11.61 Hz** | confirms the 11.57 Hz of earlier that day |
| `header.stamp` age at receipt | **88 ms** | ≈ one full sweep — the stamp is a sweep old before any consumer sees it |
| Rays per scan | **350** | confirms |
| Dropout | **28.3 %** | confirms 27.9 %, same corner of the same room |
| `/scan` QoS | **BEST_EFFORT** (sensor data) | see below |
| `teleop_twist_keyboard` `speed` default | **0.5 m/s** | `teleop_twist_keyboard.py:145` |
| `teleop_twist_keyboard` `turn` default | **1.0 rad/s** | `:146` |

**Derived — motion shear per scan**, being how far the robot travels within one
sweep plus how far it travels during the stamp lag, all of it attributed to a
single pose:

| Speed | Source | Within sweep | Stamp lag | Total |
|---|---|---|---|---|
| **0.5 m/s** | teleop default | 4.31 cm | 4.40 cm | **8.71 cm** |
| 0.10 m/s | `calibrate_straight.py` default | 0.86 cm | 0.88 cm | 1.74 cm |
| 0.055 m/s | Nav2 `max_vel_x` | 0.47 cm | 0.48 cm | 0.96 cm |

**The 9× gap is the finding.** `make teleop` publishes straight at the
controller and **nothing clamps it** — the limits in `nav2_params.yaml` are the
robot's only velocity limit and they are not running during manual driving. So
hand-driving happens at nine times the speed the mapping stack is configured
for, and no warning is emitted.

> ✅ **CONFIRMED 9 Sep.** The 0.10 m/s `calibrate_straight.py` run mapped
> **clean** over the same floor that smeared at teleop speed. The cause was
> motion shear; `reversion` is exonerated for this symptom and stays `true`.
> **Map at Nav2 speeds, or slow teleop down** — there is nothing to calibrate
> for it.

**`/scan` is BEST_EFFORT, and a RELIABLE subscriber receives nothing.** Not an
error — rclpy logs `New publisher discovered ... offering incompatible QoS. No
messages will be received` once, then goes quiet forever, which reads exactly
like a dead topic. Any script reading `/scan` must use
`rclpy.qos.qos_profile_sensor_data`. The scripts in `my_bot/scripts/` already
do; ad-hoc `rclpy` snippets are where this bites.

---

## Camera intrinsics — ⚠ **STILL LOST, must redo**

`robot_params.yaml` and `camera_info.yaml` were in `semantic_objects/config/`,
which the dump did not reach. **This is the one calibration that must be redone.**

The tools that produced them (`capture_checkerboard.py`, `calibrate_camera.py`
in `semantic_objects/tools/`) are also lost — rebuild or use
`ros-humble-camera-calibration`.

**Recovered method** (from `.bash_history`): checkerboard **9×6, 20 mm squares**.

```
python3 capture_checkerboard.py --out /tmp/calib
python3 calibrate_camera.py --dir /tmp/calib --size 9x6 --square 20.0 \
    --write-params ../config/robot_params.yaml --write-info ../config/camera_info.yaml
```

The history shows this was run **many** times — budget for it. One run was kept
as `/tmp/calib-0.4`, suggesting 0.4 px was the error being chased.

| | Value |
|---|---|
| Resolution | 640 × 480 |
| `fx` | |
| `fy` | |
| `cx` | |
| `cy` | |
| Distortion coefficients | |
| **Reprojection error** | ______ px (target < 0.5) |
| Checkerboard | **9×6, 20 mm** |
| Date | |

**Saved to:** `my_bot/config/c615_640x480.yaml`

## Odometry sanity — Day 2 gate, 2026-09-09

**Method:** `scripts/odom_check.py`, robot pushed **by hand** on the floor.
The script commands nothing, so an encoder-sign fault cannot be masked by a PID
correcting for it. Not a calibration — Day 3's `calibrate_straight.py` /
`calibrate_spin.py` do that.

| Move | Odom reported | vs nominal |
|---|---|---|
| Pushed straight ~1 m | **0.980 m** straight-line, yaw change **−0.1°** | **−2.0 %** |
| Turned ~90° in place | **−83.7°**, translation drift **0.9 cm** | **−7.0 %** |

**The important result is the decoupling, not the percentages.** Pushing
produced distance with no yaw; turning produced yaw with no distance. That is
what proves both encoder signs are correct and the differential kinematics are
not scrambled — a swapped or inverted encoder shows up here as a push that
generates yaw, or a turn that walks the robot across the floor.

> **`dy` was +0.441 m during the push, and that is NOT drift.** The odom frame
> was fixed when the controller started, *after* teleop had already turned the
> robot, so the robot's heading sat **26.7°** off odom's x-axis
> (`atan2(0.441, 0.875)`). Yaw stayed flat through the whole push, so it
> travelled straight in its own frame; the motion simply resolves onto both odom
> axes.
>
> ⚠ **The Day 2 checklist is wrong on this point.** It says "push forward 1 m →
> `/odom` x increases by roughly 1 m". That only holds if the robot happens to
> start aligned with odom's x-axis, which it generally will not. **Check the
> straight-line distance**, which is what `odom_check.py` reports.

~~**Prediction to test on Day 3.**~~ **Tested 9 Sep and it did not hold.** The
eyeballed 90° hand-turn implied `wheel_separation` ≈ **0.2325 m**, a 7 % error.
`calibrate_spin.py --turns 10` measured **0.61 %**, and in the opposite
direction — implied **0.25154**, not 0.2325. The 90° was the unreliable part,
exactly as flagged. **0.25 stands.** See §(c) above; the confirming run in the
other direction is still outstanding.

Distance scale at −2 % needs nothing: `wheel_radius` 0.0327 is carrying it well.

## Camera extrinsics — **MEASURED 2026-09-09**

**Single source:** the URDF `camera_link` joint origin, in
`description/camera.xacro`. The node reads TF (**D-10**), so there is no second
copy to drift against. Nothing here came from the lost `robot_params.yaml`.

**Method:** tape measure on the real robot, 9 Sep 2026. Recorded in the terms
actually measured — height above the **floor**, distance from the drive
**axle** — because the chassis box those would otherwise be expressed against
still has an unverified `chassis_length`.

| As measured | Value |
|---|---|
| Lens centre above floor | **0.20 m** |
| Forward of the drive axle | **0.05 m** |
| Off the centreline | **0.03 m** |
| Mount tilt | **~3° UP** |

**Resulting frame** — `camera_link` in `base_link`, derived by xacro and
checked against the same arithmetic that reproduces `laser_frame`'s recorded
`(−0.034, 0, 0.186)`:

| | Value |
|---|---|
| `dx` (forward) | **+0.050 m** |
| `dy` (left) | **+0.030 m** ⚠ side assumed, see below |
| `dz` (up) | **+0.167 m** (= 0.20 above the floor) |
| pitch | **−0.0524 rad** (3° up; negative because +pitch is nose-down) |
| `yaw` | 0 |

**Relative to the lidar:** the camera is **8.4 cm in front** of `laser_frame`
and **2 cm below** it. That gap is not bookkeeping — the semantic layer takes
its *range* from the lidar's scan plane at 0.22 m while taking its *bearing*
from a camera at 0.20 m, so an object the camera sees high in frame may sit
above the plane that measures it.

> ⚠ **`dy`'s magnitude is measured; its sign is assumed.** 3 cm was measured
> off the centreline, but not which side. `+0.03` here means **left**
> (REP-103). If the camera is right of centre this must become `−0.03`.
>
> This will not present as a bug. Every landmark lands 6 cm to one side,
> constant and small, which reads as calibration slop rather than a sign error.
> **Confirm by eye before Day 6**, and fix it in `camera.xacro`, never
> downstream.

**Two frames, and the difference matters.** `camera_link` is the mount
(x-forward, REP-103 body convention); `camera_optical_link` is z-forward,
x-right, y-down, and is the one image geometry lives in. The semantic
projection must look up **`camera_optical_link`**. Both exist, both resolve,
TF reports no gap either way — picking the wrong one is a silent 90° rotation
of every bearing.

**Still lost:** the camera **intrinsics** (`fx`, `fy`, `cx`, `cy`, distortion).
Extrinsics are now measured; intrinsics remain a Day 4 calibration against the
**9×6, 20 mm** checkerboard.

## YOLO environment — `RECOVERY.md` §5.6

> **The most expensive thing here to rediscover.** Write these down the moment
> the three import checks pass.

**Target versions, recovered from `launch/yolo.launch.py`:**

| Package | Was working | **On JetPack 6.1, verified 9 Sep** |
|---|---|---|
| JetPack | 6.2 | **6.1**, L4T 36.4.0 |
| `torch` | **2.11.0** JetPack aarch64+CUDA wheel | **2.11.0** ✅ same |
| `torchvision` | **0.26.0** JetPack aarch64 wheel | **0.26.0** ✅ same |
| `tensorrt` | present, **not in `uv.lock`** | **10.3.0** ✅ |
| `cuDNN` | — | **9.3.0** (`90300` via torch) |
| `ultralytics` | | **8.4.144** |
| `numpy` | — | **1.26.4** (pinned < 2) |
| `cv2` | — | **4.5.4** system, no CUDA |
| Python | **3.10.12** off `/usr/bin` | **3.10.12** ✅ same |

**The recovered torch pair was correct.** Confirmed against the live index
rather than assumed.

**Venv:** `~/yolo/venv`. **Rebuild with `cap_ws/yolo/setup_yolo_venv.sh`**, not
from `requirements-frozen.txt` beside it — a freeze records versions but not
**order** or **exclusions**, and here both matter more than the versions.

> ⚠ **Never run `uv sync`** against this venv. The recovered `uv.lock` pins
> generic PyPI torch **2.13.0** / torchvision **0.28.0** and omits `tensorrt`
> entirely — a sync leaves you with no CUDA and no `.engine` support.

`torch.cuda.is_available()` → **True**, device **Orin**   **Date:** 2026-09-09

Verified with a real `512×512` matmul on device, not just the flag.

### The two traps between "wheels installed" and "torch works"

Neither appears in any pre-existing note; both cost real time on 9 Sep.

**1. `libcudss.so.0` is missing and is not an apt package.** torch 2.11 links
cuDSS; `apt-cache search cudss` returns **nothing** in the Jetson repo. It comes
from the PyPI wheel `nvidia-cudss-cu12`, **but that wheel drags in
`cuda-toolkit` 12.9 and `nvidia-cublas-cu12` 12.9 onto a CUDA 12.6 system** —
the same class of mistake as the `uv.lock` hazard. What was done instead:

```bash
uv pip install --python ~/yolo/venv/bin/python nvidia-cudss-cu12==0.7.1.6
sudo mkdir -p /usr/local/lib/cudss
sudo cp -a ~/yolo/venv/lib/python3.10/site-packages/nvidia/cu12/lib/libcudss*.so* /usr/local/lib/cudss/
echo /usr/local/lib/cudss | sudo tee /etc/ld.so.conf.d/cudss.conf && sudo ldconfig
uv pip uninstall --python ~/yolo/venv/bin/python \
    cuda-toolkit nvidia-cublas-cu12 nvidia-cuda-nvrtc-cu12 nvidia-cudss-cu12
```

Four `.so` files onto the system path; the CUDA 12.9 wheels gone. No
`LD_LIBRARY_PATH` at launch, and nothing that can shadow JetPack's 12.6.

**2. The `numpy<2` warning fired from an unexpected direction.** Not from
installing ultralytics — from **torch's own dependency resolution**, which put
**numpy 2.2.6** in the venv, shadowing the system numpy 1.21 and breaking the
system `cv2` with `numpy.core.multiarray failed to import`. **Pin numpy after
torch, not before.** A freeze cannot express that ordering, which is why the
rebuild is a script.


### Day 2 progress — 2026-09-09

| Item | Value | How |
|---|---|---|
| Python | **3.10.12** `/usr/bin/python3.10` | matches the recovered interpreter |
| `uv` | **0.12.11** aarch64, `~/.local/bin/uv` | astral install script |
| Venv | **`~/yolo/venv`** | `uv venv --system-site-packages --python /usr/bin/python3.10` |
| `rclpy` | imports — `/opt/ros/humble/local/lib/python3.10/dist-packages` | reached through system-site-packages, which is what makes that flag mandatory |
| `cv2` | **4.5.4** | ⚠ Ubuntu stock, **NOT** JetPack's CUDA build |
| `numpy` | **1.21.5** | system; already < 2, so the `numpy<2` pin costs nothing |
| `torch` | not installed | **blocked — see below** |

> ⚠ **RESOLVED the same day.** The JetPack CUDA userspace was **not installed
> at all**: `jetson_release` read CUDA / cuDNN / TensorRT all *Not installed*,
> `find /usr -name 'libnvinfer*'` and `-name 'libcudnn*'` returned nothing, and
> there was no `nvcc` — only a partial CUDA 12.6 runtime under
> `/usr/local/cuda-12.6`.
>
> **Cause:** every line of `/etc/apt/sources.list.d/nvidia-l4t-apt-source.list`
> was commented out, so `nvidia-jetpack` was not a package apt had heard of.
> The re-flash never restored the userspace. Re-enabled the three `r36.4`
> lines (backup at `.bak-20260909`) and installed a targeted set rather than
> the metapackage — **D-15** has the reasoning.

**Installed 2026-09-09, and verified:**

| Library | Version | Note |
|---|---|---|
| CUDA | **12.6.68** | `nvcc` present, `cuda-toolkit-12-6` |
| cuDNN | **9.3.0.75** | |
| TensorRT | **10.3.0.30** | `import tensorrt` works in **both** system python and the venv |
| `nvidia-l4t-dla-compiler` | **36.4.0-20240912212859** | matches `nvidia-l4t-core` exactly |
| OpenCV | 4.5.4, **no CUDA** | `nvidia-opencv` deliberately not installed, D-15 |

> **The one that will cost someone an hour:** `import tensorrt` fails with
> `ImportError: libnvdla_compiler.so: cannot open shared object file` until
> **`nvidia-l4t-dla-compiler`** is installed — the TensorRT Python binding
> links it even though nothing here uses the DLA. Installing it is not enough
> on its own: the file lands in `/usr/lib/aarch64-linux-gnu/nvidia/` and the
> loader cache is stale, so **`sudo ldconfig`** is also required. Both steps,
> then it imports.
>
> Pin it to **36.4.0**, not the repo default 36.4.7 — a 36.4.7 BSP component on
> a 36.4.0 kernel is what the `nvidia-jetpack` metapackage would have forced.

**Torch, confirmed against the wheel index rather than assumed.** The audit said
to verify the recovered pair rather than trust it. Index
`https://pypi.jetson-ai-lab.io/jp6/cu126/` (note `.io`; the `.dev` host does not
resolve) publishes exactly **`torch-2.11.0-cp310`** and
**`torchvision-0.26.0-cp310`** for aarch64 — **the recovered figures are
correct.** That much is verified.

**Install in flight at time of writing** (started 9 Sep ~15:00), by direct wheel
URL so no generic PyPI wheel can substitute itself. The link is slow — measured
**~210 KB/s** — and the index sends no `content-length`, so the finish time is
not predictable. ⚠ **Not yet verified:** `torch.cuda.is_available()`. Fill in
below the moment it passes, and do not treat the pair as working until it does.

Also noted: `jetson_release` calls this an **Orin NX Engineering Reference
Developer Kit**, not an Advantech carrier. Probably an unchanged device-tree
model string in the Advantech BSP, and it changes nothing — the udev paths were
re-derived from the wire on Day 1 rather than inherited — but do not cite
"Advantech" as if the board had confirmed it.

**Recovered performance (JetPack 6.2, must be re-measured on 6.1):**

| | Value |
|---|---|
| Pipeline rate | **15 Hz end to end, camera-limited** |
| `yolo26n` inference @ 640×640 | ~18 ms |
| `yolo26s` inference @ 640×640 | ~27 ms |
| `imgsz` | 640×640 fixed in the engine |
| Camera | `cam2image`, 640×480 @ 15 Hz, **RELIABLE** QoS |

| Re-measured on 6.1 | Value |
|---|---|
| Model | |
| Detection rate | ______ Hz |
| Temp after 5 min | ______ °C |

## Wheel asymmetry — **MEASURED 2026-09-09**

**Method.** `calibrate_straight.py --distance 3.0` (closed loop, 0.10 m/s),
robot parked on a floor-tile line, start and end marked by sighting straight
down through the lidar puck centre. Distance read as **5 tiles at a nominal
600 mm = 3.00 m**. Analysis by `calibrate_correct.py --floor-lateral`.

| | Odom said | Floor said |
|---|---|---|
| straight-line chord | 3.0059 m | 3.00 m (5 tiles) |
| path length walked | 3.0011 m | — |
| lateral drift | **+0.0009 m** (left) | **−0.109 m** (right) |
| yaw drift | −0.09° | **−4.163°** (inferred from lateral) |

**The gap between those two lateral figures is the whole measurement.** The
closed loop steers on *odom* lateral offset and *odom* yaw, so it drives odom's
**estimate** of the path straight. Odom held 0.9 mm; the robot finished 10.9 cm
right. That difference cannot be anything but odometry bias.

**Result: 4.07° of uncorrected yaw bias over 3 m**, `k_r - k_l = -0.005964`,
a **0.60 % wheel asymmetry**.

**APPLIED** to `config/my_controllers.yaml`:

```yaml
left_wheel_radius_multiplier:  1.002982
right_wheel_radius_multiplier: 0.997018
```

Not to `enc_counts_per_rev_*`. Counts per rev is a property of the encoder disc
and the gearbox and both sides are the same parts — only tyre diameter can
differ between wheels. Same reasoning that rejected the old `l:2473 r:2556`
split. **One or the other, never both.** `diff_drive_controller` applies the
multipliers to the wheel **commands** as well as to odometry, so the robot
physically drives straighter rather than merely reporting better.

### Verification run — 2026-09-09, same day

Re-ran the 3 m closed loop with the multipliers installed. **Result: heading
bias gone, a lateral offset that is not curvature.**

| | run 1 (before) | run 2 (after) |
|---|---|---|
| floor lateral | −0.109 m (right) | **+0.08 m (left)** |
| heading change | turned right, same way as the offset | **~0.1°** |

**The heading is the number that matters, and it landed on the prediction.**
Applying `k_r - k_l = -0.005964` buys `D·δ/L` = **4.073°** of heading change, so
run 1's −4.163° should become **−0.090°**. Measured: **~0.1°**. The bias is
corrected.

**The 8 cm is not curvature.** A constant-curvature arc reaching 8 cm over 3 m
*requires* a **3.06°** heading change, and run 2 shows nothing like 3°. What
does produce exactly that offset is a **1.53° error in the lateral reference** —
and 1.53° over 3 m is 8 cm with **zero** heading change.

**Setup used:** the robot's *wheel axis* was aligned on a transverse grout line.
That is a sound **heading** reference — heading comes out perpendicular to the
line. It fixes nothing about where the robot's **centreline** sat relative to
the longitudinal line that drift was then measured against, nor which point on
the robot was read at the end. That is the weak link, and at ±1.5° it is the
same size as the effect being measured.

> **Multipliers left as installed** (1.002982 / 0.997018). The back-off the
> arc-reading would suggest (1.000738 / 0.999248) rests on an inference that the
> measured heading contradicts, and the residual is now inside what
> `slam_toolbox` absorbs by scan matching — the script itself stops recommending
> action below 1°. **Applying a correction on an ambiguous measurement is how a
> good number gets made worse.**

> ⚠ **Run 1's magnitude carried more uncertainty than it was given.** If hand
> parking is good to ±1.5°, that is ±8 cm over 3 m — comparable to the 10.9 cm
> the correction was built from. Run 1 still reads as a genuine curve (its
> heading turned the same way as the offset, which an arc does and a parking
> error does not), but treat 4.07° as approximate.

**If this ever needs re-deriving properly, measure the heading change, not the
lateral offset.** `calibrate_correct.py --floor-heading` takes it directly and
prefers it. A parking error produces **zero** heading change while curvature
produces heading change proportional to distance, so heading is the observable
that separates them. Lay a straightedge along the chassis at the end and read
its offset from a grout line at two points a metre apart: ±2 mm then gives
±0.11°, against ±1.5° for eyeballing a lateral offset.

> The figure was quoted as both 10.9 cm and 10 cm. It barely matters: 10.0 cm
> gives multipliers 1.002731 / 0.997269, a difference of 0.025 %. The 10.9 was
> used.

### `wheel_radius` — deliberately NOT changed

The same run says odom over-reports distance by **+0.17 %** (3.0059 m against
3.0007 m of rolled arc), which would give `wheel_radius` 0.03264.

**Not applied, and the reason matters more than the number.** That correction is
**5.2 mm over 3 m**, and the distance was *counted as five floor tiles* at a
nominal 600 mm — not taped. Real tile pitch including grout varies by several mm
per tile, so a 1 mm/tile error is 5 mm over the run: **the uncertainty in the
measurement is larger than the correction it suggests.** Applying it would be
recording noise as a calibration. `wheel_radius` stays **0.0327**; re-derive
over a longer *taped* run if map scale ever looks wrong.

### What this run does NOT measure: `wheel_separation`

**A straight run cannot test separation, and a spin cannot test this
asymmetry.** In a spin the wheels counter-rotate, so a per-wheel radius error
enters yaw with the *same* sign on both sides and cancels — only the mean radius
and the separation survive, and a radius asymmetry shows up as the robot's
centre *translating* during the spin rather than as residual heading. Driving
straight the wheels co-rotate, so the *difference* shows in yaw and the mean
cancels.

> ⚠ **This contradicts the decision rule recorded in `STATE.md`**, which expects
> a reverse-direction spin to separate the two by sign. If the reasoning above
> holds, a radius asymmetry does **not** flip sign with spin direction, and the
> reverse run should return ≈0.61 % again rather than discriminating. **Check
> the reasoning before spending a driving session on it.** The clean
> decomposition is: straight run → asymmetry (lateral) and mean radius (tape);
> spin → mean radius × separation.

> ~~⚠ **`wheel_separation` 0.25168 remains unprovenanced.**~~ **Recovered
> 10 Sep — see below.** It is the same 9 Sep run, read 2° differently.

### `wheel_separation` — **SETTLED 2026-09-10, by inversion not by driving**

**Method:** no new run. `scripts/calibrate_correct.py` computes the separation
from a spin with a single-parameter formula (lines 280–282):

```
physical = spin_odom_deg + spin_error_deg
ratio    = spin_odom_deg / physical
new_sep  = sep * ratio            # sep read from the INSTALLED my_controllers.yaml
```

With `spin_odom_deg` fixed at the logged **3600.32°** and `sep` at the
then-installed **0.25**, the residual is the only free variable, so the
installed value can be inverted back to the reading that produced it:

| Residual read | physical | ratio | new_sep | |
|---|---|---|---|---|
| −22.0° | 3578.32 | 1.0061481 | 0.2515370 | **0.25154** — the figure in `STATE.md` |
| −23.0° | 3577.32 | 1.0064294 | 0.2516073 | 0.25161 |
| **−24.0°** | **3576.32** | **1.0067108** | **0.2516777** | **0.25168** — the figure **installed** |

**Both figures are the same run.** Same odom reading, same starting 0.25. The
only difference is the floor residual being read as **−24°** when the value was
applied and written down as **−22°** afterwards. Nothing else fits either
number, and −24.0 hits 0.25168 to five decimals exactly. **There was never a
second method or an unrecorded measurement** — which is why this was settleable
from the desk, with the robot switched off.

**Decision: keep 0.25168. Do not churn it to 0.25154.**

| | |
|---|---|
| Gap between the two | **0.00014 m — 0.14 mm, 0.056 %** |
| Yaw error that implies over a 90° turn | **0.05°** |
| …over a full 360° rotation | **0.20°** |

That is far below the precision of reading a chalk mark off a floor after ten
turns: the reading would have to be good to ~1° to justify the fifth decimal,
and the two records differ by 2°. Moving the value would be **recording noise as
a calibration** — the same reasoning that left `wheel_radius` at 0.0327 on 9 Sep
rather than taking the 0.03264 the straight run suggested.

> ✅ **What IS resolved, and it is the part that matters:** 0.25 is wrong. Both
> readings put the separation **0.61–0.67 % high**, i.e. **2.2–2.4° of yaw error
> per full turn**, and 0.25 requires a residual of exactly zero to be right.
> **The correction is real; the fifth decimal place is not.**

**Direction of the run is still unrecorded, and it no longer blocks anything.**
The old rule wanted a reverse run to separate a separation error from a wheel
asymmetry by sign, but in a spin the wheels counter-rotate, so a per-wheel
radius error enters yaw with the same sign on both sides and cancels — it
surfaces as the robot's centre translating, not as residual heading. A reverse
run would not have discriminated. The asymmetry was independently measured and
applied on 9 Sep (`1.002982` / `0.997018`) and verified at ~0.1° of heading
change over 3 m, so the spin residual already reads separation cleanly.

**Installed and consistent:** `my_controllers.yaml` `wheel_separation: 0.25168`
= 2 × `robot_core.xacro` `wheel_offset_y: 0.12584`, committed in `cap_ws`
`db32d88`. Re-derive only if a driven loop shows yaw drift that scan matching
cannot absorb.

---

## Network link — **MEASURED 2026-09-09**

Jetson `172.20.10.2` → laptop `172.20.10.5`, over the phone hotspot
(`172.20.10.0/28`). Method: `my_bot/scripts/check_ros2_link.py --pub` on the
Jetson, `--sub --secs 15` on the laptop. `ROS_DOMAIN_ID=42`, Fast DDS with
unicast initial peers (D-16, `reference/ros2-network.md`).

| Stream | Published | Received | Rate | Loss |
|---|---|---|---|---|
| `std_msgs/String` | 10 Hz | 152 in 15.1 s | **10.07 Hz** | none |
| `nav_msgs/OccupancyGrid` 162×249 (40 kB) | 2 Hz | 30 in 15.1 s | **1.99 Hz** | none |

**The grid is the number that matters.** It is deliberately the shape of our
real `/map` (162×249 @ 0.05 m, measured the same day), and at 40 kB it exceeds
the ~64 kB datagram limit only when combined with headers — so it exercises the
fragmentation path that `/scan` never does. Clean at default socket buffers, so
**no `sysctl` or `<...SocketBufferSize>` tuning is installed**. If Nav2's larger
costmaps stall on Day 4, that is where to look first, and the script prints the
fix itself.

Also confirmed the same day: `demo_nodes_cpp` talker→listener **both
directions**, and `ros2 node list` on each machine listing the other's nodes.

> ⚠ **This measurement is tied to two DHCP addresses.** It says nothing about
> the link after either machine re-leases. Re-run it — it takes 15 s — rather
> than assuming it still holds.

---

## Nav2 — **RECOVERED**

| | Value | Note |
|---|---|---|
| `footprint` | `[[0.09,0.147],[0.09,-0.147],[-0.265,-0.147],[-0.265,0.147]]` | **not** `robot_radius` |
| `inflation_radius` | 0.25 | both costmaps |
| `cost_scaling_factor` | 3.0 | |
| `allow_unknown` | **true** | frontier goals sit on the unknown boundary |
| DWB `max_vel_x` | 0.055 | **timid starting value, not measured** |
| DWB `min_vel_x` | −0.025 | |
| DWB `max_vel_theta` | 0.125 | |
| `velocity_smoother` max | `[0.055, 0.0, 0.125]` | |
| slam_toolbox `base_frame` | **`base_footprint`** | not `base_link` |
| slam resolution | 0.05 | |

> ⚠ **These are the only speed limits the robot has.** `diff_cont` sets none and
> the hardware interface passes commands straight through. Watch it drive before
> raising them.

### Nav2 brought up for the first time — **VERIFIED 2026-09-10**

`navigation.launch.py` + `nav2_params.yaml` ported and launched against the live
robot. All seven lifecycle nodes reached `active` on the first attempt:
`controller_server`, `smoother_server`, `planner_server`, `behavior_server`,
`bt_navigator`, `waypoint_follower`, `velocity_smoother`.

**The e-stop gap recorded on 9 Sep is closed.** `/cmd_vel_teleop` now has
subscribers where it had none, and `twist_mux` bridges to the controller:

| Topic | Publishers | Subscribers |
|---|---|---|
| `/cmd_vel_nav` | 1 (`controller_server`) | 1 (`velocity_smoother`) |
| `/cmd_vel` | **6** — `velocity_smoother` ×1, `behavior_server` ×5 | 1 (`twist_mux`) |
| `/cmd_vel_teleop` | 0 (until teleop runs) | **2** — `twist_mux`, `behavior_server` |
| `/diff_cont/cmd_vel_unstamped` | 1 (`twist_mux`) | 1 (`diff_cont`) |

Two things in that table are not what the design comments describe, and both
were read off the live graph rather than inferred:

> ⚠ **Recovery behaviours BYPASS the velocity_smoother.** `behavior_server`
> holds five publishers straight onto `/cmd_vel` — one per behaviour plugin —
> while only `controller_server` goes through `/cmd_vel_nav` → smoother. So the
> smoother's `[0.055, 0.0, 0.125]` clamp does **not** apply to a recovery. What
> clamps a recovery spin is `behavior_server.max_rotational_vel: 0.1`, and
> nothing else. `BackUp` and `DriveOnHeading` take their speed from the BT's
> action goal, not from params at all.
>
> This matters for the Day 4 gate, which deliberately provokes a recovery by
> blocking the robot: the recovery is the one moment Nav2 can command a speed
> no params file in this repo reviewed. It is still slow — 0.1 rad/s is below
> DWB's 0.125 — but the earlier note above ("these are the only speed limits")
> is **incomplete**, and `max_rotational_vel` belongs in that list.

> ⚠ **`/cmd_vel_teleop` is not exclusively the e-stop topic.** `behavior_server`
> subscribes to it too: it is the input topic of the `AssistedTeleop` behaviour
> plugin. The e-stop is unaffected — `twist_mux` still holds it at priority 100
> and forwards to the controller — but the keystrokes are also visible to Nav2,
> and while an `AssistedTeleop` action is active the same keys feed a behaviour
> that publishes back onto `/cmd_vel` at priority 10. Nothing in our BT invokes
> `AssistedTeleop`, so this is dormant; it is recorded because "the e-stop topic
> has exactly one subscriber" is the kind of assumption that is cheap to write
> down now and expensive to discover during a demo.

TF with the full stack up: all eight edges resolve, `base_link → laser_frame`
`(−0.034, 0, +0.187)` and `base_link → camera_optical_link` at −90° as expected.
`map → odom` sat at exactly identity, which is correct before the robot moves.

## Final results — the tape-measure protocol (Day 7)

Ground truth chair position, measured against two walls: x ______ y ______

| Pass | Direction | Published x | Published y | Error |
|---|---|---|---|---|
| 1 | front | | | |
| 2 | right | | | |
| 3 | back | | | |
| 4 | left | | | |

| Metric | Target | Measured |
|---|---|---|
| Absolute position error | < 0.25 m | |
| Spread across four passes | < 0.15 m | |
| Duplicate landmarks per object | 1.0 | |
| Ghosts surviving a second pass | 0 | |
| Detections mapped / received | > 0.6 | |
