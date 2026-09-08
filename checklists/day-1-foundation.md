# Day 1 — Foundation, and the truth about the firmware

**Goal:** Jetson runs Humble, both USB devices have stable names, and the ESP32
has been proven to drive wheels under closed-loop control.

**Prerequisite:** none. This is the start.

> ⚠ **Robot on blocks from step 5 onward, and stay there.** An encoder-sign
> error drives the PID to full PWM and holds it there. On blocks that is noise.
> On the ground it is a wall.

---

## 1 · Flash and verify JetPack 6

- [ ] JetPack 6 flashed
- [ ] Verified:

```bash
lsb_release -a          # expect 22.04
uname -r                # expect a tegra kernel
sudo nvpmodel -q        # note the power mode
```

- [ ] Max clocks on — you need them for YOLO later:

```bash
sudo nvpmodel -m 0 && sudo jetson_clocks
```

- [ ] Cooling is actually attached and running. Thermal throttling is risk #6.

## 2 · ROS 2 Humble

> **Superseded by a script.** The apt blocks that were here were written before
> the NVMe dump and installed `ros-humble-usb-cam` — the camera that actually
> ran is `cam2image` from `ros-humble-image-tools`. Nav2 also needs its own
> non-fatal step; see `records/issues.md`, "Nav2 would not install".

```bash
sudo ./scripts/bootstrap-ros-humble.sh
```

- [ ] Script ran; its final "Result" block reports no failures
- [ ] `ros2 topic list` runs after `source /opt/ros/humble/setup.bash`
- [ ] **Nav2 specifically** — `ros2 pkg list | grep nav2_bringup` returns a hit.
      If it does not, stop and log the verbatim apt error in `records/issues.md`
      before doing anything else. Three days of slack now, none on Day 4.

Deliberately **not** installed by the script — all source builds, done on the
day they are needed:

| Package | When | Note |
|---|---|---|
| `ydlidar_ros2_driver` + YDLidar-SDK | Day 1/2 | needs the lidar present |
| `explore_lite` (`m-explore-ros2`) | Day 3 | `make explore` only |
| `yolo_ros` | Day 5 | gated on decision **D-11** |
| `ros_gz_sim`, `gz_ros2_control` | optional | sim is not on the demo path |

## 3 · Repos — before any code exists

Ten minutes, and it is the whole reason this workspace exists.

- [x] `capstone-docs` — this workspace. Pushed to `github.com/mairuu/cap_ref`
      at `18d29d8`. **`recoverable/` is tracked in it**, so the NVMe dump is
      backed up too.
- [x] `semantic-bridge` — `semantic-object/` is tracked in the same repo and
      pushed. Split it into its own remote only if it starts changing.
- [ ] `cap_ws` — created empty, pushed.
- [x] `esp-motor-firmware` — exists at `b0b762b`.
- [ ] `STATE.md` "Repos pushed" table updated.

## 4 · udev rules — re-derive from the hardware

The **values** died with the board, but `scripts/setup_udev.sh` — which walks
this whole section interactively — came back in the NVMe dump. Copy it into
`cap_ws/src/my_bot/scripts/` and run `make udev` rather than doing the
steps below by hand; they are kept as the explanation of what it is doing.

> The recovered `udev/99-my-bot-serial.rules` matched both devices by **USB
> port path** (`KERNELS=="1-2.1"` esp32, `"1-2.2.4"` lidar) because neither
> adapter has a serial. The Advantech carrier has different USB topology, so
> **those paths will not transfer — re-derive them, do not copy the file.**

Full rationale: `RECOVERY.md` §5.1, `reference/nvme-recovery-audit.md`.

> **Assume the ESP32 and the lidar collide on `10c4:ea60`.** Both are likely
> CP210x. A vendor/product rule would match whichever enumerated first.

**One device at a time:**

- [x] Unplug both. Plug in **only the ESP32**:

```bash
ls /dev/ttyUSB*
udevadm info -a -n /dev/ttyUSB0 | grep -E 'idVendor|idProduct|serial' | head -6
```

  Record → `idVendor` **10c4** `idProduct` **ea60** `serial` **0001**

- [x] Unplug. Plug in **only the lidar**. Repeat.

  Record → `idVendor` **10c4** `idProduct` **ea60** `serial` **0001**

- [x] **Do they collide?**  **yes** — and the serial does not save you either:
      both report the *same* `0001`, so `ATTRS{serial}` matches both and the
      rules must fall back to USB port path. Sockets are load-bearing.

