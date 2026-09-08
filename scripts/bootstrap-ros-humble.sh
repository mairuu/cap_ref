#!/usr/bin/env bash
# Day 1 step 2 — ROS 2 Humble on the rebuilt Jetson (JetPack 6.1 / Ubuntu 22.04).
#
# Idempotent: safe to re-run after a partial failure. Run with sudo:
#     sudo ./scripts/bootstrap-ros-humble.sh
#
# This REPLACES the apt block in checklists/day-1-foundation.md §2, which was
# written before the NVMe dump. Corrections, per reference/nvme-recovery-audit.md:
#
#   * ros-humble-usb-cam is NOT needed. The camera that actually ran was
#     `cam2image` from ros-humble-image-tools, publishing /image at RELIABLE QoS.
#     Installing usb_cam invites rebuilding the wrong camera pipeline on Day 5.
#   * Nav2 is installed in its own step, non-fatally. .bash_history lines
#     1391-1431 show `apt install ros-humble-navigation2` failing repeatedly on
#     the old board, a ros2-snapshot repo being tried and removed, and Nav2
#     finally going in from local debs in ~/nav2_debs/ (those debs are lost).
#     If it fails here we want to know on Day 1, not Day 4.
#   * cmake/build-essential are included: ydlidar_ros2_driver, explore_lite and
#     yolo_ros are all source builds, not apt packages.
#
set -uo pipefail

if [ "$(id -u)" -ne 0 ]; then
    echo "error: run with sudo — sudo $0" >&2
    exit 1
fi
REAL_USER="${SUDO_USER:-$(logname 2>/dev/null || echo root)}"

say() { printf '\n\033[1m== %s\033[0m\n' "$*"; }
FAILED=()

# ---------------------------------------------------------------- 1. apt repo
say "1/5  ROS 2 apt repository"
apt-get update -qq
apt-get install -y software-properties-common curl gnupg ca-certificates
add-apt-repository -y universe

if [ ! -s /usr/share/keyrings/ros-archive-keyring.gpg ]; then
    curl -fsSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key \
        -o /usr/share/keyrings/ros-archive-keyring.gpg
fi
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] http://packages.ros.org/ros2/ubuntu jammy main" \
    > /etc/apt/sources.list.d/ros2.list
apt-get update

# ------------------------------------------------------------ 2. core distro
say "2/5  ros-humble-desktop + ros-dev-tools  (this is the long one)"
apt-get install -y ros-humble-desktop ros-dev-tools || FAILED+=("ros-humble-desktop")

# --------------------------------------------------------- 3. the week's set
say "3/5  Week's package set"
apt-get install -y \
    ros-humble-ros2-control ros-humble-ros2-controllers \
    ros-humble-controller-manager \
    ros-humble-slam-toolbox \
    ros-humble-twist-mux \
    ros-humble-image-tools \
    ros-humble-camera-calibration \
    ros-humble-compressed-image-transport \
    ros-humble-image-transport-plugins \
    ros-humble-vision-msgs \
    ros-humble-teleop-twist-keyboard \
    ros-humble-xacro \
    ros-humble-joint-state-publisher-gui \
    ros-humble-tf2-tools ros-humble-rqt-tf-tree ros-humble-rqt-image-view \
    || FAILED+=("week package set")

# Source-build toolchain for ydlidar_ros2_driver / explore_lite / yolo_ros.
apt-get install -y build-essential cmake git pkg-config python3-venv \
    || FAILED+=("build toolchain")

# --------------------------------------------------------------- 4. Nav2
say "4/5  Nav2  (known to have fought back on the old board — see header)"
if apt-get install -y ros-humble-navigation2 ros-humble-nav2-bringup; then
    echo "Nav2 installed cleanly from packages.ros.org."
else
    FAILED+=("navigation2")
    cat <<'MSG'

  !! Nav2 did not install. This is the SAME failure the old board hit.
     Do NOT paper over it with a ros2-snapshot repo — that was tried and
     reverted on the old board (.bash_history ~line 1405/1417).
     Capture the exact apt error and log it in records/issues.md before
     retrying. Day 4 depends on this.

MSG
fi

# ------------------------------------------------------------- 5. rosdep
say "5/5  rosdep"
rosdep init 2>/dev/null || echo "rosdep already initialised — fine."
sudo -u "$REAL_USER" rosdep update || FAILED+=("rosdep update")

# ------------------------------------------------------------------ report
say "Result"
if [ ${#FAILED[@]} -eq 0 ]; then
    echo "All steps succeeded."
else
    printf 'FAILED: %s\n' "${FAILED[@]}"
fi
echo
echo "Verify by hand:"
echo "  source /opt/ros/humble/setup.bash && ros2 topic list"
echo
echo "NOT installed here, deliberately — all source builds, done later:"
echo "  ydlidar_ros2_driver + YDLidar-SDK   (Day 1/2, needs the lidar)"
echo "  explore_lite (m-explore-ros2)       (Day 3)"
echo "  yolo_ros                            (Day 5, see decision D-11)"
echo "  ros_gz_sim / gz_ros2_control        (only if sim is wanted; not on the demo path)"
