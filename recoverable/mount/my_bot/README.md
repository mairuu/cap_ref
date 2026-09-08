# my_bot

Differential-drive robot: an ESP32 base controller over serial, a YDLidar X2,
`ros2_control`, and slam_toolbox.

## Serial port mapping (do this first)

The ESP32 and the lidar are both USB serial adapters. The kernel hands out
`/dev/ttyUSB0`, `/dev/ttyUSB1`, ... in enumeration order, so which device gets
which number depends on power-up timing and flips across reboots. Pointing the
driver at the wrong one gives you a lidar that never spins or a base controller
that times out on configure.

The fix is udev symlinks that follow the hardware:

| Symlink        | Device                | Configured in                  |
| -------------- | --------------------- | ------------------------------ |
| `/dev/esp32`   | ESP32 base controller | `description/ros2_control.xacro` |
| `/dev/ydlidar` | YDLidar X2            | `launch/real_robot.launch.py`, `config/ydlidar.yaml` |

Run once per machine, with **both devices plugged in**:

```bash
make udev          # from the workspace root (cap_ws)
```

It lists every serial device with its VID:PID, serial number and USB port, asks
which is which, then generates `/etc/udev/rules.d/99-my-bot-serial.rules` and
keeps a copy at `udev/99-my-bot-serial.rules`.

Matching key, chosen automatically:

- **`ATTRS{serial}`** when the adapters have distinct serial numbers. Preferred
  — the device can be moved to any USB port.
- **`KERNELS`** (USB port path) when they are indistinguishable, e.g. two
  CP2102s from the same batch or a CH340, which has no serial at all. The
  device must then stay in the **same physical port**; re-run `make udev` if
  you move it.

Check the current state any time:

```bash
make ports
```

Re-run `make udev` after swapping an adapter or moving one between ports.

### When a symlink does not appear

`udevadm trigger` does not re-fire for every adapter. Unplug and replug the
device. If it still does not show up:

```bash
udevadm test $(udevadm info -q path -n /dev/ttyUSB0)   # see which rules matched
udevadm info -a -n /dev/ttyUSB0 | head -40             # attributes udev can match on
```

Access is via `GROUP="dialout", MODE="0660"` — your user must be in `dialout`
(`id -nG | grep dialout`; if missing, `sudo usermod -aG dialout $USER` then log
out and back in).

## Bringup

```bash
make build     # colcon build --symlink-install
make sim       # Gazebo
make real      # real hardware: rsp + controller manager + controllers + lidar
make slam      # online async SLAM, needs `make real` or `make sim` already up
make nav       # Nav2 + twist_mux, needs `make slam` already up
make explore   # frontier exploration, needs `make nav` already up
make save-map  # write the current map to disk
make yolo      # YOLO detection on the USB webcam, standalone
make teleop    # keyboard teleop, own terminal
```

`make slam SIM_TIME=true` runs the mapper against the simulator.

To force a raw port for one run, bypassing the symlink:

```bash
make real LIDAR_PORT=/dev/ttyUSB0
```

## Autonomous navigation

`slam_toolbox` does **not** drive the robot. It publishes `/map` and the
`map -> odom` transform and nothing else; there is no planner and no velocity
output in it. The piece that turns a goal into wheel commands is **Nav2**, and
the piece that chooses goals without a human is **explore_lite**. They stack:

```
make real     base + lidar
  make slam     /map + map->odom          <- knows where it is
    make nav      Nav2 + twist_mux        <- can drive to a goal
      make explore  frontier goals        <- chooses its own goals
```

Each layer needs the one above it already running, in its own terminal. Start
them in that order and stop them in reverse.

### Driving to a clicked goal

```bash
make real          # terminal 1
make slam          # terminal 2
make nav           # terminal 3
rviz2              # terminal 4
```

In RViz set **Fixed Frame** to `map`, add a **Map** display on `/map` and a
**Path** on `/plan`, then use the **2D Goal Pose** button. The robot plans and
drives there on its own.

**Get this working before trying `make explore`.** Exploration only sends
`NavigateToPose` goals; if a clicked goal does not work, an automatic one will
not either, and the failure is much harder to read.

### Exploring unattended

```bash
make explore       # terminal 5
```

It watches `/map`, finds frontiers (the boundary between mapped free space and
unknown space), picks one, and hands it to Nav2. Add a **MarkerArray** display
on `/explore/frontiers` in RViz to see which frontier it chose. With
`return_to_init: true` (the default in `config/explore_params.yaml`) the robot
drives back to its starting pose when no frontiers remain, which is the "done"
signal. Save the result:

```bash
make save-map MAP=~/maps/lab
```

### In simulation first

Test here before letting it loose on hardware. `use_sim_time` must match across
**all** of slam, nav and explore, or TF lookups fail silently:

```bash
make sim                      # terminal 1 (loads worlds/room.world)
make slam    SIM_TIME=true    # terminal 2
make nav     SIM_TIME=true    # terminal 3
make explore SIM_TIME=true    # terminal 4
```

