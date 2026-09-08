# YOLO object detection on the Jetson's USB webcam.
#
# This deliberately does NOT include yolo_bringup's yolo.launch.py. That launch
# shells out to `uv sync` on every start, which resolves yolo_ros/uv.lock and
# would rip the hand-installed Jetson wheels out of the venv:
#
#   torch       2.11.0 (JetPack aarch64+CUDA wheel)  ->  2.13.0 (generic PyPI)
#   torchvision 0.26.0 (JetPack aarch64 wheel)       ->  0.28.0 (generic PyPI)
#
# and it prunes tensorrt/onnx, which are in the venv but not in the lock. The
# result is a venv with no working CUDA and no TensorRT, so the .engine models
# stop loading. All yolo_bringup actually needs from `uv sync` is the venv's
# site-packages on PYTHONPATH, so we do that part ourselves and skip the sync.
#
# The venv is user-managed -- see VENV below. Don't run `uv sync` against it.

import glob
import os

from launch import LaunchDescription, LaunchContext
from launch.actions import DeclareLaunchArgument, OpaqueFunction, Shutdown
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue

# Hand-built venv holding the JetPack torch/torchvision/tensorrt wheels plus
# ultralytics. Its interpreter is 3.10.12 off /usr/bin, the same one the ROS
# nodes run under, so putting its site-packages on PYTHONPATH is enough -- the
# nodes do not need to run the venv's own python.
VENV = "/home/jetson/dev_ws/install/yolo_ros/share/yolo_ros/.venv"

# TensorRT engines built by /home/jetson/yolo/compile.py. Both carry a fixed
# 640x640 input shape, so IMGSZ has to match or ultralytics rejects the plan.
# Re-export with compile.py if you want a different size.
DEFAULT_MODEL = "/home/jetson/yolo/yolo26n.engine"
IMGSZ = (640, 640)  # height, width -- inference size, letterboxed from CAM_SIZE

# Native mode of the C615. Independent of IMGSZ.
CAM_SIZE = (480, 640)  # height, width

# cam2image (ros-humble-image-tools, already installed) publishes RELIABLE, so
# the YOLO subscribers must be reliable too or they never match. If you swap in
# a best-effort camera driver, flip this to 2.
RELIABLE = 1


def _venv_pythonpath() -> str:
    """Venv site-packages first, so its torch/ultralytics shadow the system's."""
    site_pkgs = glob.glob(os.path.join(VENV, "lib", "python*", "site-packages"))
    if not site_pkgs:
        raise RuntimeError(
            f"No site-packages under {VENV}. The yolo_ros venv is missing or "
            f"was built for a different python; recreate it before launching."
        )
    return ":".join(site_pkgs + [os.environ.get("PYTHONPATH", "")]).strip(":")


def launch_setup(context: LaunchContext, use_tracking):

    use_tracking = eval(context.perform_substitution(use_tracking))
    env = {"PYTHONPATH": _venv_pythonpath()}

    namespace = LaunchConfiguration("namespace")
    image_topic = LaunchConfiguration("image_topic")

    # The debug overlay follows the tracker when it is running, so the track
    # ids show up in the annotated image.
    debug_detections = "tracking" if use_tracking else "detections"

    # cam2image logs one INFO line per frame, hence the log-level bump. It
    # aborts if it cannot open the device -- usually because a previous run is
    # still holding /dev/video0 -- so take the whole launch down with it rather
    # than leave the YOLO nodes up and silently receiving nothing.
    camera_node = Node(
        package="image_tools",
        executable="cam2image",
        name="cam2image",
        condition=IfCondition(LaunchConfiguration("use_camera")),
        parameters=[{
            "device_id": ParameterValue(
                LaunchConfiguration("camera_device_id"), value_type=int),
            "frequency": ParameterValue(
                LaunchConfiguration("camera_fps"), value_type=float),
            "width": CAM_SIZE[1],
            "height": CAM_SIZE[0],
            "frame_id": "camera_link",
            "reliability": "reliable",
        }],
        arguments=["--ros-args", "--log-level", "cam2image:=warn"],
        on_exit=Shutdown(reason="camera node exited"),
    )

    # Publishes <namespace>/detections (yolo_msgs/DetectionArray).
    yolo_node = Node(
        package="yolo_ros",
        executable="yolo_node",
        name="yolo_node",
        namespace=namespace,
        additional_env=env,
        parameters=[{
            "model_type": "YOLO",
            "model": LaunchConfiguration("model"),
            "device": LaunchConfiguration("device"),
            # Fusing a TensorRT engine is a no-op at best and throws at worst
            # -- the layers are already fused inside the plan.
            "fuse_model": False,
            "yolo_encoding": "bgr8",
            "enable": True,
            "threshold": LaunchConfiguration("threshold"),
            "iou": 0.7,
            "imgsz_height": IMGSZ[0],
            "imgsz_width": IMGSZ[1],
            "half": False,
            "max_det": 300,
            "image_reliability": RELIABLE,
        }],
        remappings=[("image_raw", image_topic)],
    )

    # Adds track ids on <namespace>/tracking.
    tracking_node = Node(
        package="yolo_ros",
        executable="tracking_node",
        name="tracking_node",
        namespace=namespace,
        condition=IfCondition(str(use_tracking)),
        additional_env=env,
        parameters=[{
            "tracker": "bytetrack.yaml",
            "image_reliability": RELIABLE,
        }],
        remappings=[("image_raw", image_topic)],
    )

    # Annotated frames on <namespace>/dbg_image.
    debug_node = Node(
        package="yolo_ros",
        executable="debug_node",
        name="debug_node",
        namespace=namespace,
        condition=IfCondition(LaunchConfiguration("use_debug")),
        additional_env=env,
        parameters=[{"image_reliability": RELIABLE}],
        remappings=[
            ("image_raw", image_topic),
            ("detections", debug_detections),
        ],
    )

    return [camera_node, yolo_node, tracking_node, debug_node]


def generate_launch_description():

    use_tracking = LaunchConfiguration("use_tracking")

    return LaunchDescription([
        DeclareLaunchArgument(
            "model", default_value=DEFAULT_MODEL,
            description="Path to a .engine or .pt model"),
        DeclareLaunchArgument(
            "device", default_value="cuda:0",
            description="Inference device; cpu to fall back off the GPU"),
        DeclareLaunchArgument(
            "threshold", default_value="0.5",
            description="Minimum confidence to publish a detection"),
        DeclareLaunchArgument(
            "namespace", default_value="yolo",
            description="Namespace for the yolo nodes"),
        DeclareLaunchArgument(
            "image_topic", default_value="/image",
            description="Input image topic (cam2image publishes /image)"),
        DeclareLaunchArgument(
            "use_camera", default_value="True",
            description="Start cam2image; set False if a camera is already up"),
        DeclareLaunchArgument(
            "camera_device_id", default_value="0",
            description="V4L2 index; the C615 enumerates as /dev/video0"),
        DeclareLaunchArgument(
            "camera_fps", default_value="15.0",
            description="Camera publish rate"),
        DeclareLaunchArgument(
            "use_debug", default_value="True",
            description="Publish the annotated debug image"),
        DeclareLaunchArgument(
            "use_tracking", default_value="True",
            description="Run the tracker and publish <namespace>/tracking"),
        OpaqueFunction(function=launch_setup, args=[use_tracking]),
    ])
