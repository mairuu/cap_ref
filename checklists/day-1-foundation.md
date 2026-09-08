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
- [ ] `capstone-ws` — created empty, pushed.
- [x] `esp-motor-firmware` — exists at `b0b762b`.
- [ ] `STATE.md` "Repos pushed" table updated.

## 4 · udev rules — re-derive from the hardware

The **values** died with the board, but `scripts/setup_udev.sh` — which walks
this whole section interactively — came back in the NVMe dump. Copy it into
`capstone-ws/src/my_bot/scripts/` and run `make udev` rather than doing the
steps below by hand; they are kept as the explanation of what it is doing.

> The recovered `udev/99-my-bot-serial.rules` matched both devices by **USB
> port path** (`KERNELS=="1-2.1"` esp32, `"1-2.2.4"` lidar) because neither
> adapter has a serial. The Advantech carrier has different USB topology, so
> **those paths will not transfer — re-derive them, do not copy the file.**

Full rationale: `RECOVERY.md` §5.1, `reference/nvme-recovery-audit.md`.

> **Assume the ESP32 and the lidar collide on `10c4:ea60`.** Both are likely
> CP210x. A vendor/product rule would match whichever enumerated first.

**One device at a time:**

- [ ] Unplug both. Plug in **only the ESP32**:

```bash
ls /dev/ttyUSB*
udevadm info -a -n /dev/ttyUSB0 | grep -E 'idVendor|idProduct|serial' | head -6
```

  Record → `idVendor` ________ `idProduct` ________ `serial` ________________

- [ ] Unplug. Plug in **only the lidar**. Repeat.

  Record → `idVendor` ________ `idProduct` ________ `serial` ________________

- [ ] **Do they collide?**  yes / no  → if yes, serials are mandatory

- [ ] Write `capstone-ws/src/my_bot/udev/99-capstone.rules`:

```udev
SUBSYSTEM=="tty", ATTRS{idVendor}=="10c4", ATTRS{idProduct}=="ea60", ATTRS{serial}=="<ESP32_SERIAL>", SYMLINK+="esp32", MODE="0666"
SUBSYSTEM=="tty", ATTRS{idVendor}=="10c4", ATTRS{idProduct}=="ea60", ATTRS{serial}=="<LIDAR_SERIAL>", SYMLINK+="ydlidar", MODE="0666"
```

  **If the serials are identical or absent** (common on CP2102 clones), fall back
  to physical USB port paths — and **label the sockets physically**, because the
  rule becomes a promise about cabling:

```bash
udevadm info -a -n /dev/ttyUSB0 | grep -m1 KERNELS   # e.g. KERNELS=="1-2.3"
```

```udev
SUBSYSTEM=="tty", KERNELS=="1-2.3", SYMLINK+="esp32", MODE="0666"
SUBSYSTEM=="tty", KERNELS=="1-2.4", SYMLINK+="ydlidar", MODE="0666"
```

- [ ] Install and verify:

```bash
sudo cp .../99-capstone.rules /etc/udev/rules.d/
sudo udevadm control --reload-rules && sudo udevadm trigger
ls -l /dev/esp32 /dev/ydlidar
```

- [ ] Both plugged in together, both symlinks correct
- [ ] Unplug/replug both in the other order — still correct
- [ ] Rules file committed and pushed
- [ ] `STATE.md` "Devices" table filled in

## 5 · Firmware validation — the day's real work

`ROADMAP.md` step 5 was only ever checked through `e` and `r`. **The firmware
has never turned a motor.** Full context: `reference/firmware-protocol.md`.

- [ ] **Robot on blocks.** Wheels free. Confirm before continuing.
- [ ] Nothing holds the port:

```bash
sudo fuser -v /dev/esp32     # must be empty
```

- [ ] Write `serial_probe.py` and `encoder_report.py` now
      (`reference/scripts-to-rebuild.md`) — you will use them all week.

Then, **in order, do not skip ahead**:

| # | Send | Expect | Pass | If wrong |
|---|---|---|---|---|
| 5.1 | *power on* | `# boot reset=1 encoders=ok` | [ ] | `encoders=FAIL` → pin problem, go to 5.9 |
| 5.2 | `r` | `OK` | [ ] | — |
| 5.3 | spin **left** wheel forward by hand, then `e` | left count **increases** | [ ] | flip `LEFT_ENC_INVERT` in `config.h`, reflash |
| 5.4 | spin **right** wheel forward by hand, then `e` | right count **increases** | [ ] | flip `RIGHT_ENC_INVERT`, reflash |
| 5.5 | `o 50 50` | `OK`, both wheels turn **forward** | [ ] | swap that motor's FORWARD/BACKWARD pins |
| 5.6 | *wait 2 s* | motors stop by themselves | [ ] | auto-stop broken — **do not proceed** |
| 5.7 | `m 20 20` | `OK`, wheels settle at a steady speed | [ ] | **see below** |
| 5.8 | power-cycle 5× | boots every time | [ ] | GPIO12 strapping issue |

> ⚠ **5.7 is the dangerous one.** If a wheel accelerates to full speed and stays
> there, the encoder sign disagrees with the motor sign — the PID reads the
> error as growing while it pushes. **Cut power immediately.** Flip that wheel's
> `*_ENC_INVERT`, reflash, retest. Do not "try it on the ground to see."

- [ ] **5.9 · Resolve the encoder pin conflict.** `ARCHITECTURE.md` says right
      encoder = GPIO 32/33; `config.h` says 23/22. `config.h` is what is
      flashed, so if 5.4 gave changing counts, `config.h` wins and the doc is
      stale. If the right encoder reads zero while the left works, reflash with
      32/33 and retest.

  Winner: `config.h` (23/22) / `ARCHITECTURE.md` (32/33) — circle one

- [ ] Both files made to agree
- [ ] `config.h` committed and **pushed the same day**

---

## Record these

Into `records/calibration.md`, with today's date:

- [ ] ESP32 serial / `KERNELS` path
- [ ] Lidar serial / `KERNELS` path
- [ ] Whether the VID:PID collide
- [ ] Final `LEFT_ENC_INVERT` / `RIGHT_ENC_INVERT`
- [ ] Which encoder pin set is correct
- [ ] GPIO12 boot reliability result (5 power cycles)

---

## GATE — do not start Day 2 until all of these hold

- [ ] `ls -l /dev/esp32 /dev/ydlidar` shows both, correctly, after a replug
- [ ] `e` returns counts that **change** when a wheel is spun by hand
- [ ] `m 20 20` spins both wheels **forward**, **steadily**, and **stops on its
      own** after ~2 seconds
- [ ] The board boots reliably across 5 power cycles
- [ ] Everything above is committed and pushed

**Then update `STATE.md`:** day, gate ticked, devices, next action.
