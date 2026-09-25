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
| `calibrate_straight.py --distance 5.0`, closed loop, marks under the lidar centre | **4.90 m** (tape 4 → 494 cm) | **5.0018 m** | **0.03203** (was 0.0327, −2.0 %) | **25 Sep 2026** |

> ❌ **REVERTED to 0.0327 on 25 Sep, within the hour — the reasoning below was a sign error.**
> The hand push read odom *short* (0.980 of ~1 m); this run reads odom *long* (5.0018 of 4.90);
> the map is *short*. An odom over-read leaking into the map would make it LONG. With 0.03203
> the next lap put A at 4.817 m (was 4.894): the map got shorter, confirming the leak exists
> but that the map's shortness is NOT from the wheels. The 4.90 m tape also contradicts the
> 9 Sep 3 m calibration (+0.17 %). Suspects for the short map: lidar range scale, or the
> tape truths. Original (wrong) note follows.
>
> **Applied** to `my_controllers.yaml` and `robot_core.xacro` (cap_ws). Why now: objective 1's
> map came out short on every tape pair (−2.3 % fitted, 24 Sep 23:50 lap), and the
> 9 Sep hand push had already read −2.0 %. Three measurements, two methods, one
> sign. Floor lateral offset at the end of the run was not reported. The script's
> hint printed `0.034 ×` (free tyre radius) — wrong base, fixed to point at the
> configured radius.
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

## Camera intrinsics — ✅ **SETTLED 11 Sep 2026, validated against a tape measure**

`robot_params.yaml` and `camera_info.yaml` were in `semantic_objects/config/`,
which the dump did not reach — the one calibration that had to be redone. Done,
and cross-checked against a physical length, which is the part that matters.

### The installed calibration — `my_bot/config/c615_640x480.yaml`

| | Value |
|---|---|
| Resolution | 640 × 480 |
| `fx` | **667.8740** |
| `fy` | **669.8458** |
| `cx` | **321.5690** |
| `cy` | **234.5015** |
| Distortion coefficients | `[-0.062931, 0.057181, -0.001224, 0.000858, 0.0]` |
| **Reprojection error** | **0.3403 px** — passes the < 0.5 gate |
| **Tape-measure check** | **PASS**, twice. Pooled tape estimate **668.6**; installed value is **−0.11%** from it. Each run is only ±2.6% precise — see below |
| Measured HFOV | **51.2°** H / 39.4° V (independently 51.4° from the tape) |
| Board depth range | 0.30 – 0.83 m (2.7×) |
| Checkerboard | 9×6, 20 mm |
| Images used | **59** — an 80-image capture, refit with boards closer than 0.30 m excluded |
| **Autofocus** | **LOCKED**, `focus_absolute=51`, `focus_automatic_continuous=0` |
| Method | `make camera` + `make calib` + `make calib-report --min-depth 0.30 --write`, verified by `make calib-scale` |
| Date | 2026-09-11 |

> **Reproduce with:** `ros2 run my_bot camera_calib_report.py --min-depth 0.30 --write`
> against the same `/tmp/calibrationdata.tar.gz`. Without `--min-depth` the
> script only scores what `cameracalibrator` shipped; the flag opts into a refit.

#### Why 59 images and not the 80 that were captured

A locked focus makes near boards soft, and the soft ones carry the residual.
Trimming them is strictly better on every axis — including the one that is not
self-referential, the tape:

| fit | n | RMS | `fx` | `cx` | vs pooled tape 668.6 |
|---|---|---|---|---|---|
| all 80, as shipped | 80 | 0.4464 | 672.65 | 331.19 | +0.60% |
| **refit, ≥ 0.30 m** | **59** | **0.3403** | **667.87** | **321.57** | **−0.11%** |
| refit, ≥ 0.35 m | 54 | 0.3156 | 663.30 | 308.4 | −0.79% ⚠ |

> ⚠ **Correction. An earlier version of this table justified the refit on the
> tape**, quoting +0.45% against +1.17% as though the tape had chosen between
> them. It had not and cannot: a single run of that test is only ±2.6% precise,
> and running it a second time moved its own answer by 1.1%. **All three fits
> are inside the tape's noise.** The pooled column above is a weak preference,
> not evidence.

**`cx` is the reason this was worth doing — not the RMS, and not the tape.**
`cx` offsets every bearing by a constant: the 9.6 px it moved is
`atan(9.6/668)` = **0.82° of systematic pointing bias** removed from every
landmark the semantic layer ever places. 321.57 also sits where a webcam's
principal point ought to, on the frame centre. Unlike `fx`, that argument does
not depend on a measurement with ±2.6% noise in it.

> ⚠ **Do not trim further.** The 0.35 m cut scores better again and is worse:
> `cx` swings out to 308.4. The near views are what constrain the wide end of
> the distortion model, and starved of them the fit starts paying for it with
> the principal point — the same failure as run 1's `391.7`, in the other
> direction. Trimming is not monotonic and RMS will not tell you where to stop.

> The refit pins **`k3 = 0`** (`CALIB_FIX_K3`) to match the model
> `cameracalibrator` shipped. Left free on the reduced set it came out at
> **−0.398**, a large high-order term fitted from fewer near-edge views — a
> different camera model smuggled in under the name of a trim.

### The tape-measure check — what it settles, and what it cannot

`scripts/camera_check_scale.py`, run twice on 11 Sep, each time three stations
at 0.4 / 0.7 / 1.0 m with the board flat-on:

| run | config `fx` at the time | slope | intercept | `fx_true` = config/slope |
|---|---|---|---|---|
| 1 | 672.6463 | 1.0117 | +19.3 mm | **664.87** |
| 2 | 667.8740 | 0.9933 | −5.9 mm | **672.36** |

**The two runs disagree by 1.1%, and that is the important result.**
`fx_true` is supposed to be an absolute anchor independent of the config it was
compared against. It did not reproduce, so the first thing to establish is how
precisely this test measures anything.

`SE(slope) = σ / √Sxx` — the scatter divided by the *spread* of the stations.
With σ = 11.0 mm, `Sxx` = 0.18 m² and one degree of freedom:

> **SE(slope) = ±2.6% at 1σ.**

So each run pins `fx` to about ±2.6%, the two runs differ by 1.1%, and **that
difference is comfortably inside the noise.** The 1.0117 and 0.9933 slopes are
the same measurement twice.

> ⚠ **The ±2% gate this script shipped with was tighter than its own
> precision.** It passed both runs while implying an accuracy neither had.
> Corrected: the script now prints σ, the span, `SE(slope)` and its dof, widens
> the tolerance to the run's own 2σ when that exceeds 2%, and says explicitly
> when a residual offset is inside the noise. The default sweep is now **six
> stations from 0.4 to 1.5 m** — precision goes as `1/√Σ(D−D̄)²`, so reaching
> further out is worth far more than repeating the near stations. At the same
> scatter that takes SE from 2.6% to **1.2%**.

**What the test does establish, beyond any doubt:** the camera is **~51° HFOV,
not the ~62°** this project assumed. That is a 20% error, or **eight sigma**.
The tool is fit for the purpose it was built for — catching a grossly wrong
`fx` — and unfit for adjudicating fractions of a percent. Both facts matter.

**Pooling the two runs** gives `fx` ≈ **668.6**, and the installed 667.874 sits
**−0.11%** from it (the 80-image fit is +0.60%). That is a weak preference, not
a proof: at ±2.6% per run the tape cannot choose between 667.87 and 672.65.
**The case for the installed refit rests on `cx` and the RMS, not on the tape.**

### ⚠ The C615's HFOV is ~51°, not the ~62° this project assumed

Three independent numbers agree and the spec figure is the odd one out:

| Source | HFOV |
|---|---|
| Installed 59-image refit | **51.2°** |
| 80-image focus-locked calibration | 50.9° |
| Tape measure, three distances | **51.4°** |
| `reference/hardware-inventory.md`, pre-dump | ~62° ✗ |
| `semantic_objects_node.py` default `fx: 554.0` | ~60° ✗ |

**The ~62° was a guess written before the dump and it was wrong.** It fired a
false warning on two good calibrations in a row, so `camera_calib_report.py`'s
reference is now **51.0°, measured**, not a vendor figure. A diagonal FOV quoted
for a 16:9 mode does not survive the crop to 4:3 at 640×480.

The node's built-in `554.0` defaults are **21% off the real value** and must be
deleted when the September `semantic_objects` tree is rebuilt — a missing params
file has to fail loudly. (The `fx: 528.1` in the lost `robot_params.yaml` was
marked `← YOUR VALUE`: a template placeholder, never a measurement. Neither
figure conflicts with 672.65 because neither was ever measured.)

### Run 1 (11 Sep, autofocus ON) — kept because it is the diagnostic

The first attempt passed the reprojection gate at **0.3651 px** and was wrong.

| Subset | n | RMS | `fx` | `cx` | depths |
|---|---|---|---|---|---|
| all | 48 | 0.3640 | 715.95 | 323.3 | 0.20–1.07 m |
| first 29 | 29 | **0.1528** | **819.74** | **391.7** | 0.70–1.23 m |
| last 19 | 19 | 0.5302 | **676.30** | 322.1 | 0.18–1.01 m |

**The half with the best RMS was the worst calibration.** Reprojection error
ranks a badly-conditioned fit above a well-conditioned one, because it only ever
asks whether the model explains its own images.

**And the resolution confirms autofocus was the cause.** The `last 19` subset —
the frames after the lens had settled — gave **676.30**, against the
focus-locked run's **672.65** and the tape's **664.85**. All three inside 1.7%.
The outlier is the `first 29` at 819.74, captured at a different focus position
*and* over a degenerate 1.8× depth range. Lock the focus and the disagreement
disappears.

> **The C615 is varifocal: refocusing moves the lens, so `fx` is not a constant
> while `focus_automatic_continuous` is 1.** Left enabled, the driver walked
> `focus_absolute` 51 → 85 unprompted. It drifts at *run* time too, not only
> during calibration — which is why the lock lives in `make camera` and must be
> the same value for the demo as for the calibration.

### Why the focus-locked run scores *worse* (0.4464 vs 0.3651), and why that is fine

`FOCUS=51` focuses far. Boards closer than ~0.3 m are out of focus, their
corners are soft, and they carry almost all the residual:

| board depth | mean RMS | mean sharpness (Laplacian var) | n |
|---|---|---|---|
| < 0.30 m | 0.6280 px | 46 | 21 |
| 0.30–0.40 m | 0.4763 px | 94 | 11 |
| 0.40–0.50 m | 0.3110 px | 99 | 2 |
| 0.50–0.65 m | 0.3317 px | 266 | 9 |
| > 0.65 m | **0.2711 px** | **574** | 37 |

`corr(rms, depth) = −0.735`, `corr(sharpness, depth) = +0.775`. The RMS rise is
**blur from the focus lock, not a worse camera model** — and `fx` is validated
against the tape regardless.

**This makes `FOCUS=51` the right choice for the demo**, which detects objects
across a room, not at arm's length. It is sharp from roughly 0.4 m to far.
If a future run wants a tighter RMS, keep the board beyond ~0.35 m; do not
unlock the focus to chase it.

### What is settled about the method

**`fx` is exactly invariant to square size.** Scale the squares by any factor
and the solver scales every board distance by the same factor and returns the
identical camera matrix — seven significant figures across `--square` 0.020 /
0.030 / 0.050, board distance moving 0.42 → 0.63 → 1.05 m, RMS identical to six
decimals.

> **This reversed an earlier claim made the same day** in this file, the Day 4
> checklist and the report script — all of which said implied HFOV was the guard
> against a mis-scaled printout. It is not, and there is nothing to guard:
> **a mis-scaled board cannot corrupt a bearing**, because `atan((u − cx)/fx)`
> carries no length. Square size sets only the scale of the board's pose, which
> this project never uses — range comes from the lidar. All three corrected.

**`cameracalibrator` computes the reprojection error and discards it.**
`calibrator.py:797` binds `reproj_err` from `cv2.calibrateCamera` and never
stores it; the figure beside the CALIBRATE button is the *linear* error.
`scripts/camera_calib_report.py` recovers the real one by solvePnP-ing each
board with `K` and `D` held at their published values. Validated against
OpenCV's own RMS on a synthetic 12-image set: **0.3253 px both ways, four
decimals.**

**A depth-degenerate capture defeats reprojection error.** Over a narrow depth
range `fx` and board distance are nearly interchangeable; `calib-report` now
prints the ratio and wants **≥ 2.5×**. `cx`/`cy` wandering off the frame centre
is the fingerprint.

**`cam2image` defaults to 320×240**, and intrinsics do not transfer across
resolutions. `make camera` sets the size; `calib-report` refuses anything else.

**`--no-service-check` is required** — `cam2image` offers no `set_camera_info`
service, so without it `cameracalibrator` waits forever looking hung, and
**COMMIT does nothing**. SAVE writes `/tmp/calibrationdata.tar.gz`.