- [x] **Be in `dialout` first.** Done 8 Sep; the re-login has happened and
      `id -nG` now lists `dialout`. The recovered `setup_udev.sh` writes
      `GROUP="dialout", MODE="0660"` — **not** the `0666` this checklist used to
      claim. On this board `mic-711` was **not** in `dialout` (checked 8 Sep).
      Without it the symlinks appear and every open fails with permission
      denied, which reads exactly like a dead adapter.

```bash
sudo usermod -aG dialout $USER   # then LOG OUT and back in — newgrp is not enough
                                 # for processes ROS launches
id -nG | tr ' ' '\n' | grep -qx dialout && echo ok
```

- [x] Run the recovered script, with **both devices plugged in**:

```bash
cd ~/cap_ws && make udev
```

> ⚠ **It was answered with the two adapters swapped**, and installed crossed
> names — `/dev/esp32` pointed at the lidar. Nothing failed loudly; the first
> read of `/dev/esp32` just streamed lidar frames forever. Corrected on the wire
> (see `records/issues.md`), and `setup_udev.sh` now checks the operator's
> answers before installing and refuses on a contradiction.

  It probes one adapter at a time, prefers `ATTRS{serial}` and falls back to
  `KERNELS` when the serials collide or are absent, then installs
  `/etc/udev/rules.d/99-my-bot-serial.rules` and leaves a checked-in copy at
  `src/my_bot/udev/99-my-bot-serial.rules`.

  The rules it writes take one of these two shapes:

```udev
SUBSYSTEM=="tty", ATTRS{idVendor}=="10c4", ATTRS{idProduct}=="ea60", ATTRS{serial}=="<ESP32_SERIAL>", SYMLINK+="esp32", GROUP="dialout", MODE="0660"
SUBSYSTEM=="tty", SUBSYSTEMS=="usb", KERNELS=="1-2.3", SYMLINK+="esp32", GROUP="dialout", MODE="0660"
```

  **If it falls back to `KERNELS`** — which is what happened on the old board,
  neither adapter has a serial — the rule becomes a promise about *cabling*.
  **Label the two sockets physically before you walk away.**

- [x] Verify — done 8 Sep, **after** installing the corrected rules (which
      needed sudo and so happened well after they were committed):

```bash
make ports          # both symlinks, and where they point
ls -l /dev/esp32 /dev/ydlidar
```

- [x] Both plugged in together, both symlinks correct — **after the fix**;
      as first generated they were crossed. Correct mapping, measured:
      `1-2.2.1` = ESP32, `1-2.2.4` = lidar.
- [x] Unplug/replug both in the other order — still correct. **Passed 8 Sep**,
      and it is the check that mattered most. They re-enumerated the *other way
      round* — `ttyUSB0` became `1-2.2.1`, `ttyUSB1` became `1-2.2.4`, the
      reverse of first boot — and the names did not follow the numbers. Until a
      replug reverses the order this is untested, because a rule matched on
      anything else looks identical while the order happens to hold.
- [x] Rules file committed — `cap_ws` `6e91aec`. Not pushed: no remote (§3).
- [x] `STATE.md` "Devices" table filled in

## 5 · Firmware validation — the day's real work

`ROADMAP.md` step 5 was only ever checked through `e` and `r`. ~~**The firmware
has never turned a motor.**~~ **It has now — 8 Sep 2026, on blocks, closed
loop.** Full context: `reference/firmware-protocol.md`.

- [x] **Robot on blocks.** Wheels free. Confirmed 8 Sep, and stayed there.
- [x] Nothing holds the port:

```bash
sudo fuser -v /dev/esp32     # must be empty
```

      Not run — it needs a password on this board — but nothing holds it: every
      open of `/dev/ttyUSB1` succeeded, and `micro_ros_agent` is not installed.
- [x] Write `serial_probe.py` and `encoder_report.py` now
      (`reference/scripts-to-rebuild.md`) — you will use them all week.
      Both in `cap_ws/src/my_bot/scripts/`, `6e91aec`. **Use
      `encoder_report.py`, not repeated `serial_probe.py e`, for 5.3 and 5.4:**
      a connect can reboot the board and zero the counts, so only one held-open
      connection accumulates.

Then, **in order, do not skip ahead**:

