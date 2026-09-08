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

- [ ] Repository added:

```bash
sudo apt update && sudo apt install -y software-properties-common curl
sudo add-apt-repository universe
sudo curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key \
  -o /usr/share/keyrings/ros-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] \
http://packages.ros.org/ros2/ubuntu $(. /etc/os-release && echo $UBUNTU_CODENAME) main" \
  | sudo tee /etc/apt/sources.list.d/ros2.list
sudo apt update && sudo apt install -y ros-humble-desktop ros-dev-tools
```

- [ ] Week's package set installed:

```bash
sudo apt install -y \
  ros-humble-ros2-control ros-humble-ros2-controllers \
  ros-humble-slam-toolbox ros-humble-navigation2 ros-humble-nav2-bringup \
  ros-humble-usb-cam ros-humble-camera-calibration \
  ros-humble-compressed-image-transport ros-humble-image-transport-plugins \
  ros-humble-vision-msgs ros-humble-teleop-twist-keyboard \
  ros-humble-twist-mux ros-humble-xacro ros-humble-joint-state-publisher-gui \
  ros-humble-tf2-tools ros-humble-rqt-tf-tree
```

- [ ] `ros2 topic list` runs after `source /opt/ros/humble/setup.bash`

## 3 · Repos — before any code exists

Ten minutes, and it is the whole reason this workspace exists.

- [ ] `capstone-docs` — this workspace. Remote created, initial commit pushed.
- [ ] `semantic-bridge` — push `semantic-object/` **now**; it is currently
      one drive failure from gone.
- [ ] `capstone-ws` — created empty, pushed.
- [x] `esp-motor-firmware` — exists at `b0b762b`.
- [ ] `STATE.md` "Repos pushed" table updated.

## 4 · udev rules — re-derive from the hardware

The rules died with the board and the VID/PID/serial values are not recoverable
from anything we have. Full rationale: `RECOVERY.md` §5.1.

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
SUBSYSTEM=="tty", ATTRS{idVendor}=="10c4", ATTRS{idProduct}=="ea60", ATTRS{serial}=="<LIDAR_SERIAL>", SYMLINK+="lidar", MODE="0666"
```

  **If the serials are identical or absent** (common on CP2102 clones), fall back
  to physical USB port paths — and **label the sockets physically**, because the
  rule becomes a promise about cabling:

```bash
udevadm info -a -n /dev/ttyUSB0 | grep -m1 KERNELS   # e.g. KERNELS=="1-2.3"
```

```udev
SUBSYSTEM=="tty", KERNELS=="1-2.3", SYMLINK+="esp32", MODE="0666"
SUBSYSTEM=="tty", KERNELS=="1-2.4", SYMLINK+="lidar", MODE="0666"
```

- [ ] Install and verify:

```bash
sudo cp .../99-capstone.rules /etc/udev/rules.d/
sudo udevadm control --reload-rules && sudo udevadm trigger
ls -l /dev/esp32 /dev/lidar
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

- [ ] `ls -l /dev/esp32 /dev/lidar` shows both, correctly, after a replug
- [ ] `e` returns counts that **change** when a wheel is spun by hand
- [ ] `m 20 20` spins both wheels **forward**, **steadily**, and **stops on its
      own** after ~2 seconds
- [ ] The board boots reliably across 5 power cycles
- [ ] Everything above is committed and pushed

**Then update `STATE.md`:** day, gate ticked, devices, next action.