`make sim` now defaults to `worlds/room.world`, a closed 8x6 m room with two
offset doorways and two pillars. `empty.world` is an infinite ground plane, so
the map never gains a boundary, frontiers never run out and exploration never
terminates; `make sim WORLD=empty` still gets you the bare plane.

### Velocity limits and the e-stop

Nothing between Nav2 and the motors clamps speed: `diff_cont` sets no limits and
`hardware/diffdrive_serial.cpp` passes commands straight to the ESP32. The
limits in `config/nav2_params.yaml` (`max_vel_x` 0.22 m/s, `max_vel_theta`
1.0 rad/s) are therefore the **only** speed limit the robot has, and they are
deliberately timid starting values rather than measured ones. Watch it drive
before raising them.

`twist_mux` arbitrates between Nav2 and you, with teleop at the higher priority:

```
/cmd_vel         (Nav2, prio 10)  --+
                                    +--> twist_mux --> /diff_cont/cmd_vel_unstamped
/cmd_vel_teleop  (you,  prio 100) --+
```

So this overrides an autonomous run at any time, and is the closest thing to an
emergency stop:

```bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard \
  --ros-args -r /cmd_vel:=/cmd_vel_teleop
```

Note the topic: plain `make teleop` publishes to `/diff_cont/cmd_vel_unstamped`
directly, which bypasses the mux and fights Nav2 instead of overriding it. Use
the remap above whenever Nav2 is running.

### Troubleshooting

| Symptom | Cause |
| ------- | ----- |
| Path is planned, robot does not move | `twist_mux` not running, so nothing bridges `/cmd_vel` to `/diff_cont/cmd_vel_unstamped`. Check `ros2 topic echo /diff_cont/cmd_vel_unstamped`. |
| Every goal rejected as unplannable | `allow_unknown` got set back to `false`. Frontier goals sit on the edge of unknown space and need it `true`. |
| Robot's pose jumps around | Something other than slam_toolbox is publishing `map -> odom` — usually an accidentally launched `amcl` or `map_server`. |
| Nothing happens in sim, no error | `SIM_TIME` not passed to every layer. |
| Robot refuses doorways it fits through | `footprint` replaced with `robot_radius`. A circle around this robot needs r=0.265 because `base_link` sits on the axle, not at the centre. |

## YOLO object detection

```bash
make yolo
```

Runs standalone — it needs no other bringup, just the Logitech C615 on
`/dev/video0`. `launch/yolo.launch.py` starts a camera node plus the three
[yolo_ros](https://github.com/mgonzs13/yolo_ros) nodes and publishes:

| Topic               | Type                        |                                   |
| ------------------- | --------------------------- | --------------------------------- |
| `/image`            | `sensor_msgs/Image`         | camera frames, 640x480 @ 15 Hz    |
| `/yolo/detections`  | `yolo_msgs/DetectionArray`  | raw detections                     |
| `/yolo/tracking`    | `yolo_msgs/DetectionArray`  | same, with persistent track ids   |
| `/yolo/dbg_image`   | `sensor_msgs/Image`         | annotated frames                   |

Measured end to end at 15 Hz on every topic, i.e. camera-limited — the
`yolo26n` engine infers a 640x640 frame in ~18 ms (`yolo26s`: ~27 ms), so there
is headroom in `camera_fps` if you want it.

Useful arguments:

```bash
make yolo MODEL=/home/jetson/yolo/yolo26s.engine   # bigger model
ros2 launch my_bot yolo.launch.py use_camera:=False image_topic:=/my/camera
ros2 launch my_bot yolo.launch.py threshold:=0.25 use_debug:=False
```

### The venv, and why not `yolo_bringup`

Inference runs out of a hand-built venv at
`dev_ws/install/yolo_ros/share/yolo_ros/.venv`, holding the JetPack
`torch`/`torchvision` aarch64 wheels and `tensorrt`. **Do not run `uv sync`
against it** — the checked-in `uv.lock` pins generic PyPI `torch==2.13.0` and
does not list `tensorrt` at all, so a sync downgrades the JetPack wheels and
prunes TensorRT, leaving a venv with no CUDA and no `.engine` support.

Upstream's `yolo_bringup/launch/yolo.launch.py` runs exactly that `uv sync` on
every launch, which is why this workspace has its own launch file instead. All
it borrows is the useful half: the venv's `site-packages` on the nodes'
`PYTHONPATH`. Nothing needs `activate` — the venv's interpreter is the same
`/usr/bin/python3.10` the ROS nodes already run under.

`yolo_ros` also needs a one-line patch before `.engine` models work at all; see
`cap_ws/patches/`. Without it `make yolo` hangs at `Activating...`.

### Troubleshooting

`cam2image` aborts with `Could not open video stream` when something else still
holds the camera — usually a node left over from a previous run. The launch
shuts everything down when that happens, so check with:

```bash
fuser -v /dev/video0
```
