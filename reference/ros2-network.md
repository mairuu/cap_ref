# Multi-machine ROS 2 over the phone hotspot — set up 9 Sep 2026

Verified working end to end, both directions, on 9 Sep. This file is so it is
never re-derived. **Everything here is reproduced by `make net`** in `cap_ws`;
do not hand-edit `~/.bashrc` instead.

---

## The two machines

| | Jetson (the robot) | Laptop (the viewer) |
|---|---|---|
| host | `ubuntu` | `ju-hp-probook-laptop` |
| user | `mic-711` | `ju` |
| address | **172.20.10.2** | **172.20.10.5** |
| interface | `enP8p1s0` | `wlp0s20f3` |
| arch / OS | aarch64 · Ubuntu 22.04.5 | x86_64 · Ubuntu 22.04.5 |
| ROS | Humble + `cap_ws` | Humble, `/opt/ros/humble` only |
| runs | `make real` · `make slam` · `make nav` | `rviz2` · teleop |

`172.20.10.1` is the phone acting as gateway. The subnet is `172.20.10.0/28`,
so the whole usable range is `.1`–`.14` — that is an iPhone hotspot's fixed
allocation, not a coincidence.

> ⚠ **`172.20.10.2` is the Jetson itself.** It was handed to me as the *remote*
> address at the start of this work. There is no `ju` account on the Jetson;
> `ju` lives on `.5`. Easy to invert, because both addresses are `172.20.10.x`
> and neither machine's hostname says which robot it is.

> ⚠ **These are DHCP addresses on a phone hotspot and they will change.** The
> peer list in the DDS profile is literal — it does not follow a rename or a
> re-lease. After any reconnection, check `ip -4 addr` on both and re-run
> `make net PEERS=<jetson>,<laptop>` on **both** machines if either moved.

SSH is key-based, Jetson → laptop, installed 9 Sep:
`ssh ju@172.20.10.5` needs no password. Key `~/.ssh/id_ed25519` on the Jetson,
`SHA256:Dou9H0otuPfAe61+CBpsLRSeQsY/P9G5+hjrMEG7MF8`.

---

## What is set, and why each one is load-bearing

`make net` writes a marked block into `~/.bashrc` on the machine it runs on:

```bash
export ROS_DOMAIN_ID=42
export ROS_LOCALHOST_ONLY=0
export FASTRTPS_DEFAULT_PROFILES_FILE=$HOME/.ros2/fastdds_hotspot.xml
```

**`ROS_DOMAIN_ID=42`, deliberately not 0.** Every other ROS 2 machine on a
shared hotspot also defaults to 0, and the collision is silent in the worst
way: a stranger's nodes turn up in `ros2 topic list` and their `/tf` competes
with ours, which presents as a *broken TF tree*, not as a second robot. Nothing
in the demo needs domain 0.

**`ROS_LOCALHOST_ONLY=0`.** Humble still honours it and it is the difference
between traffic leaving the machine and not. (Removed in Iron+; irrelevant to
us — constraint 1.)

**The Fast DDS profile is the part that actually matters.** A phone hotspot is
an access point, and it forwards unicast between clients while **dropping
client-to-client multicast**. Fast DDS discovers over multicast `239.255.0.1`
by default. So without the profile, two machines that ping each other in 0.08 ms
see **zero** of each other's topics, and every obvious explanation — firewall,
domain, `ROS_LOCALHOST_ONLY` — is wrong. The profile adds each machine's
address as a **unicast initial peer**, so discovery no longer depends on
multicast crossing the AP.

`~/.ros2/fastdds_hotspot.xml`, identical on both machines:

```xml
<initialPeersList>
  <locator><udpv4><address>239.255.0.1</address></udpv4></locator>
  <locator><udpv4><address>172.20.10.2</address></udpv4></locator>
  <locator><udpv4><address>172.20.10.5</address></udpv4></locator>
</initialPeersList>
```