**The two focus controls cannot be set in one `v4l2-ctl` call** — setting
`focus_absolute` in the same `VIDIOC_S_EXT_CTRLS` transaction that still has AF
enabled is rejected. Two calls, AF off first. The lock survives `cam2image`
opening the device.

**Board, from `.bash_history`: 9×6 interior corners, 20 mm.** The recovered
command reads `--square 20.0` because that lost tool took millimetres;
`cameracalibrator` takes **metres** → `--square 0.020`. The pre-dump `8x6` /
`0.025` is wrong on both counts.

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

## Idle-stack timing baseline — 11 Sep 2026

Measured with `check_pose_stability.py --seconds 60`, robot **stationary**, full
stack up (`real_robot.launch.py` + `slam.launch.py`), while `cam2image` and
`cameracalibrator` were also running on the board. Taken to chase a reported
RViz rubber band; it is the baseline any future rubber band is compared against.

| Edge / topic | Measured | Expected, and why |
|---|---|---|
| `odom → base_link` | **30.0 Hz** | `publish_rate: 50` capped by `update_rate: 30`. Confirms the 9 Sep note. |
| `map → odom` | **50.1 Hz** | `1 / transform_publish_period` = 1/0.02. **One publisher.** |
| `base_link → left/right_wheel` | 15.0 Hz | rsp off `/joint_states`, which itself runs at 30.0 Hz. Cosmetic frames; nothing localises off them. |
| `base_link → laser_frame` | **static, 0 Hz** | On `/tf_static`, published once and latched. A rate of zero here is correct, not a fault. |
| `/joint_states` | 29.997 Hz | |
| `/diff_cont/odom` | 30.0 Hz | |
| `/scan` | **11.5 Hz** | **Not the 10.0 in `ydlidar.yaml`.** 4 kHz sample rate / 350 rays ≈ 11.4 Hz — the hardware's real rate; the config value is not what it runs at. |

Timestamp health, 1747 odom and 670 scan messages, **zero** stamps going
backwards on either, and zero same-stamp-different-pose on any TF edge:

| | median age | sd | p99 | max |
|---|---|---|---|---|
| `/diff_cont/odom` | 2.2 ms | 1.0 ms | 5.6 ms | 12.2 ms |
| `/scan` | 88.4 ms | 1.1 ms | 92.2 ms | 93.7 ms |

**Scan sweep: 89 ms** (`scan_time` = 0.0871 s; `time_increment` × 349 = 88.0 ms).
This independently reproduces the 86 ms measured 9 Sep. The shear table stands:
4.4 cm per scan at 0.5 m/s, 0.9 cm at 0.10 m/s.

> **The 88 ms scan age is structural, not a fault.** It is the sweep itself: the
> driver stamps the scan when the sweep completes and the ranges span the 89 ms
> before it. It is nowhere near the 200 ms `transform_timeout`, and its standard
> deviation is 1.1 ms — there is no jitter to chase here.

> ⚠ **A first run of the same test reported 338 ms and 352 ms outliers and a
> ±22 ms odom jitter. Those were an artefact of the measurement**, taken while
> the ros2 daemon was being restarted and several `ros2` CLI processes were
> starting. The 60 s rerun on a settled graph put the sd at 1.0/1.1 ms. **Judge
> this test on p99, never on max, and never run it during bring-up.**

## Jetson ↔ laptop clock offset — 11 Sep 2026

**Laptop is 10.3 ms BEHIND the Jetson. Uncertainty ±12.2 ms.** Well inside the
~50 ms where RViz's TF interpolation would visibly rubber-band, so **clock skew
is eliminated** as a cause of the reported snap-back.

Method matters here. An SSH round-trip estimate gave `+54.8 ms ±82.2 ms` — the
uncertainty is wider than the threshold it is being compared against, so that
number decides nothing, and its midpoint is biased high because remote process
spawn lands late in the window. The figure above is a four-timestamp NTP-style
UDP exchange (server on the Jetson, which has no firewall; client on the
laptop, whose `ufw` allows the outbound), best-delay sample of 34:

| | |
|---|---|
| round-trip delay, min | 24.4 ms |
| offset, best-delay sample | +10.25 ms (Jetson ahead) |
| offset, median of 34 | +10.39 ms |
| offset, stdev | **0.54 ms** |
| UDP replies | 34/40 — **15 % loss on the laptop's wifi** |

Sync quality is **not** symmetric, and that is worth knowing before trusting a
future reading: the Jetson runs **chrony** against `ntp1.bknix.co.th`, RMS
offset 0.6 ms, polling every 64 s. The laptop runs **systemd-timesyncd** against
`ntp.ubuntu.com`, reporting **Jitter=55 ms** and polling every **34 minutes**.
The 10 ms agreement is better than the laptop's own sync discipline deserves;
it can drift between polls, so **re-measure rather than assume it holds.**

> The two boxes are also in different timezones — `Asia/Taipei` on the Jetson,
> `Asia/Bangkok` on the laptop. UTC agrees, which is all ROS uses. Not a bug,
> but it makes side-by-side `date` output look alarming.

## YOLO detector — **MEASURED 2026-09-14** (Day 5, D-11 option B)

`my_bot/scripts/yolo_detector.py` + `launch/yolo.launch.py`, `make yolo`.
Measured with `my_bot/scripts/detection_report.py`, which is the gate tool.

### Environment — all versions confirmed live in the node, 14 Sep

| | |
|---|---|
| model | `~/yolo/yolo26n.pt` (5.3 MB, ultralytics release v8.4.0), **torch, no engine** |
| precision / imgsz | fp16 (`quantize=16`) / 640, letterboxed from 640×480 |
| torch / torchvision | **2.11.0 / 0.26.0** (JetPack cp310 wheels, unchanged from 9 Sep) |
| ultralytics | **8.4.144** — `half` is deprecated for `quantize` in this version |
| tracker | ByteTrack (`bytetrack.yaml`), needs **`lap` 0.5.13** — was missing from the venv, now in `setup_yolo_venv.sh` |
| numpy / cv2 | 1.26.4 / 4.5.4 (system, no CUDA) |
| power mode | nvpmodel **15 W**; GPU devfreq governor `nvhost_podgov`, floor 306 MHz, ceiling 624.75 MHz |
| camera | `cam2image` 640×480 @ 15 Hz, RELIABLE, focus locked 51, `frame_id` `camera_link` |

### Bench — synthetic 640×480 frame, GPU, 30-frame mean after 5 warm-up (14 Sep)

| model | predict 640 fp32 | predict 640 fp16 | predict 480 fp32 | predict 480 fp16 | **track 640** (wall, incl. ByteTrack) |
|---|---|---|---|---|---|
| `yolo26n.pt` | 34.9 ms | 35.9 ms | 36.2 ms | 37.9 ms | **53.3 ms** |
| `yolov8n.pt` | 29.2 ms | 25.0 ms | 27.8 ms | 27.7 ms | **47.9 ms** |

Two things the table settles: **imgsz 480 buys nothing** (the pipeline is
launch-bound, not pixel-bound, at nano size) and **fp16 buys nothing on
yolo26n**. The checklist's two "levers" are therefore not levers on this board.
The recovered engine figure (18 ms for yolo26n) is ~2× faster than `.pt`, and is
the only lever left if one is ever needed.

### Live — `make yolo` against the real camera, 301 s, 14 Sep 16:00

| | |
|---|---|
| `/detections` rate | **15.15 Hz**, 4556 msgs; inter-arrival 66.0 ms, **sd 5.2 ms**, max 96 ms |
| inference + tracking, in-node | **p50 44.5 ms**, max ~50 ms typical, one 62.6 ms outlier |
| age at publish (capture → publish) | p50 48 ms, max 79 ms |
| age at receipt (capture → subscriber) | p50 49 ms, p95 60 ms, max 80 ms |
| GPU clock through the run | **306 MHz the whole time** (floor); load bursty 0–50 % |
| `tj-thermal` | 42.8 → 44.1 °C, **max 44.6 °C** |
| `gpu-thermal` | 42.3 → 44.1 °C |
| detections | **0.00 per frame** — the camera was facing a blank wall |