| # | Send | Expect | Pass | If wrong |
|---|---|---|---|---|
| 5.1 | *power on* | `# boot reset=1 encoders=ok` | **[x]** verbatim, 8 Sep | `encoders=FAIL` → pin problem, go to 5.9 |
| 5.2 | `r` | `OK` | **[x]** 8 Sep; `e` → `0 0` | — |
| 5.3 | spin **left** wheel forward by hand, then `e` | left count **increases** | **[x]** 8 Sep — *driven, not spun; see below* | flip `LEFT_ENC_INVERT` in `config.h`, reflash |
| 5.4 | spin **right** wheel forward by hand, then `e` | right count **increases** | **[x]** 8 Sep — needed `RIGHT_ENC_INVERT=false` | flip `RIGHT_ENC_INVERT`, reflash |
| 5.5 | `o 50 50` | `OK`, both wheels turn **forward** | **[x]** 8 Sep, watched | swap that motor's FORWARD/BACKWARD pins |
| 5.6 | *wait 2 s* | motors stop by themselves | **[x]** 8 Sep — **2.0 s** | auto-stop broken — **do not proceed** |
| 5.7 | `m 20 20` | `OK`, wheels settle at a steady speed | **[x]** 8 Sep — both near **600 ticks/s**, no wind-up | **see below** |
| 5.8 | power-cycle 5× | boots every time | [ ] | GPIO12 strapping issue |

> **5.3–5.7 were done by driving, not by hand-spinning**, with
> `cap_ws/src/my_bot/scripts/motor_check.py`. Hand-spinning tests the encoder
> against your arm; the condition that destroys the robot is the encoder
> disagreeing with its own *motor*. `o` bypasses the PID, so driving under it
> measures that directly and cannot run away — which is what makes it safe
> *before* 5.7 rather than after. The script refuses to reach `m` until the
> open-loop check passes on both sides, and cuts PWM itself at 3x the commanded
> rate. What it cannot judge is whether "forward" is forward: two backwards
> wheels still agree. The operator watched the wheels.
>
> **5.4 failed on the first attempt and that is the point of the step.** With
> the flashed `RIGHT_ENC_INVERT = true` the right count ran backwards against
> its own motor. Flipped to `false`, reflashed, both sides agree.

> ⚠ **5.7 is the dangerous one.** If a wheel accelerates to full speed and stays
> there, the encoder sign disagrees with the motor sign — the PID reads the
> error as growing while it pushes. **Cut power immediately.** Flip that wheel's
> `*_ENC_INVERT`, reflash, retest. Do not "try it on the ground to see."

- [x] **5.9 · Resolve the encoder pin conflict.** `ARCHITECTURE.md` says right
      encoder = GPIO 32/33; `config.h` says 23/22. `config.h` is what is
      flashed, so if 5.4 gave changing counts, `config.h` wins and the doc is
      stale. If the right encoder reads zero while the left works, reflash with
      32/33 and retest.

  Winner: **`config.h` (23/22)** / ~~`ARCHITECTURE.md` (32/33)~~ — the right
  encoder returns changing counts with 23/22 flashed, so the doc was stale.

- [x] Both files made to agree — `ARCHITECTURE.md` corrected,
      `esp-motor-firmware` `52cf077`
- [x] `config.h` committed — `52cf077`. **Not pushed:** this board has no git
      credentials (see `STATE.md`). Hard constraint 4 is still unmet.

---

## Record these

Into `records/calibration.md`, with today's date:

- [x] ESP32 serial / `KERNELS` path — no unique serial, `1-2.2.1`
- [x] Lidar serial / `KERNELS` path — no unique serial, `1-2.2.4`
- [x] Whether the VID:PID collide — **yes**, both `10c4:ea60`, both serial `0001`
- [x] Final `LEFT_ENC_INVERT` / `RIGHT_ENC_INVERT` — **false / false**
- [x] Which encoder pin set is correct — **23/22**
- [ ] GPIO12 boot reliability result (5 power cycles)

---

## GATE — do not start Day 2 until all of these hold

- [x] `ls -l /dev/esp32 /dev/ydlidar` shows both, correctly, after a replug —
      and after a replug that *reversed the enumeration order*
- [x] `e` returns counts that **change** when a wheel is driven, and they change
      in the same direction the motor is driven
- [x] `m 20 20` spins both wheels **forward**, **steadily** (~600 ticks/s each),
      and **stops on its own** after 2.0 seconds
- [ ] The board boots reliably across 5 power cycles ← **the only one left**
- [ ] Everything above is committed and pushed — committed (`cap_ws` `d056229`,
      `esp-motor-firmware` `52cf077`); **pushed: no**, no credentials on this
      board

**Then update `STATE.md`:** day, gate ticked, devices, next action.