> **The multicast locator is first on purpose, and must stay.** It is what
> nodes on the *same* machine use to find each other. Defining an
> `initialPeersList` replaces the default locator set, so dropping it would
> push same-host discovery onto unicast initial peers — which probe only
> participant ids **0..4** by default. The robot stack is ~15 participants
> (`controller_manager`, both controllers, `robot_state_publisher`, the lidar,
> `slam_toolbox`, and ~10 more once Nav2 is up), so everything past the fifth
> would quietly stop being discoverable **by its own machine**. Cross-machine
> is safe from this because the laptop only ever runs two or three.

**What is deliberately NOT set: `RMW_IMPLEMENTATION`.** The stack that works
today runs on Humble's default `rmw_fastrtps_cpp`. Cyclone is often recommended
for Nav2, but swapping the RMW four days from the demo buys nothing this
profile does not already give and costs a fresh set of failure modes.
Constraint 3.

---

## Measured, 9 Sep

`check_ros2_link.py`, Jetson publishing → laptop subscribing, 15.1 s:

| Stream | Sent | Received | Rate | Loss |
|---|---|---|---|---|
| `std_msgs/String` | 10 Hz | 152 msgs | **10.07 Hz** | none |
| `nav_msgs/OccupancyGrid` 162×249, 40 kB | 2 Hz | 30 msgs | **1.99 Hz** | none |

Also confirmed: `demo_nodes_cpp` talker/listener **both directions**, and
`ros2 node list` on each machine showing the other's nodes.

**The two streams are separate on purpose.** A String that never arrives is a
discovery failure. A String that arrives while the grid does not is **UDP
fragmentation** — anything over ~64 kB is split, and fragments are dropped
silently when the socket buffers are smaller than the burst. That is the
classic "RViz shows the laser but the map never appears", and a plain
talker/listener test passes straight through it. **It did not happen here** —
default buffers carried 40 kB clean — so no `sysctl` tuning is installed. If
Nav2's costmaps (larger than `/map`) do stall on Day 4, the fix is in the
script's own failure message.

---

## Firewall

The **laptop runs `ufw`, active.** Traffic still crosses, because the laptop's
own outbound announcements open conntrack state that the Jetson's replies ride
back through. That works but is not something to rely on — if discovery ever
goes one-way, this is the first suspect, and the fix is one command **on the
laptop**:

```bash
sudo ufw allow from 172.20.10.0/28 comment "ROS2 hotspot subnet"
```

The Jetson has no firewall at all (`ufw` inactive, all iptables policies
`ACCEPT`), so nothing is needed on this side.

---

## Running RViz on the laptop

The URDF is **primitive geometry with no meshes** (checked 9 Sep), so
`RobotModel` renders on the laptop straight from `/robot_description` over the
wire. **Nothing needs building on the laptop** — it has no `cap_ws` and does
not need one. Only the layout file was copied:

```bash
# on the laptop
rviz2 -d ~/cap_view/nav.rviz
```

`~/cap_view/` on the laptop holds `nav.rviz` and `check_ros2_link.py`, copied
from `cap_ws/src/my_bot/`. **They are copies, not links** — re-scp `nav.rviz`
after changing it in the repo, or the laptop keeps showing the old layout.

Everything in that layout is a standard message type (`LaserScan`,
`OccupancyGrid`, `Path`, `TF`, `MarkerArray`), so the laptop needs no custom
interfaces. `yolo_msgs/DetectionArray` is **not** standard — a laptop-side
`ros2 topic echo /yolo/detections` will fail on the type, but the Day 6
semantic markers are `visualization_msgs/MarkerArray` and will display fine.

---

## `ROS_DOMAIN_ID` and the semantic bridge

`semantic_bridge/config.py` reads `ROS_DOMAIN_ID` from the environment with a
default of `0`. It inherits **42** automatically from the `.bashrc` block, so
long as the bridge is started from a normal login shell. `day-6-fusion.md`
asks for bridge and robot to match — they do, by inheritance, and the thing to
check is that the bridge was not started from a stripped environment (a
systemd unit, a container, `env -i`).