**Camera-limited, same as the recovered stack.** 44.5 ms of work fits inside
the 66.7 ms frame with 22 ms spare, and the node processed every frame (4556
in 301 s = 15.13 Hz against cam2image's 15.15). The GPU never left its floor
clock and the chip warmed by 1.3 °C in five minutes. Nothing here is near a limit.

### Track-id persistence — still image on `/image`, 60 s, 14 Sep 16:06

The real camera had nothing in view, so the tracker was proven against a
stand-in: a still 640×480 frame (ultralytics' `bus.jpg`, four people and a bus)
published on `/image` at 15 Hz RELIABLE with capture-time stamps, exactly as
`cam2image` would. `make yolo USE_CAMERA=false`.

| | |
|---|---|
| rate | 14.83 Hz, 893 msgs; sd 14.5 ms (the Python stand-in publisher jitters more than cam2image) |
| detections | **5.00 per frame, 893/893 frames**, 0 frames with a detection but no id |
| track ids | **5 distinct, each in 893/893 frames, span 100 %** — person 0.88 / bus 0.87 / person 0.86 / 0.82 / 0.79 |
| GPU load | mean 37 %, max 73 %, clock still 306 MHz |
| `tj-thermal` | max 45.4 °C |

**What this proves:** the id is written into `Detection2D.id`, ByteTrack holds
it across every frame for a static scene, and the message layout is what the
June `semantic_objects` parses (`class_id` is the class *name*, bbox is
centre+size in original pixels). **What it does not prove:** persistence under
the real camera's noise, exposure flicker and a slightly moving robot. That
needs a real object held still in frame for the five-minute run — which is
what the gate line says, and it remains **open** until someone is at the robot.

### Track-id persistence — **REAL CAMERA, PASSED 14 Sep evening**

One cup placed in front of the camera and left alone; `make yolo` +
`detection_report.py --seconds 30`, run by the user.

| | |
|---|---|
| rate | 15.18 Hz, 457 msgs; sd 17.5 ms, **one 356 ms stall**, otherwise 66 ms |
| detections | 1.00 per frame, **457/457 frames**, class `cup`, conf 0.69 |
| track ids | **1 distinct, id 1, in 457/457 frames, span 100 %** |
| age at receipt | p50 66 ms, p95 93 ms, max 419 ms (the same stall) |
| GPU | 306 MHz floor, load mean 37 % max 66 % |
| `tj-thermal` | 52.0 → 52.0 °C, max 52.3 (board warmer than the afternoon's 44 °C; ambient/uptime) |

**Day 5 gate closed.** A single low-contrast object at 0.69 confidence held one
id for the whole window with no re-acquisition; this is the case the still-image
run could not prove. The one stall is worth a glance in the next 300 s run — if
it recurs every few seconds it is something scheduling frames, not the model.

> ⚠ **Read `detection_report.py`'s thermal verdict on temperature, not clock.**
> The first version of the script called "clock below max while at rate"
> throttling and failed the 301 s run on it. A 306 MHz clock at 15 Hz is the
> podgov governor idling a launch-bound GPU, not a throttle; the script was
> rewritten mid-run to judge on `tj` and print load alongside. The 301 s
> numbers above were re-read from the raw samples with the corrected rule.

## YOLO model swap to `yolo26s` + ONNX — **MEASURED 2026-09-16** (D-22)

`make yolo` now exports `yolo26s.pt` → `yolo26s.onnx` (fp16) and runs it under
onnxruntime-gpu. Same node, same topic, same track-id contract as Day 5 — only
the weights and the backend changed. **The Day 5 gate has not been re-run yet;
everything below is a synthetic-frame bench.**

### Environment added, 16 Sep — nothing else in the venv moved

| | |
|---|---|
| onnxruntime-gpu | **1.24.0**, the **JetPack aarch64 wheel** from `pypi.jetson-ai-lab.io/jp6/cu126` |
| providers reported | `TensorrtExecutionProvider`, `CUDAExecutionProvider`, `CPUExecutionProvider` |
| provider actually used | **CUDAExecutionProvider** — confirmed by reading `session.get_providers()` back from the live AutoBackend, not assumed |
| onnx / onnxslim | 1.22.0 / 0.1.96 |
| transitive | colorama 0.4.6, flatbuffers 25.12.19, ml-dtypes 0.5.4, protobuf 7.36.1 |
| unchanged | numpy **1.26.4**, cv2 **4.5.4**, torch **2.11.0** (cuda True), ultralytics 8.4.144 |
| `yolo26s.pt` | 20.4 MB, ultralytics release v8.4.0 |
| `yolo26s.onnx` | **19.2 MB** fp16 (fp32 is 38.3 MB); opset 17, static 1×3×640×640, export 5.5–6.0 s |

### Bench — synthetic 640×480 frame, `model.track()` wall time incl. ByteTrack, 30 frames after 5 warm-up

| model | mean | p50 | max |
|---|---|---|---|
| `yolo26n.pt` torch | 35.4 ms | 35.4 ms | 36.4 ms |
| `yolo26s.pt` torch | 36.6 ms | 35.5 ms | 46.5 ms |
| `yolo26s.onnx` **fp32** | **45.8 ms** | 44.2 ms | 58.7 ms |
| `yolo26s.onnx` **fp16** | **35.4 ms** | 34.1 ms | 45.7 ms |

**`yolo26s` costs 1.2 ms over `yolo26n`** — not the ~1.5× the recovered engine
figures implied (27 ms vs 18 ms). Launch-bound, not compute-bound; the same
conclusion 14 Sep drew from `imgsz` 480 buying nothing.

**ONNX fp32 is a 9 ms regression against plain torch.** Only fp16 pays for
itself, and it lands level with the nano `.pt`. `ONNX_HALF` defaults to true
for this reason — see D-22.

> ⚠ **These numbers are NOT comparable to the 14 Sep bench table above**, which
> records 53.3 ms for `yolo26n.pt` where this run measures 35.4 ms for the same
> model and nominally the same method. The cause is not established. The
> `n`-vs-`s`-vs-`onnx` comparison here is internally consistent — one run, one
> session, same frame — so it is sound for **choosing between the options**, and
> it is not evidence about absolute end-to-end rate. Treat 14 Sep's live 44.5 ms
> p50 as the only measured in-node figure until a new live run replaces it.

### Live — `make yolo` against the real camera, 301 s, 16 Sep — **GATE RE-PASSED**

`yolo26s.onnx` fp16, imgsz 640, CUDAExecutionProvider. User-run, real scene
(people, a laptop, chairs, a phone, a cup), unlike 14 Sep's blank wall.

| | 14 Sep — `yolo26n.pt` torch, blank wall | 16 Sep — `yolo26s.onnx` fp16, busy scene |
|---|---|---|
| `/detections` rate | 15.15 Hz, 4556 msgs | **15.13 Hz, 4553 msgs** |
| inter-arrival sd / max | 5.2 ms / 96 ms | **9.8 ms / 180 ms** |
| age at receipt p50 / p95 / max | 48 / 60 / 80 ms | **65 / 80 / 246 ms** |
| detections per frame | 0.00 | **4.41** (4553/4553 frames had ≥1) |
| frames with a det but no track id | — | **0** |
| GPU clock | **306 MHz floor** throughout | **625 MHz ceiling**, 510 at the end |
| GPU load | 0–50 % bursty | **mean 57 %, max 99 %** |
| `tj-thermal` | 42.8 → 44.1 °C, max 44.6 | **49.5 → 51.9 °C, max 52.0** |

**Still camera-limited.** 4553 messages in 301 s is 15.13 Hz against cam2image's
15.15, and every published frame carried detections — the node did not drop
frames. That is the thing the gate asks and it holds.

> ⚠ **This run changed TWO variables against 14 Sep, not one.** The model and
> backend changed *and* the scene went from a blank wall to 4.41 detections per
> frame with 144 tracked ids. **The GPU, thermal and latency rises above cannot
> be attributed to the model** — postprocess, NMS and ByteTrack all scale with
> detection count, and 14 Sep's baseline did none of that work. The honest read
> is that the numbers are fine, not that `yolo26s.onnx` caused the difference.
>
> Separating them is cheap and takes 60 s in the same scene:
> `make yolo MODEL=~/yolo/yolo26n.pt` then `detection_report.py --seconds 60`.
> Not run.

**The 306 MHz-floor observation from 14 Sep no longer describes this workload.**
The `nvhost_podgov` governor did exactly what the symptom index says it does —
it raised the clock on load, to the 625 MHz ceiling. The end-of-run 510 MHz is
the governor coming back down as load fell, not throttling: tj peaked at 52.0 °C
against a ~90 °C limit, and the clock's maximum and its mean load both rose
together. **`sudo jetson_clocks` is no longer a lever in reserve here** — the
clock is already reaching its ceiling on its own.

### Track-id churn — 144 distinct ids in 301 s, **a Day 6 risk, not a Day 5 failure**

The gate wants one id spanning ≥80 % of the window and got it: **id 37, laptop,
4459/4553 frames = 100.0 %, conf 0.92** — a stationary object held perfectly,
which is the same result the 14 Sep cup gave.

What the gate does not judge is the other 143. Several classes carry more than
one id: laptop 37 (100 %) **and** 107 (27.8 %, conf 0.60); chair 329 (17.8 %)
**and** 230 (7.6 %); cell phone 322 and 374.

**This output cannot distinguish "two chairs in the room" from "one chair, two
ids".** Both are consistent with what was printed, and people walking in and out
legitimately produce many short-lived person ids. So this is recorded as a thing
to watch, not a proven defect.

It matters because **P5 gives the semantic layer track id as its "same object
again" key**. If one physical chair acquires a second id, the semantic node has
no way to know, and the result is two landmarks for one chair — already in the
symptom index as "Duplicate landmarks for one object". A chair is the Day 6 test
object, and the Day 6 bench check (`landmark_tape_measure.py chair --truth X Y`,
one taped chair, no driving) is exactly the test that would expose it. Do that
before reading anything into the drive-past.

## Semantic fusion — Day 6 desk work, **14 Sep 2026** (bench check ✅ passed 16 Sep, below)

`cap_ws/src/semantic_objects/` rebuilt from the June modules. Everything below
was verified on the desk with `robot_state_publisher` only — no lidar, no
camera, no map. ~~The stationary bench check (chair at a taped position) and the
Day 6 gate remain **open**~~ — **the bench check PASSED 16 Sep**, recorded
immediately below; the Day 6 gate (drive-past) is still open. See STATE.md.

### Camera side corrected — `camera_offset_y` is **−0.030 m (RIGHT)**

The user confirmed on 14 Sep that the camera is mounted on the robot's
**right**. `camera.xacro` carried `+0.03` (left, assumed) from 9 to 14 Sep.
Resolved `camera_link` in `base_link` is now **(+0.050, −0.030, 0.167)**,
read back from TF by the semantic node at startup. The lidar is at
**(−0.034, 0.000)**. Nothing measured on Day 4 depended on the side (intrinsics
and the tape check are internal to the camera).

### Two geometry defects found by review, neither in P1–P8, both now tested

| Defect | Effect | Fix |
|---|---|---|
| **Mirrored scan window.** `pixel_to_azimuth` is image-right-positive; the extractor searched the scan at those angles; the lidar is left-positive (verified 11 Sep) | a box on the image's right took its range from the robot's **left** — bearing right, range from the wrong side | window is `[−az_right + yaw, −az_left + yaw]` in lidar angles; 5 tests in `test_day6_fixes.py::TestMirror` including an extractor→projector round trip |
| **Wrong range origin.** projector did `camera + r·ray` with a range measured from the lidar | constant bias: at 1 m, 20° left, **8.8 cm** | camera ray ∩ lidar range circle (one sqrt); 6 tests. Also handles the 3 cm lateral offset exactly: 1.7° at 1 m, more than one lidar ray |

Both went unseen by the 111 June tests because every window they used was
symmetric about the optical axis. Total after Day 6: **139 tests, all green**.

### Node startup, desk, 14 Sep 17:39

```
intrinsics from .../my_bot/config/c615_640x480.yaml: fx 667.874 fy 669.846 cx 321.569 cy 234.502 @ 640x480
base_link->camera_link: (+0.050,-0.030) yaw +0.00 deg, pitch -3.0 deg (ignored, 2D)
base_link->laser_frame: (-0.034,+0.000) yaw +0.00 deg
```

So: the **554.0 defaults are gone** — the node has no intrinsics of its own and
reads the one installed copy — and the extrinsics come from TF (D-10). Without
`/scan` and `/detections` it says so every 5 s; with them but without odometry
the motion gate stays **closed** and says that instead.

### Bridge and UI, desk, 14 Sep 17:43

| | |
|---|---|
| bridge venv | uv, `/usr/bin/python3.10`, system site-packages; `fastapi 0.141.1`; 37 bridge tests pass (`-p no:launch_testing` — the ROS pytest plugin is incompatible with pytest 8) |
| `GET /api/health` | `ros_connected: true`, `landmark_count: 0` |
| `POST /api/clear` | 200; the semantic node logged `clear_landmarks: dropped 0 landmark(s)` — the service exists now |
| `GET /api/map` | 503 "not yet received" — correct without `make slam` |
| Node | **20.19.x** via NodeSource (apt's 12.22 cannot run Vite 5); `npm ci` clean; `npm run build` 2.9 s |
| UI | `npm run dev -- --host` answers at `http://192.168.160.106:3000/`; `.env` points it at the bridge on the Jetson |

Three bridge edits, none to the landmark schema (which matched on all seven
fields): `/scan` was subscribed RELIABLE and would never have connected to the
best-effort driver; `/map` now transient-local; the camera topic is a setting
(`/image/compressed`, fed by a `republish` node in `semantic.launch.py`); CORS
open; `datetime.UTC` (3.11) replaced for 3.10.

### `min_returns` against the measured dropout

Left at **3**, per the 9–10 Sep analysis (27.9 % / 25.7 % dropout: a 0.3 m
object at 3 m has ~4 live rays). `max_spread` **0.5 m**. `angular_padding`
**0.035 rad**: the window is computed at the camera and the lidar is 3 cm
beside it. All in `config/robot_params.yaml` with the reasoning.

## Stationary bench check — **PASSED 2026-09-16**, the geometry chain is verified

The first live run of the whole fusion chain: `make real` · `make slam` ·
`make yolo` · `make semantic`, robot stationary, one chair at a tape-measured
position. Scored with `my_bot/scripts/landmark_tape_measure.py`.

### Setup

| | |
|---|---|
| object | one chair, **on the robot's RIGHT** (confirmed by the user) |
| measured | 1.50 m ahead of the **camera**, 0.50 m right of the **camera** |
| converted to `base_link` | **X 1.55, Y −0.53** — camera sits at (+0.05, −0.03), and REP-103 makes the robot's right **negative** Y |
| bearing off the camera axis | **18.4°**, projecting to pixel x ≈ 544 of 640 (half-FOV 25.5°) |
| range, axle → chair | 1.64 m |
| detector | `yolo26s.onnx` fp16 (D-22) |

### Result — all three targets met, with margin

| | measured | target | |
|---|---|---|---|
| absolute error | **0.08 m** | < 0.25 m | ✅ 3× inside |
| spread | **0.04 m** | < 0.15 m | ✅ |
| duplicates within 1 m | **1** | exactly 1 | ✅ |
| fused ratio | **132/140 = 94.3 %** | well above zero | ✅ |

**What this actually proves.** These three numbers fail for different reasons,
which is why all three are scored: error is the geometry chain, spread is the
fusion, duplicates is the association. All three passing at once means the whole
chain is right end to end —

- **intrinsics** read from `c615_640x480.yaml` (fx 667.87), one copy, D-19;
- **the mirrored scan window is fixed** — this is the decisive one. The chair
  was 18.4° off-axis on the **right**. A mirrored window would have placed the
  landmark at Y **+0.53** instead of −0.53, an error of ~1.06 m. Measured error
  was 0.08 m, so the mirror defect found on 14 Sep is genuinely gone;
- **the camera is on the right** (`camera_offset_y −0.03`), for the same reason;
- **the range origin is the lidar, not the camera** (D-19) — an 8.4 cm error
  would eat a third of the budget on its own, and 0.08 m total leaves no room
  for it;
- **TF is looked up at the detection's capture stamp** (P2) — less strained by a
  stationary robot than it will be while driving, so this one is confirmed but
  not yet stressed;
- **association on track id** (P5) held one chair to one landmark.

**94.3 % fused** means the lidar-window extraction is not fighting the chair's
legs: the anticipated `max_spread` / `min_returns` rejection against thin chair
legs with a wall behind did not materialise at this range.

> ⚠ **Not yet tested by this run:** P2 under rotation (the robot never moved),
> the motion gate (`max_omega` 0.3 rad/s never approached), and landmark
> persistence after driving away. Those are the drive-past gate.

## Spin recovery — **PASSES, 2026-09-16.** The two failures were a loose battery

The Day 4 clause that was ticked-but-unevidenced since 15 Sep. Executed three
times by Claude with the full stack up (`make real` · `make slam` · `make nav`).

```
ros2 action send_goal /spin nav2_msgs/action/Spin "{target_yaw: 1.57, time_allowance: {sec: 25}}"
```

| | attempt 1 | attempt 2 | attempt 3 |
|---|---|---|---|
| battery | **unseated** | **unseated** | **reseated** |
| result | ABORTED | ABORTED | ✅ **SUCCEEDED** |
| `total_elapsed_time` | 25.000396 s | 25.000421 s | **16.400653 s** |

### ✅ The result — D-21 is vindicated on both counts

| | measured | expected |
|---|---|---|
| duration | **16.4007 s** | 15.7–16.5 s |
| yaw achieved | **1.5762 rad (90.31°)** | 1.57 |
| wheel rotation | **−5.9963 / +6.1356 rad** — counter-rotating | — |
| mean ω | **0.0961 rad/s** | 0.1 commanded (shortfall is the ramp) |

**1. The `time_allowance="25.0"` override works.** Even the failed attempts
proved this: they aborted at **25.000 s**, not upstream's 10 s port default, so
`my_bot`'s behaviour tree is loaded and used.

**2. The stiction worry D-21 raised is DISPROVEN.** The successful run used the
*same* `max_rotational_vel: 0.1` as the two failures. **0.1 rad/s does break
this robot away from standstill.** No change to `max_rotational_vel` is needed
and none was made.

### ⚠ RETRACTION — an earlier entry here called this stiction. That was wrong.

Between attempts 2 and 3 the only change was **the battery being reseated.** The
failures were **loss of motor power**, not friction.

The evidence gathered during the failures is still good, and it is worth keeping
because the *diagnostic* is reusable:

| evidence | value | meaning |
|---|---|---|
| `/cmd_vel` | 502 samples, `angular.z 0.1` | the behaviour commanded correctly |
| `/diff_cont/cmd_vel_unstamped` | 502 samples, `angular.z 0.1` | `twist_mux` passed it through to the hardware interface |
| `/diff_cont/odom` | `(0,0,0,1)` exact identity | the robot did not rotate |
| `/joint_states` | `0.0`, `0.0` after 50 s | the encoders recorded nothing |

**Why every one of those readings was consistent with a dead motor rail:** the
**ESP32 is powered over USB**, so `DiffDriveSerial` connected, accepted commands
and reported encoder counts perfectly — while the motors had no supply. The
conclusion drawn from that ("the motors do not break away at 0.1 rad/s") did not
follow, because *motor power was never checked*. **Check the battery before
suspecting friction.** The connector is keyed and this was a one-off, so no
recurring pre-flight step was added.

### Free result — `wheel_separation` physically confirmed for the first time

Back-computed from the successful spin's own encoder data, independent of any
earlier calibration:

```
mean |wheel rotation| 6.0660 rad × r 0.0327 m      = 0.19836 m of arc per wheel
L = 2 × 0.19836 / 1.5762 rad                        = 0.25169 m
configured (my_controllers.yaml:58)                 = 0.25168 m      → 0.003 % apart
```

**`wheel_separation` was settled on 10 Sep by inverting a formula, with no
driving** (see the callout in STATE.md). This is its **first physical
validation**, and it holds to a hundredth of a millimetre. The 2.30 % left/right
rotation asymmetry is consistent with the radius multipliers already installed
(`left 1.002982` / `right 0.997018`).

## Day 6 gate — **PASSED 2026-09-16.** Fusion live, end to end

`make real` · `make slam` · `make nav` · `make yolo` · `make semantic`, driven on
`make teleop-nav`. Detector is `yolo26s.onnx` fp16 (D-22).

### The gate

| clause | result |
|---|---|
| marker appears in roughly the right place and **stays** after driving away | ✅ **user-confirmed** |
| browser UI shows it | ✅ (after four defects fixed, below) |
| fused ratio well above zero | ✅ **~45 %** |
| everything pushed | ✅ both repos |

### Fused ratio — four consecutive 5 s windows

| fused / detections | frames | tf miss | gate no-odom / turning | rejections |
|---|---|---|---|---|
| 20 / 57 | 57 | 0 | 0 / 0 | max_spread 37 |
| 28 / 57 | 57 | 0 | 0 / 0 | max_spread 29 |
| 26 / 57 | 57 | 0 | 0 / 0 | max_spread 31 |
| 25 / 57 | 57 | 0 | 0 / 0 | max_spread 32 |

**Every single rejection was `max_spread`.** `tf miss 0` and both motion-gate
counters at 0 across all four windows — so P2 (TF at the capture stamp) and P3
(the motion gate) were clean, and the geometry chain was not implicated at all.

> ⚠ **Provenance, stated precisely.** These four windows were captured by Claude
> shortly after the robot was repositioned, with the robot **largely stationary**.
> The drive-past that satisfied the "stays" clause was run separately by the
> user, and **its fused ratio was not captured.** Do not read ~45 % as a
> while-driving figure.

### `max_spread` against range — the placement envelope

Three points from the same day, same parameters (`max_spread: 0.5`,
`min_returns: 3`):

| chair range | fused | note |
|---|---|---|
| **~0.7 m** (computed from bbox) | **0 %** — all 57/57 rejected | bbox 473×477 px in a 640×480 frame; scan spread within ±20° measured **0.62 m** against the 0.5 m limit |
| drive-past distance | **~45 %** | after backing the robot off |
| **1.64 m** (tape-measured) | **94.3 %** | the stationary bench check |

At ~0.7 m the chair subtends roughly 39°, so the lidar window across the bbox
inevitably catches the chair *and* the background. **This is the guard working
as designed** (§2.4, "reject, do not fall back", D-09) — not a defect, and
**not** a reason to lower `max_spread`. The fix is physical: put the object
further away.

⚠ **Day 7 scores this metric at > 0.6** (detections mapped / detections
received). ~0.45 is short of it. **Back the robot off toward the 1.64 m figure
before the tape-measure protocol.**

### Detector under fusion load

| | |
|---|---|
| `/detections` rate | 14.4–15.2 Hz |
| infer + track, in-node p50 | 47.9 → 56.1 ms |
| age at publish p50 | 53 → 88 ms |
| detections per frame | 1.0 (one chair, one track id) |
| detection confidence | 0.90 |

### Bridge and UI, verified live

| | |
|---|---|
| `/api/health` | `ros_connected: true`, `landmark_count: 18`, robot pose present |
| bridge map | 249×216, res 0.05, origin (−7.696, −9.237) — **verified identical to live `/map`** |
| `/image/compressed` | **15.3 Hz** |
| `/map` | 0.5 Hz |

### Landmark persistence — resolved, cause not established

`~/maps/landmarks.json` was written at **17:35:22**, the moment a landmark was
confirmed. It had been stale since **14 Sep 19:16** despite the bench check
producing a confirmed landmark that morning. **The staleness is not
reproducing and no cause was established**; it is recorded as resolved-not-
explained rather than attributed to a guess.

### Four defects fixed reaching this gate — **none of them fusion or geometry**

Every one presented as though the robot were wrong. Worth citing in the Day 7
limitations write-up.

1. **Fatal startup race**, `semantic_objects_node.py` — `self._stats` was
   initialised *after* `_setup_subscribers()`. With
   `TransformListener(spin_thread=True)` a background executor exists, so
   starting `semantic` while `/detections` was **already flowing** raised
   `AttributeError` in `_on_synced` and **killed the executor**: process alive,
   node still listed, nothing ever processed again. Order-dependent — starting
   `semantic` before `yolo` hid it completely, which is why it survived until
   now, and the natural bring-up order is the failing one.
2. **`NO SIGNAL` rendered unconditionally** over a working 15.3 Hz feed —
   nothing tracked whether a frame had arrived.
3. **The map was fetched once at page load**, never refreshed, while
   `slam_toolbox` kept extending the grid. RViz live, browser frozen.
4. **Class labels invisible** — `#e8e8e8` on mapped free space `#f0f0f0` is
   **1.08:1** contrast (4.83:1 over unknown grey), so labels vanished exactly
   where the robot had already mapped. The scale bar had the same defect,
   unreported.

### Not confirmed by this gate

- **Markers in RViz.** A §3 item, not a GATE clause. The `Semantic Landmarks`
  display added to `nav.rviz` (MarkerArray on `/semantic_markers`, **Transient
  Local** to match the publisher) **has never been exercised.**
- **Wheel-slip heading recovery.** Reported by the user after the gate: a robot
  wedged on an obstacle slips, and wheel odometry reports rotation that did not
  happen. `slam_toolbox` corrects this into `map → odom` by design, but the
  matcher's angular search window is `coarse_search_angle_offset: 0.175 rad`
  = **±10°**, narrowed deliberately by D-18 on the premise that odometry is
  trustworthy. At `diff_cont`'s 0.5 rad/s ceiling, **0.35 s of full-speed slip
  exhausts that window.** Untested and unmeasured.
  ⚠ Second-order: the semantic motion gate reads ω from `/diff_cont/odom`
  (`semantic_objects_node.py:421`), so during a slip it sees phantom rotation
  and drops every detection — the fusion goes blind exactly when the robot is
  physically still.

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

---

## Day 4 gate — first attempt, **FAILED 2026-09-15**, two causes both found

Four RViz goals, all failed. Neither cause was navigation tuning; both were
config contradictions with exact, reproducible signatures. Raw evidence in
`~/.ros/log/planner_server_7209_1789463847748.log` and
`behavior_server_7211_1789463847821.log`.

### Cause 1 — goals were published in the `odom` frame

| | |
|---|---|
| Error | `Extrapolation Error ... when looking up transform from frame [odom] to frame [map]` |
| Logger | `transformPoseInTargetFrame`, then `planner_server: Could not transform the start or goal pose in the costmap frame` |
| Requested time | `1789463888.599865` — **pinned, identical on every retry** |
| "earliest data" | `889.944 → 890.705 → 891.636 → 892.652` — marches forward |
| Error first logged | `1789463899.851` — **11.25 s after the pinned stamp** |
| Goal accepted by `bt_navigator` | `1789463888.635` — 35 ms after the stamp, i.e. it is the RViz click |

The goal's `frame_id` was `odom`. RViz stamps a goal in its **Fixed Frame**, and
a goal already in `map` needs no lookup at all, so this is silent until the
frame is wrong. `nav.rviz` ships with `Fixed Frame: map`; it had been changed.

**Method for reading the gap — the buffer was never the problem.** Measured the
same day by filling a default `tf2_ros.Buffer` from the live stack for 12 s and
probing `lookup_transform('map','odom', now − age)`:

| age | result |
|---|---|
| 0.0 – 9.5 s | OK |
| 11.0 s | FAIL, and prints `earliest` **1.158 s** after `requested` |

So the buffer holds a healthy **10 s**, and the printed gap is
`request_age − 10 s`, not the buffer depth. The gate's 1.344 s and 0.673 s gaps
therefore mean requests **~10.7 s and ~11.3 s stale**.

`map → odom` itself measured healthy at the same time, robot stationary:

| | |
|---|---|
| publish rate | **46.1 Hz** (`transform_publish_period: 0.02`) |
| stamp − now | min −0.109, median **+0.070**, max +0.113 s |
| stamp step | median **0.000 s**, max 0.086 s — the transform is *scan*-stamped and republished ~4× per scan, so stamps advance at the 11.6 Hz scan rate |
| backwards steps | **0** in 369 samples |
| arrival gap | median 20.0 ms, max 22.9 ms |
| stamp span held | 7.365 s over 7.206 s of wall time — the buffer fills 1:1 |

### Cause 2 — the Spin recovery can never finish

| | |
|---|---|
| `spin_dist` (upstream tree) | 1.57 rad |
| `behavior_server.max_rotational_vel` | 0.1 rad/s |
| Time the geometry needs | **15.7 s**, before any acceleration ramp |
| `time_allowance` (BT **port** default) | **10.0 s** |
| Measured | `Turning 1.57` → `Exceeded time allowance` at **exactly 10.000 s**, 4 of 4 |

Timestamps: 902.631→912.631, 927.630→937.630, 976.630→986.630, 1001.630→…

Not drift, not the motors, not the floor. Fixed by owning the BT XML with
`time_allowance="25.0"` — **D-21**. `max_rotational_vel` deliberately left at
0.1 (below DWB's `max_vel_theta` 0.125).

> **Next thing to check if 25 s is also exceeded:** 0.1 rad/s is only ~151
> encoder ticks/s per wheel — four times slower than the `BackUp` recovery,
> which succeeded every time at 0.05 m/s (~600 ticks/s). If the wheels stall on
> stiction the symptom is a *stationary* robot that still times out. Not
> observed yet; untested.

> ✅ **ANSWERED 16 Sep: no stiction.** The spin succeeded at this same
> 0.1 rad/s in 16.4007 s. The two failures that looked like stiction were an
> unseated battery. `max_rotational_vel` was left unchanged.

### Day 4 gate — re-run, **PASSED 2026-09-15** (goal clause)

Both fixes applied: RViz Fixed Frame back to `map`, and the D-21 behaviour tree.
Three goals, three successes, no extrapolation errors anywhere in the session.
`bt_navigator_8618_1789465529679.log`.

| goal | from → to | straight-line | wall time | mean speed |
|---|---|---|---|---|
| A | (−0.83, −2.04) → (3.43, 0.52) | 4.97 m | **115.5 s** | 0.043 m/s |
| B | (3.35, 0.41) → (2.90, 0.24) | 0.48 m | **31.8 s** | — |
| C | (3.01, 0.30) → (3.08, 0.37) | 0.099 m | 6.9 s | — |

Goal A's 0.043 m/s mean against DWB's `max_vel_x` 0.055 is the expected shape
for a path with turns in it, and confirms the velocity clamp is the binding
limit rather than anything upstream of it.

> **Goal C is not a valid test.** 0.099 m is inside `xy_goal_tolerance` 0.15, so
> the robot began already within tolerance and only settled its yaw. Two of the
> three goals exercised planning.

> ⚠ **No recovery behaviour ran in this session — zero `Running spin` lines in
> `behavior_server_8584_1789465529644.log`, against twelve in the failed
> attempt.** So the second half of the Day 4 gate is recorded as passed on the
> user's report but has no log evidence, and **D-21's `time_allowance="25.0"`
> has never executed on this robot.** Untested, not verified. The direct test
> is in STATE.md; expect 15.7–16.5 s, and watch for stiction at 0.1 rad/s
> (~151 encoder ticks/s per wheel) rather than a timeout.

> ✅ **EXECUTED 16 Sep: SUCCEEDED in 16.4007 s.** D-21's override is proven
> loaded and used, and no stiction occurred. See "Spin recovery" above.

---

## IMU — GY-521 / MPU6050 (D-25, 18 Sep 2026) — **NOTHING MEASURED YET**

Fitted by the user 18 Sep on the ESP32's I2C bus (SDA GPIO21, SCL GPIO19,
address 0x68; `esp-motor-firmware/config.h`). Read through the firmware's `i`
command, published as `/imu_broad/imu` in frame `imu_link`, fused by
`robot_localization` when `make real USE_IMU=true USE_EKF=true`.

**MEASURED 2026-09-18** with `scripts/imu_check.py`, firmware `6c487ef`
flashed, 10 s at rest on a level floor with the motors off, then the axes
flag for the orientation. Both are installed.

| Quantity | Value | Where it goes | Method |
|---|---|---|---|
| Gyro bias, raw counts (131 per °/s) | **x −105.5 · y +238.4 · z −81.6** = −0.805 / +1.820 / −0.623 °/s | `ros2_control.xacro` `imu_gyro_bias_*` ✅ installed | 10 s at rest, motors off, 18 Sep |
| Gyro σ per axis (rad/s) | **x 0.00171 · y 0.00145 · z 0.00112** (z = 0.064 °/s), var z **1.25e−06** | `my_controllers.yaml` `imu_broad.static_covariance_angular_velocity` = **1e−5** (8× σ²_z) ✅ installed | same run |
| Raw→body axis map | **identity** — body +x = raw +x, +y = raw +y, +z = raw +z; det +1, proper rotation → **rpy 0 0 0** | `imu.xacro` joint `rpy` ✅ installed (now measured, was assumed) | axes flag: CCW turn, nose-down, left-side-down, by hand, 18 Sep |
| `i` round-trip p50 / p95 | **not recorded** — the script printed it, it was not kept. Superseded in practice by `/joint_states` staying at 30.0 Hz with `USE_IMU=true`, which is the test that matters | `imu_poll_divisor` if p95 > ~10 ms | same run |
| Gyro σ with the **motors running** | **NOT MEASURED** — this is why the installed covariance is 8× the rest figure and not the rest figure | as above | `imu_check.py` on blocks with the motors turning under `o` |
| Mount position (from axle, lateral, height) | 0.0 / 0.0 / 0.10 — **placeholder, deliberately not chased** | `imu.xacro` properties | tape. Affects only the RViz box: ω is identical everywhere on a rigid body and accel is not fused |
| `map → odom` correction total-path, EKF off / on | **NOT MEASURED** | D-25 result | `check_pose_stability.py --seconds 30` during the Day 3 loop, both flags |
| Yaw under induced slip, `odom → base_link` vs `map → base_footprint`, EKF off / on | **NOT MEASURED** | the report's D-23 figure | wedge the robot, log both TF yaws |

> **Qualitative, not a measurement (reported by the user 24 Sep; date of the
> run not recorded):** when the robot turned and got caught on an obstacle —
> wheels turning, body not — the map **skewed with the EKF off and did not
> skew with it on.** That is the slip case this row exists for, observed but
> not logged. Do not quote it as a number; it is the reason objective 1 is
> measured with the EKF on (D-31).

> ⚠ **The signs are the fragile part, and one was already lost once.** The
> biases are *subtracted*, so a dropped sign does not merely fail to correct
> the bias — it doubles it. `+81.6` was pasted for z where the run said
> `−81.6`, which would have given −1.246 °/s of phantom yaw (**75 °/min** of
> heading drift standing still) against 37 °/min uncorrected. Caught the same
> day by re-deriving the table from the script's output. **Copy the script's
> `gyro bias (raw)` line verbatim; do not retype it.**

> **σ_z = 0.064 °/s is also a firmware check, not just a covariance.** With
> the MPU6050's DLPF at its power-on default (off, 256 Hz bandwidth, 8 kHz
> internal rate) 30 Hz sampling aliases motor and chassis noise, and this
> figure would be several times larger. A quiet rest σ is the cheap
> confirmation that `6c487ef` is the firmware actually running.

### Live verification on the fused stack — 18 Sep 2026, evening

`make real USE_EKF=true` (which implies the IMU: `use_imu:=false
use_ekf:=true` was what actually ran, and the launch's `imu_on` expression
turned the polling on — verified from the process command line). Robot
stationary on the floor, motors energised, 30 s samples.

| Quantity | Measured | Verdict |
|---|---|---|
| `/joint_states` | **29.996 Hz** | ✅ the serial budget fits. This is the test that mattered: `i` costs ~8 ms of a 33 ms frame and the loop did not slip |
| `/imu_broad/imu` | **30.00 Hz**, inter-arrival p50 33.3 / p95 34.3 / max 35.3 ms, **zero gaps > 50 ms** | ✅ no dropped polls. An early `ros2 topic hz` showed max 0.343 s; that was startup only and did not recur |
| `/diff_cont/odom` · `/odometry/filtered` | 30.016 · 30.007 Hz | ✅ |
| Controllers | `diff_cont`, `joint_broad`, `imu_broad` all **active**; all 10 IMU interfaces claimed | ✅ |
| `diff_cont enable_odom_tf` | **False** | ✅ the spawner `--param-file` override applied; the EKF owns `odom → base_link` |
| **Bias subtraction, end to end** | `/imu_broad/imu` wz mean **−0.00015 rad/s** (−0.009 °/s) where uncorrected is −0.01087 | ✅ the xacro param reaches the hardware interface and is applied |
| **Stationary yaw drift, `/odometry/filtered`** | **+0.028° net over 30 s = +0.06 °/min** | ✅ **the headline number.** 0.6° over a ten-minute demo |
| `\|a\|` | **0.999 g** | ✅ confirms the ±2 g range and the 16384 LSB/g scaling |
| Accel z tilt from vertical | **3.2°** (ax +0.521, ay +0.165, az +9.786 m/s²) | recorded, **not applied** — see below |
| `frame_id` · orientation · `orientation_covariance[0]` | `imu_link` · identity · **−1.0** | ✅ correctly flagged "no orientation estimate" |

> ⚠ **The rest-noise figure was wrong for this purpose, by 11×, and the
> filter told us so.** Gyro σ_z on the running stack is **0.01053 rad/s**
> (variance **1.11e−04**) against **0.00112** (1.25e−06) at rest with the
> stack down — same chip, same room, eight minutes apart. Energising the
> drive is most of the difference, and that is the condition the robot is
> always in when the number is used.
>
> The covariance had been installed at **1e−5** on the strength of the rest
> figure, and the symptom was specific: **`/odometry/filtered`'s vyaw σ came
> back 0.01023 against the raw gyro's 0.01053 — the filter was doing no
> smoothing at all**, tracking gyro noise 1:1, and putting **14.8° of total
> yaw path** into a stationary 30 s window whose net drift was 0.028°.
> Now installed at **1e−4**, the measured value, which restores D-25's
> intended **100:1** gyro-to-wheel ratio. Slip rejection is unaffected:
> 100:1 already means a slipping wheel cannot move the heading estimate.

### `DLPF_CFG` 3 → 4, flashed 18 Sep 2026 late evening

`IMU_DLPF_CFG = 4` in `esp-motor-firmware/config.h` (20 Hz gyro / 21 Hz
accel, 8.3 ms group delay, was 42 Hz / 4.8 ms). Compiled 311287 bytes,
uploaded to `/dev/esp32`, hash verified. Firmware `a9e4f8c`.

Re-measured at rest, motors off, stack down, 20 s:

| | DLPF=3, 18 Sep earlier | DLPF=4, after reflash |
|---|---|---|
| Gyro σ x / y / z (rad/s) | 0.00171 / 0.00145 / **0.00112** | 0.00144 / 0.00097 / **0.00114** |
| Sample rate achieved | 19.3 Hz — **invalid, see below** | **30.1 Hz** |
| `i` round trip p50 / p95 | 51.7 / 52.3 ms — **invalid** | **6.6 / 6.8 ms** |
| `\|a\|` · tilt | 0.999 g · 3.2° | 0.999 g · 3.2° |

> ⚠ **A defect in `imu_check.py` invalidated every round-trip figure it has
> ever printed.** `read_line` called `ser.read(64)`; pyserial waits for **64
> bytes or the port timeout**, and a reply is ~30 bytes, so every exchange
> burned the full 50 ms. The 51.7 ms p50 was therefore a measurement of the
> script's own timeout, not of the firmware, and the 19.3 Hz ceiling was the
> same thing. Fixed: read `in_waiting` (or one byte) and return the instant
> the terminator arrives — 6.6 ms p50 afterwards, which matches the ~8 ms
> predicted from the byte count. **The other bring-up scripts share the same
> `read_line` shape but poll at 10 Hz, where 50 ms per exchange never
> mattered; they are left alone.**

> ❓ **The σ_z = 0.330 °/s reading in that same run is UNEXPLAINED, and it
> should not be written off as the script bug.** The tempting story —
> undersampling at 19.3 Hz drops Nyquist to 9.7 Hz and aliases more — does
> not survive contact with the data: **the earlier `DLPF_CFG=3` run was
> undersampled by exactly the same bug and read 0.064 °/s.** Same script,
> same ceiling, 5× different answer. So undersampling alone cannot account
> for it.
>
> What is established: 0.330 °/s **did not reproduce** at a true 30 Hz
> (0.065 °/s, and all four verdicts PASS). What is not established: what it
> was. The run followed a `colcon build`, an `arduino-cli compile` and a
> reflash, so the Jetson's fan was at high RPM and the ESP32 had just reset
> — a transient chassis vibration is plausible and unproven. **If a stray
> high-σ reading recurs, this is the note to come back to**; the thing that
> would settle it is two back-to-back runs in the same thermal state.
> Recorded as an open loose end rather than a closed one.

> **What the reflash did and did not buy.** At rest it changed nothing
> measurable — 0.00114 against 0.00112 rad/s — and that is expected: with
> the drive unpowered there is almost no broadband vibration to alias, so a
> narrower filter has nothing to remove. **The case it targets is
> motors-energised, and there it worked — measured below.**

### `DLPF_CFG=4` on the running stack, and the covariance set from it

`make real USE_EKF=true`, robot stationary on the floor, drive energised,
30 s windows. **This is the condition the covariance is used in and the only
one it should ever be measured in.**

| | DLPF=3, cov 1e−5 | DLPF=3, cov 1e−4 | **DLPF=4, cov 5e−5** |
|---|---|---|---|
| Gyro wz σ (rad/s) | 0.01053 | 0.01053 | **0.00486** |
| Gyro wz variance | 1.11e−04 | 1.11e−04 | **2.31e−05** |
| `/odometry/filtered` vyaw σ | 0.01023 | 0.00392 | 0.00431 |
| **σ ratio filtered/gyro** | **0.97 — no smoothing** | 0.81 | 0.89 |
| Yaw **total path** / 30 s | **14.840°** | 4.320° | 5.681° |
| Yaw **net** drift | +0.06 °/min | +0.15 °/min | **+0.01 °/min** |

> ✅ **The aliasing diagnosis is CONFIRMED. `DLPF_CFG` 3 → 4 cut the gyro
> variance 4.8×** (σ 2.19×, 0.603 → 0.276 °/s) with the drive energised,
> while changing nothing at rest. That is exactly the signature of
> undersampling: 42 Hz of bandwidth against a 30 Hz poll folds everything
> above the 15 Hz Nyquist back into the reading, and it only shows when
> there is broadband vibration present to fold. Yaw jitter fell **3.4×**.

**Installed: `static_covariance_angular_velocity` = 5e−5**, about 2× the
measured 2.31e−05. The padding covers **one named unknown and no more**:
the robot was stationary, so vibration from the wheels actually turning is
not in the figure. Gyro outvotes wheel yaw rate **200:1**.

> **The jitter went UP from 1e−4 to 5e−5 (4.32° → 5.68°), and that was
> predicted, not a regression.** Lowering a measurement covariance tells the
> filter to trust the sensor more, so it smooths less. 1e−4 bought smoother
> output by asserting the gyro was 4.3× noisier than measured — the same
> class of error as the 1e−5 that started all this, in the other direction.
> Smoothing is the process model's job, not a lie about the sensor.

> ⚠ **AT STANDSTILL THE EKF IS STRICTLY WORSE THAN WHEEL ODOMETRY, and the
> report should say so.** `/diff_cont/odom` yaw path over the same 30 s is
> **0.000°** with σ exactly 0 — stationary encoders cannot report rotation,
> so wheel odometry is *perfect* in precisely this case, and the EKF adds
> 5.7° of random-walk yaw path to it. **This is not an argument against the
> EKF; it is the observation that its entire value is in the case that has
> not been measured yet** — driving, and specifically slip, where the wheels
> report rotation that did not happen and the gyro does not. The standstill
> comparison flatters the wheels by construction.
>
> Two consequences worth carrying into the Day 3 run:
> - **D-18 narrowed the scan matcher's window on the premise that the
>   odometry prior is quiet** (~0.01° per 0.2 m keyframe). The EKF's prior
>   carries ~0.25° RMS of jitter, i.e. ~2.5 % of the ±10° window — far from
>   exhausting it, but no longer negligible against the figure D-18 quoted.
>   `check_pose_stability.py` run **both ways** is what settles whether this
>   costs or buys anything.
> - The semantic layer's motion gate is **unaffected**: it reads ω from
>   `/diff_cont/odom`, not the EKF, and σ 0.0043 rad/s is far below
>   `motion.max_omega` 0.3 anyway.

### `odom_check.py --compare` — hand-push, wheels against the EKF, 18 Sep

Robot pushed ~1.1 m by hand and turned ~90°, stack up with `use_ekf:=true`,
`odom_check.py` commanding nothing. `--compare` was added for this (D-25):
the default invocation watches only `/diff_cont/odom`, which the EKF does not
touch, so it cannot say anything about the fusion.

| | wheels (`/diff_cont/odom`) | EKF (`/odometry/filtered`) | agreement |
|---|---|---|---|
| straight-line | **1.127 m** | **1.116 m** | **−11 mm, −0.98 %** |
| dyaw | **−87.9°** | **−92.2°** | **−4.3°, −4.9 %** |
| dx / dy | +1.109 / −0.199 | −0.131 / −1.108 | frame-rotated, expected |

> ✅ **THE YAW SIGNS AGREE.** This is the single most important result of the
> run. A gyro fused with the wrong yaw sign is invisible in TF, invisible in
> RViz, and makes the EKF worse than no EKF — and it is what `imu.xacro`'s
> measured rpy exists to prevent. The axis identification was done on a
> stationary robot by hand; **this confirms it on real rotation with the
> whole chain live.** `--compare` fails loudly on opposite signs.

> ✅ **Distance agrees to 0.98 %.** The EKF is not corrupting a working
> estimate, and the twist covariances in `my_controllers.yaml` are not
> obviously wrong (the EKF fuses only vx and vyaw, so a large distance
> disagreement would have pointed straight at them).

> **The 4.3° of yaw disagreement is NOT resolvable from this run, and should
> not be quoted as either sensor's error.** Against a nominal 90° the wheels
> read −2.3 % and the gyro +2.4 %, but the true angle was a hand turn and is
> unknown, so neither figure is an error measurement. Three candidates, none
> separable here:
> - **Gyro scale factor.** The MPU6050's sensitivity tolerance is ±3 %
>   typical, so +2.4 % is *inside spec* and needs no explanation.
> - **Wheel skid during the turn**, which makes the wheels under-read.
> - `wheel_separation` 0.25168, which sets the wheels' yaw scale.
>
> The mount tilt is **not** a candidate: 3.2° costs cos(3.2°) = 0.9984,
> i.e. −0.16 %. What would separate them is `calibrate_spin.py` under power
> against a floor mark, with the gyro logged alongside — Day 3 work, and
> worth doing because it would calibrate the gyro scale for free.

> ⚠ **An earlier attempt at this run recorded something worth keeping: the
> EKF turned through −86.4° while the wheels registered −0.6°.** The yaw
> then stopped changing rather than continuing, so it was **an event, not
> drift** — and stationary drift measured minutes earlier was +0.01 °/min,
> 140× too small to account for it. The likely cause is the robot being
> lifted or pivoted so the wheels did not roll; **that is inference, not
> established.** Two things follow regardless:
> - It is the closest thing yet seen to the **slip signature** — real
>   rotation that wheel odometry is completely blind to and the gyro catches.
>   It is *not* a controlled test and must not be reported as one.
> - **Repositioning this robot by hand desynchronises the EKF's heading from
>   the wheels' permanently**, because the EKF integrates the gyro through
>   the lift and the encoders see nothing. `slam_toolbox` absorbs it into
>   `map → odom`, so it is survivable — but do not lift the robot mid-run
>   and expect `odom` to still mean anything.

> **A defect in `--compare` hid 68 s of that first run and is fixed.** The
> progress trace only printed when the *wheels* had moved enough to be worth
> a line, so an EKF-only divergence produced no output at all — exactly
> backwards, since disagreement is the whole point of the mode. The trigger
> now tests both tracks.

> **Gyro σ repeats across two runs on the running stack** — 0.00481 and
> 0.00486 rad/s, 1 % apart. The noise figure is stable; it is the *condition*
> (rest vs energised) that moves it, not run-to-run scatter.

> ✅ **The 85× motors-off/motors-energised gap survives the script fix**, so
> the covariance decision below still stands on solid ground: rest σ_z at a
> true 30 Hz is 0.00114 rad/s (var 1.30e−06) against **0.01053** (1.11e−04)
> on the running stack. The live figure came through the C++ hardware
> interface, not through the script, so it was never affected by the bug.

> ✅ **Serial budget, now measured instead of estimated.** `i` costs
> **6.6 ms p50** (predicted ~8) on top of ~6 ms for the encoder and motor
> exchanges: **~13 ms of a 33.3 ms frame**, which is why `/joint_states`
> holds 29.996 Hz.

> ✅ **Gyro bias is repeatable across three runs**, which is the evidence
> that it is a constant worth subtracting rather than a drifting quantity:
> z reads **−81.6 / −82.2 / −81.5** raw, a spread of 0.7 counts
> (0.005 °/s, 0.32 °/min). x spreads 2.9 counts and y 1.1.
> **The installed values are kept unchanged.** The largest disagreement on z
> — the only axis the EKF fuses — is 0.27 °/min, far below anything that
> matters, and churning a calibration by less than its own repeatability is
> how noise gets recorded as a measurement (same reasoning that left
> `wheel_radius` at 0.0327). x and y are not fused at all under
> `two_d_mode`.

> **The noise is aliasing, and that is fixable in firmware — highest-value
> next step.** σ = 0.6 °/s is high for an MPU6050 behind a filter. The cause
> is the sample-rate mismatch: `DLPF_CFG=3` gives **42 Hz** of gyro
> bandwidth, but the host polls at **30 Hz**, so Nyquist is 15 Hz and
> everything from 15 to 42 Hz folds back into the reading. The chip samples
> internally at 1 kHz and we decimate by reading one register set per frame,
> with no averaging.
>
> Two ways to fix it honestly, either of which should be followed by
> re-running `imu_check.py` and letting the covariance come down to whatever
> it then measures:
> - **`DLPF_CFG=4`** (20 Hz bandwidth, 8.3 ms group delay) — one constant in
>   `config.h`, reflash. `DLPF_CFG=5` (10 Hz) is properly below Nyquist but
>   costs 13.4 ms of lag in the heading estimate, which is half a control
>   frame. **4 is the sweet spot; do not go past 5.**
> - **Average in firmware**: read the chip several times per frame and mean
>   them. Strictly better than a lower DLPF (no added group delay) but it is
>   real work on the `i` command and its timing budget.
>
> Until one of those happens, **1e−4 is the honest covariance** and the
> stationary drift of 0.06 °/min says the EKF is already doing its job.

> **On the 3.2° mount tilt: measured, deliberately not applied.** A tilt
> means the gyro's z axis is not exactly vertical, so world yaw rate projects
> onto it as ω·cos(3.2°) — a **0.16 % scale error** on yaw rate. That is a
> quarter of the `wheel_separation` correction that *was* worth applying
> (0.67 %) and far below the 11× noise question above. Putting it in
> `imu.xacro`'s rpy would also fold in however level the floor was, not just
> the mount. Same reasoning that left `wheel_radius` at 0.0327: applying a
> correction smaller than the uncertainty in its own measurement records
> noise as a calibration.

> **On the axis map reading 0 0 0.** The value is unchanged from the
> placeholder, and that is not the same as the measurement being redundant:
> before 18 Sep it was an assertion about a silkscreen, and now it is a
> result with a determinant check behind it. The lidar's `reversion` /
> `inverted` flags are the precedent — both also "looked right" and both
> cost days. Re-run the axes flag after any remount.

Fixed by construction, not measured: ±250 °/s (131 LSB per °/s), ±2 g
(16384 LSB per g), DLPF_CFG 3 (44 Hz accel / 42 Hz gyro) — the firmware writes
these on every boot since `6c487ef`. Covariance split in the fusion: gyro vyaw
**1e-4** against wheel vyaw **1e-2** (`config/ekf.yaml`,
`config/my_controllers.yaml`).

Serial budget with the IMU on, computed not measured: encoder + motor exchange
~32 B ≈ 5.6 ms; `i` + reply ~45 B ≈ 7.8 ms; total ≈ 13.4 ms of the 33.3 ms
frame at 57600 baud. The number that says whether it fits is `/joint_states`
staying at **30.0 Hz** with `USE_IMU=true`.

---

## Concurrent detection rate — **MEASURED 2026-09-22, from the demo bag**

The report's objective 3 asks for ≥ 5 FPS of detection **while SLAM is
running**. `~/bags/2026-09-22-163401` is a 215.28 s window of the full stack,
and the concurrency is in the bag rather than asserted: `/scan` flowing and
`/map` republishing in the same window is SLAM working.

| topic | messages | rate |
|---|---|---|
| `/detections` | 2 809 | **13.05 Hz** |
| `/detections/image` | 2 809 | 13.05 Hz |
| `/image/compressed` | 2 808 | 13.04 Hz |
| `/scan` | 2 497 | 11.60 Hz |
| `/map` | 105 | 0.49 Hz |
| `/semantic_landmarks`, `/semantic_markers` | 402 each | 1.87 Hz |
| `/diff_cont/odom` | 6 257 | 29.06 Hz |
| `/tf` | 19 804 | 91.99 Hz |

**Method:** message counts and duration read from the bag's `metadata.yaml`
(`rosbag2_bagfile_information.duration`), not a live `ros2 topic hz`.

**13.05 Hz is 2.6× the criterion.** Against Day 5's standalone **15.15 Hz
(sd 5 ms over 301 s)**, the ~2 Hz difference is what SLAM, the semantic node
and the recorder cost. Quote the pair, not just the survivor.

> ⚠ These are **recorded** rates: what the recorder wrote, which can only be
> ≤ what was published. They are a lower bound on the true rate, which is the
> safe direction for a criterion, but the table should also carry one live
> `detection_report.py --seconds 300` figure taken during a lap.

**Map from the same session:** `~/maps/day7-run-22sep.pgm`, 666×361 px at
0.05 m/px = 33.3 × 18.1 m of bounding box, origin `[-7.12, -6.70]`. Saved from
`~/my_map` (the Makefile default, which the next bare `make save-map`
overwrites) and copied under a dated name the same day. Walls are single-stroke
at this resolution — no shear visible.

---

## YOLO bench re-run, 23 Sep — why n / s / torch / ONNX looked identical

Re-run because the 16 Sep table (35.4 / 36.6 / 35.4 ms) made every option look
the same. Script: `cap_ws/yolo/bench_yolo.py`, one process per config, 100
timed after 20 warm-up, `bus.jpg` resized to 640×480 (5 detections at conf 0.5),
imgsz 640, nvpmodel 15 W. Fresh ONNX exports of **both** n and s, fp16 and fp32.
Pass 2 used `jetson_clocks` (GPU locked at 624.75 MHz), stored and restored after.

**It is on the GPU — verified, not assumed:** torch parameters read back as
`cuda:0` (fp16 where asked); ORT `session.get_providers()` on ultralytics' own
session = `CUDAExecutionProvider` first; GPU load 45–94 % during runs; the CPU
control (`yolo26s.pt` on cpu) is **1084 ms raw / 1391 ms predict**, ~35× slower.

### Clocks locked (624.75 MHz) — ms, mean

| model | backend | raw forward | predict pre / inf / post | predict wall | track wall | GPU load (raw) |
|---|---|---|---|---|---|---|
| yolo26n | torch fp32 | 46.7 | 1.4 / 30.4 / 3.6 | 36.3 | 59.4 | 45 % |
| yolo26n | torch fp16 | 50.5 | 1.2 / 31.6 / 3.8 | 37.6 | 61.3 | 31 % |
| yolo26n | onnx fp32 | 21.2 | 1.4 / 19.9 / 3.9 | 26.0 | 49.4 | 90 % |
| yolo26n | onnx fp16 | **16.3** | 1.3 / 15.6 / 4.1 | **21.9** | **46.8** | 89 % |
| yolo26s | torch fp32 | 47.0 | 1.3 / 30.9 / 3.5 | 36.7 | 60.3 | 85 % |
| yolo26s | torch fp16 | 52.1 | 1.3 / 32.9 / 3.9 | 39.0 | 63.8 | 50 % |
| yolo26s | onnx fp32 | 37.7 | 1.4 / 36.8 / 4.1 | 43.1 | 66.4 | 94 % |
| yolo26s | onnx fp16 | **27.4** | 1.3 / 27.0 / 4.1 | **33.2** | **56.5** | 93 % |

Default governor (`nvhost_podgov`, as the robot runs): ONNX rows within ~2 ms of
the above (it drives the clock to 625). Torch rows the same wall time but the
governor sat at **306–510 MHz** because torch never loaded the GPU enough to raise it.

### Why they looked the same

1. **Torch is launch-bound.** n and s take the same ~30 ms inference although s
   is ~3.5× the FLOPs; fp16 is no faster (slightly slower); GPU load 31–66 %.
   The time is Python dispatching kernels one by one, not the GPU computing.
   Raw forward (unfused) is *slower* than ultralytics' inference (Conv+BN
   fused) — fewer kernels, less time: same conclusion.
2. **ONNX shows the real model cost.** ORT runs the graph without per-op
   Python; GPU load ~90 %, and n vs s separates: **16.3 vs 27.4 ms** fp16.
3. **`track()` adds ~25–30 ms** of CPU (ByteTrack + Python) to every row,
   and the 16 Sep table measured `track()` wall — that flattens the spread
   further (46.8 → 66.4 ms here, i.e. 21–15 Hz).
4. **Live, the camera caps it at 15 Hz** — every option above is faster than
   66.7 ms per frame, so the live `/detections` rate cannot tell them apart.

**Consistent with 16 Sep:** `yolo26n.pt` torch ≈ `yolo26s.onnx` fp16 (36.3 vs
33.2 ms predict), and ONNX fp32 is slower than torch for `s`. New: `yolo26n.onnx`
fp16 is the fastest at 21.9 ms predict — not adopted; D-22 chose `s` for accuracy
and the camera, not inference, is the ceiling.

### TensorRT via onnxruntime, 23 Sep — measured, NOT adopted

`TensorrtExecutionProvider` (`trt_fp16_enable`, engine + timing cache on) on
the **fp32** ONNX exports, raw `session.run` on a 1×3×640×640 input, 200 timed
after 20 warm-up, `jetson_clocks` locked then restored. Compare with the
"raw forward" column above.

| model | CUDA EP fp16 | **TensorRT EP fp16** | first build |
|---|---|---|---|
| yolo26s | 27.4 ms | **12.3 ms** (sd 0.2) | **531 s** |
| yolo26n | 16.3 ms | **8.3 ms** (sd 0.1) | 398 s |

**End to end, measured** (`yolo26s`, ultralytics `predict()`/`track()` on
`bus.jpg`, clocks locked, two runs each, interleaved; TRT session swapped into
`AutoBackend.backend.session` with outputs rebound to its IO-binding tensors):

| | CUDA EP (onnx fp16) | TensorRT EP fp16 |
|---|---|---|
| inference | 27.0 ms | **10.8 ms** |
| predict wall | 33.1 ms (~30 FPS) | **16.5 ms (~61 FPS)** |
| **track wall** | **58.1–59.0 ms (~17 FPS)** | **42.1–42.3 ms (~24 FPS)** |
| GPU load | 59 % | **40 %** |
| detections | 5: bus + 4 person | **same 5**, conf within 0.001 |
| start, engine cached | — | 2.7 s |

ByteTrack + Python (~26 ms) is now the larger half of `track()`. ultralytics
8.4.144 hard-codes `CUDAExecutionProvider` for `.onnx`
(`nn/backends/onnx.py`), so adopting this means a node change, not a flag.
⚠ A first attempt set `AutoBackend.session` (a proxy) instead of
`.backend.session` and silently kept running CUDA fp32 — 36.8 ms — while
`get_providers()` on the swapped object reported TensorRT. Check `inference`
time, not the provider string.

Not adopted: the camera caps live rate at 15 Hz, so it buys no FPS on this
robot; a lost cache costs a 9-minute build before the first detection; fp16
TRT accuracy unmeasured. Note for D-11/D-22: through ORT the `.onnx` stays the
source and the engine is a rebuildable cache, so a JetPack change costs a
rebuild, not the model — the failure D-11 feared does not apply to this path.

## Objective 2 — detection accuracy (24 Sep 2026)

**macro F1 64.4 %** (precision 96.5 %, recall 52.5 %) → FAIL vs 80 %.
yolo26s ONNX fp16 @ 640, conf 0.5, IoU 0.5, 4 classes, 143 hand-reviewed frames
from bag `2026-09-24-165025`, fixed viewpoint (D-27). Per-class table, method and
the recall-by-size breakdown: `records/objective-tests.md` → Objective 2 → Run log.

## Objective 5 — CPU, pre-fix windows and the busy-wait diagnosis (23–24 Sep 2026)

**Windows (23 Sep, `resource_report.py`, `~/maps/resource_session.jsonl`)** — all
of them, per `MEASUREMENT-PLAN.md` §4.3 (no picking the pretty one):

| label | file | s | 6-core mean | GPU | RAM peak | tj max |
|---|---|---|---|---|---|---|
| idle | 211545 | 120 | 0.3 % | 0 % | 1328 MB | 45.2 °C |
| real+slam | 212252 | 120 | 0.8 % | 0 % | 1557 MB | 46.2 °C |
| full stack, driving | 212914 | 5 | 90.8 % | 52 % | 3321 MB | 48.0 °C — stub, discard |
| full stack, driving | 213525 | 356 | 76.3 % | 46 % | 3762 MB | 51.7 °C |
| full stack, driving | **214529** | **596** | **81.5 % ✗** | 52 % | 3852 MB | 55.7 °C |

214529 is the longest and the one to report as the pre-fix figure. Load is even
across cores (80.6–82.9 %), so there is no single busy core.

**Who (24 Sep 17:16, live stack, `top -H -p`):** `yolo_detector.py` **371 %**, 28
threads — **5 threads at a steady ~40 % each, state R**, identical cumulative
time; main thread 23 %. Others: cam2image 18 %, image_transport republish 6.5 %,
`update-manager` 14 % (GUI, close it before measuring).

**Which pool (24 Sep, offline, `bus.jpg` at 640×480, `model.track()` paced at
1/15 s sleep, 90 frames, yolo26s.onnx CUDA EP; per-thread ticks from
`/proc/self/task`):**

| setting | process CPU | busiest threads | rate |
|---|---|---|---|
| default | **263 %** | 46 46 46 46 45 33 | 6.4 Hz |
| ORT `intra_op_num_threads=1`, `allow_spinning=0` | 258 % | 46 46 45 45 45 32 | 6.5 Hz |
| `OMP_NUM_THREADS=1` | 38 % | 38 | 6.3 Hz |
| **`OPENBLAS_NUM_THREADS=1`** | **38 %** | 38 | 6.3 Hz |

A random-noise frame (0 detections) costs 35 % with default settings, so the
spinning only happens while something is being tracked. It is **numpy's OpenBLAS pool**,
woken by ByteTrack's per-frame matrix maths and busy-waiting between frames,
**not onnxruntime**. The rate here is 6 Hz rather than the robot's 13 because
of the bench pacing and board state. It is the same across settings, which is the
point. Fix: `OPENBLAS_NUM_THREADS=1` in `yolo.launch.py` (D-28). Post-fix
full-stack window: see the next section.

## Objective 5 — CPU, post-fix window (24 Sep 2026) — **PASS, 55.8 %**

`resource_report.py`, 596 s, label `full stack, driving`, CSV
`~/maps/resource_samples/20260924-200759.csv` (19:58:03 → 20:07:59). Stack
launched 19:55–19:57, after `c4b874d` (OPENBLAS fix, 17:31) and `07370da`
(D-30, yolo26l TRT fp16 480×640 conf 0.4, 19:16). **The model is inferred from
the launch time, not logged** — the label does not say yolo26l.

The window is **not one clean run**. Launch logs in `~/.ros/log` show it:

| t (s) | what was up | n | 6-core mean | p95 | max | GPU | busiest core |
|---|---|---|---|---|---|---|---|
| 0–129 | full stack (yolo #1) | 128 | 57.7 % | 73.3 | 87.5 | 48 % | 60.8 % |
| 129–175 | yolo Ctrl-C'd 20:00:12, relaunched 20:00:46 + engine load | 45 | 42.4 % | 74.5 | 77.5 | 5 % | — |
| 175–521 | full stack (yolo #2), steady | 344 | 55.1 % | 64.7 | 85.0 | 49 % | 59.4 % |
| 521–596 | yolo + semantic stopped 20:06:44; real+slam only | 79 | 7.4 % | — | — | 3 % | — |
| **whole file as logged** | | 596 | *48.4 %* | 67.2 | 87.5 | 39 % | 51.8 % |

**Figure to report: 55.8 %** = every sample with the full stack up (rows 1 + 3,
n = 472). The 48.4 % in `resource_session.jsonl` is diluted by the gap and the
stack-off tail — do not quote it. Full-stack portion: RAM peak 2915 MB (pre-fix
3852), 8.3 W mean (pre-fix 9.0), tj max 53.1 °C, 1.4 % of samples above 80 %,
no single-core bottleneck (busiest core mean ≤ 61 %).

**Pre → post is two changes at once** (OpenBLAS threads *and* yolo26s ONNX →
yolo26l TRT), **but the model's share is negligible.** In core-equivalents
(6-core mean × 6): 81.5 % ≈ 4.9 cores → 55.8 % ≈ 3.35 cores, a drop of ~1.5
cores. The busy-waiting OpenBLAS threads were ~2 cores (5 × ~40 %, `top -H`
above). The model swap is 72 % → 67 % of one core, both measured with
`OPENBLAS_NUM_THREADS=1` (`records/objective-tests.md`, cost table), so ~0.05
core. **The drop is the OpenBLAS fix.** The ~0.5 core by which the drop falls
short of the ~2 spinning cores is not accounted for. Likely causes are that the
spin only happens while something is tracked (the pre-fix window itself ran
92 % → 59 % as the scene changed), and that `update-manager` (14 %) may have
been open pre-fix.
Not known from the files: whether the robot drove the whole window, and
whether `update-manager` was closed.

Figure `figures/resource_usage.png` (report `fig:resource`, table `tab:obj5`):

```bash
cd ~/cap_ws/src/my_bot/scripts
python3 plot_objectives.py resource --series 20260924-200759 --exclude 129:175 --exclude 521: \
  --bar-label "20260923-211545=ขณะว่าง" --bar-label "20260923-212252=ฐานหุ่นยนต์ + SLAM" \
  --bar-label "20260923-213525=ทั้งระบบ ก่อนแก้ (รอบ 1)" \
  --bar-label "20260923-214529=ทั้งระบบ ก่อนแก้ (รอบ 2)" \
  --bar-label "20260924-200759=ทั้งระบบ หลังแก้"
```

Full-stack portion (472 samples) for the table: GPU 48.9 %, 8.25 W, p95 68.8 %,
busiest core 59.8 %. The 5 s stub (212914) is dropped by `--min-seconds 30`.

## yolo26m TensorRT fp16 engine (24 Sep 2026) — for D-28

Built on this board: `YOLO("yolo26m.pt").export(format="engine", half=True,
imgsz=640, batch=1, dynamic=False)`, `YOLO_OFFLINE=1`, TensorRT 10.3 →
`~/yolo/yolo26m.engine` (42 MB). **Build ≈ 14 min** (17:44–17:58, with the
yolo26s node running on the GPU alongside).

| | yolo26m `.pt` (torch) | **yolo26m `.engine` fp16** | yolo26s `.onnx` fp16 (deployed) |
|---|---:|---:|---:|
| macro F1 @ conf 0.5, D-27 validation set, no tracker | 67.4 % | **65.6 %** | — (66.3 % as `.pt`) |
| macro P / R | 96.8 / 54.7 | 95.3 / 52.7 | |
| `track()` wall, real frame, 60 after 10 warm-up | | **60.2 ms mean, ~17 FPS** | 57.0 ms, ~18 FPS |
| inference | | 30.1 ms | 33.4 ms |

Timing taken with the yolo26s node still running on the GPU, clocks not locked
— comparative, not absolute. fp16 TRT costs ~1.8 F1 points against the `.pt` on
these frames. The camera caps live rate at 15 Hz either way.

### The accuracy loss is the square input, not TensorRT (24 Sep)

Same 143 validation frames, yolo26m, no tracker:

| backend / input | F1 @ 0.5 | F1 @ 0.25 |
|---|---:|---:|
| `.pt` (ultralytics letterboxes 640×480 → **480×640**, no padding) | 67.4 % | 79.8 % |
| `.onnx` fp32, static **640×640** | 65.5 % | 76.0 % |
| `.engine` fp16, static **640×640** | 65.6 % | 76.2 % |
| `.onnx` fp32, static **480×640** | **67.4 %** | **79.8 %** — identical to `.pt` |

Paired boxes (IoU > 0.9) differ in confidence by −0.003 mean between engine
and `.pt`: fp16 costs nothing measurable. What costs ~2 F1 points (~4 at 0.25)
is exporting at 640×640, which pads the camera's 640×480 frame with 160 rows of
grey. **This applies to the deployed `yolo26s.onnx` too** (64.4 % in the D-27
score). Export at `imgsz=(480, 640)`; ultralytics reads the baked-in shape from
the model's metadata and uses it even when the node passes `imgsz=640`
(verified: `predictor.imgsz` → `[480, 640]`), so no node change is needed.

### Objective 2 after tuning (24 Sep 2026) — D-29

yolo26l `.engine` fp16 480×640, **conf 0.4 → macro F1 82.2 %** (P 96.2 / R 75.1)
on the D-27 set, offline, no tracker. Tuned on the same frames (no held-out
test). Baseline yolo26s ONNX conf 0.5: 64.4 %. Details: `records/decisions.md` D-29.

### yolo26l engine live on the camera, standalone (24 Sep 2026, 18:58)

`make yolo MODEL=$HOME/yolo/yolo26l_480x640.engine CONF=0.4`, real camera
(cam2image 640×480 @ 15), nothing else running. Node log, 5 s windows over
~40 s: **15.1–15.2 Hz** (camera-limited — every frame processed),
infer+track p50 **40.9–50.9 ms**, max 57 ms after the first window (86 ms
first window, warm-up); age@publish p50 44–54 ms. Load 363 ms, warm-up 2.4 s;
`imgsz [480, 640] (from the model)` confirmed in the log.
**Not objective 3's condition** (SLAM running) — that run is still owed.

### Objective 3 with yolo26l engine and SLAM running — **15.16 Hz, PASS** (24 Sep 2026, ~19:05)

Stack (tmux session `meas`): `make real` · `make slam` (Registering sensor,
`map → base_footprint` live) · `make semantic` (fusing) · `make yolo
MODEL=$HOME/yolo/yolo26l_480x640.engine CONF=0.4`. Robot stationary, no teleop,
no Nav2, no bag recording, no RViz. `/scan` 11.5 Hz.
`ros2 run my_bot detection_report.py --seconds 120`:

| | |
|---|---|
| rate | **15.16 Hz** (1787 msgs, inter-arrival 66.0 ms mean, sd 5.2 ms, max 105 ms) — camera-limited |
| age capture→receipt | p50 57 ms, p95 79 ms, max 121 ms |
| dets | 1.74 / frame; chair ×2068, person ×1046 |
| tracks | 1 persistent (chair, 100 % of window) |
| GPU | load mean 51 %, clock 408 of 625 MHz ceiling |
| tj | max 54.6 °C |

Compared with the earlier 13.05 Hz (yolo26s ONNX, 22 Sep demo bag, full stack
*and the recorder*, robot driving): conditions differ — this run had no Nav2,
no recorder and a stationary robot — so the pair shows the criterion is met
with margin, not that yolo26l is faster.

## Objective 4 — object position, chair, four passes (24 Sep 2026, 20:52–21:02) — **PASS, worst 33.8 cm**

Method: `MEASUREMENT-PLAN.md` §2.2, `object_accuracy.py` (tape from the drive-axle
midpoint, robot frame; 30 s still per pass; criterion 50 cm). Stack: `make real`
· `make slam` · `make semantic` · `make yolo` (yolo26l TensorRT, conf 0.4).
Landmarks were **not** cleared between passes. Raw rows: `~/maps/object_accuracy.jsonl`.

| Pass | Tape (fwd, left) | System (fwd, left) | Error | Spread in window | Landmark map (x, y) |
|---|---|---|---|---|---|
| front | (+1.60, +0.00) | (+1.667, −0.023) | **7.4 cm** | 16.0 cm | (+1.673, +0.042) |
| right | (+1.60, +0.00) | (+1.503, −0.221) | **24.8 cm** | 14.3 cm | (+1.517, −0.178) |
| back  | (+1.458, +0.00) | (+1.347, −0.319) | **33.8 cm** | 11.2 cm | (+1.838, −0.229) |
| left  | (+1.70, +0.12) | (+1.783, +0.084) | **9.0 cm** | 10.0 cm | (+2.048, −0.131) |

| Metric | Value |
|---|---|
| Mean error | **18.8 cm** |
| Worst error | **33.8 cm** (back) against 50 cm → **PASS** |
| Across-pass spread of the mapped position | 27.9 cm |
| Landmark id | `783d3c01` in all four → **one landmark, no duplicates** across viewpoints |

**Report from `~/maps/object_accuracy_chair_final.jsonl`**:
`object_accuracy.py chair --summary --session ~/maps/object_accuracy_chair_final.jsonl`
reproduces the table above. The default session file also holds an earlier
`front` pass (20:50, id `e6e5e439`) that the plan's re-measured front replaces,
plus suitcase passes, so its plain `--summary` is not this set.

**The 27.9 cm spread is viewpoint dependence in practice, not convergence**, even
though the id did not change. The store's EMA is α = 0.3 *per fusion*, and the
node fused tens of detections per 5 s during each pass, so the previous view's
weight is < 1 % after ~13 fusions (1–2 s). Each 30 s window is effectively a
fresh estimate from that side. What the unchanged id proves is the merge: one
chair stayed one landmark from all four sides.

Method note: the UI shows **map-frame** coordinates (origin = where SLAM
started). `--fwd/--left` are **robot-frame** tape pulls. The two coincide only
while the robot is at the SLAM start pose, so never take `--fwd/--left` from the UI.

The back error is mostly **lateral** (left −0.32 m, fwd −0.11 m). The right pass
errs sideways too (−0.22 m). Not diagnosed.



## Objective 1 — SLAM position error, 24–25 Sep 2026 (round D)

Marks HOME (0,0), A (5,0), B (5,3.5), C (0,3.5), tape from HOME along a rope;
area 5 × 3.5 m (criterion asks 5 × 5). `make real` (EKF off, D-31 reversed),
`make slam`, teleop 0.10 m/s. Files in `~/maps/`:

| file | what | ABSOLUTE | ALIGNED | REPEAT | scale | rot |
|---|---|---|---|---|---|---|
| `_0924a` | 2 marks, session abandoned | — | — | — | — | — |
| `_0924b` | 1 lap, **lidar blind −150°..0°** (0 % returns; cleaned + replugged 23:43) | 26.0 cm | 26.2 cm | 6.8 cm | −3.4 % | −0.23° |
| `_0924c` | 1 lap, lidar full circle, `wheel_radius` 0.0327 | **15.9 cm** | **13.6 cm** | **3.2 cm** | **−2.3 %** | +1.16° |

`_0924c` with the fitted scale and rotation both removed: A 1.3, B 2.8, C 5.7,
HOME 6.4 cm — SLAM itself is within 10 cm; the excess is odometry scale leaking
into the map plus the robot's heading at `make slam` (setup, not drift). The
fitted −2.3 % was **not** applied; the radius came from the taped run above.
| `_0925a` | HOME + A only, `wheel_radius` 0.03203 | A 19.2 cm (4.817, 0.061) | — | — | — | — |

| **`_0925b`** | **2 laps**, radius 0.0327, lidar full circle | **34.4 cm** | **16.1 cm** | **25.7 cm** (HOME) | −2.0 % | +1.75° |

`_0925b` per lap: lap 1 worst 22.7 cm (B), HOME return 8.9 cm. **Lap 2 slipped:**
every mark moved +y against lap 1, and between B and C by **+46 cm** (C 3.343 → 3.805);
HOME return 34.4 cm. A pose jump on the B→C leg, not gradual drift. Lap 1 C was
parked facing −x (171.8°), lap 2 C facing +y (92.4°). A at x 4.87–4.89 in every
session since 23 Sep (except the 0.03203 lap) — a fixed ~12 cm, cause open
(tape truth vs lidar scale; lidar read a wall at 3.01 m, tape value not given).

| **`_0925c`** | **HOME → A → B → C, 1 lap, no HOME return** (battery died after C; Jetson rebooted, session lost), radius 0.0327, truths **A (4.85, 0) B (4.85, 3.5) C (0, 3.52)** | **6.4 cm** (A) | **6.5 cm** | — (1 visit each) | pairs mixed sign (−5.3…+5.7 cm): no scale error | −0.02° |

`_0925c` per mark: A 6.4 (dx +5.7, dy +3.0), B 4.1, C 5.3 cm. Truths changed from
A/B x = 5.0 to **4.85** and C y 3.5 → **3.52**. **Confirmed by the user 25 Sep: HOME→A re-taped
(4.85 m). C = 3.52 is the robot's own taped position** — it parked 2 cm off the mark and
could not be squared up closer, so the truth is where the robot was, not where the mark is.
Re-scored with A/B x = 4.85 (C kept at 3.5 — the 3.52 is `_0925c`'s parking only),
`_0924c` is worst 15.9 cm (C) and still fails — see the re-score table below — so the
improvement is not the truth change alone: the start heading was better
(A dy +3.0 cm vs +10.8 in `_0924c`). Not a full lap: the HOME return is missing.

**Earlier laps re-scored, A/B truth x 5.0 → 4.85 (user, 25 Sep: the 5.0 was a taping
mistake, 4.85 is the real distance; applies to every session).** C/HOME truths unchanged.
Via `slam_accuracy_check.py --summary` on copies with the truth edited:

| file | A | B | C | HOME return | ABSOLUTE | ALIGNED | REPEAT |
|---|---|---|---|---|---|---|---|
| `_0924b` (lidar blind) | 3.6 | 15.7 | 15.9 | 13.6 | 15.9 FAIL | 13.8 FAIL | 6.8 |
| `_0924c` | 11.7 | 2.0 | 15.9 | 6.4 | **15.9 FAIL** | **14.1 FAIL** (+0.75°) | 3.2 |
| `_0925b` lap 1 / lap 2 | 10.7 / 16.7 | 8.4 / 15.4 | 21.2 / 31.2 | 8.9 / 34.4 | 34.4 FAIL | 8.8* | 25.7 |
| `_0925c` | 6.4 | 4.1 | 5.3 | — | 6.4 PASS | 6.5 PASS | — |

\* `_0925b` ALIGNED is fitted on each mark's mean over both laps, which averages the
lap-2 jump away — not a pass. `_0924c`'s remaining error is C (dx −8.3, dy −13.6 cm)
and the C–HOME pair reads 3.39 m against 3.50.

**Used in the report as objective 1's result (25 Sep):** `tab:obj1`, `fig:slam-error`
(`figures/slam_error_result.png`, `plot_objectives.py slam --slam-session
~/maps/slam_accuracy_0925c.jsonl`), stated as 3 marks / 1 lap / no HOME return / area
4.85 × 3.52 m, with the earlier over-criterion laps and the 46 cm jump disclosed.

| **`_0925d`** | **HOME → A → B → C → HOME, 1 full lap**, 25 Sep 22:10, **after D-32** (restart time not confirmed), radius 0.0327, `make slam` defaults (no IMU/EKF), truths **A (5.0, 0) B (5.0, 3.5) C (0, 3.5)** | **8.0 cm** (C) | **7.8 cm** (+0.43°) | HOME return 6.5 cm (the only revisit) | all 6 pairs short, −0.4…−7.9 cm; fitted −0.56 % | +0.43° |

`_0925d` per mark: A 7.4 (dx −0.9, dy +7.4), B 2.5, C 8.0 (dy −7.8), HOME return 6.5 (dx +6.5);
mean 6.1 cm. Split out of `~/maps/slam_accuracy.jsonl` lines 24–28 (that file pools five
sessions, 21:33–22:10 — its `--summary` is meaningless as a whole).
**Truth A/B x = 5.0: the user stated 25 Sep late that 5 is correct for this run**, which
contradicts the "4.85 applies to every session" note above; not reconciled. Re-scored at
4.85 this lap would be A 15.9 / B 12.6 cm FAIL. A reads 4.99 here vs 4.87–4.89 in every
earlier session, consistent with the marks having been moved to 5.0.
The same session continued a lap 2 (lines 29–33): A 6.4, B 3.1 cm, then **someone bumped
the robot on B → C** and SLAM never recovered — C 103.4 / 101.8 cm, HOME 93.0 cm, a
persistent ~1 m offset. Excluded at the user's request; not in the report. So the D-32 test
(REPEAT vs `_0925b`'s 25.7 cm) is **inconclusive**: pre-bump A/B repeat is 1.3 cm, but the
near-chain gate only acts on revisits and the lap that exercises it was disturbed.

**Used in the report as objective 1's result (25 Sep late), replacing `_0925c`:** `tab:obj1`
(4 rows incl. HOME return), abstract, summary bullet and `tab:eval` row 1 → 8.0 cm;
`figures/slam_error_result.png` from `plot_objectives.py slam --slam-session
~/maps/slam_accuracy_0925d.jsonl`.

**0.03203 reverted (see Odometry (b)).** Still owed: ≥ 3 laps at 0.0327, and a check of
what makes the map short (lidar range vs a wall at 2–4 m; re-tape HOME → A).
