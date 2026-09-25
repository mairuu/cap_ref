from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(populate_by_name=True)

    mock: bool = Field(default=False, validation_alias="SEMANTIC_BRIDGE_MOCK")
    ros_domain_id: int = Field(default=0, validation_alias="ROS_DOMAIN_ID")
    state_ws_interval_ms: int = 200
    camera_fps: int = 10
    ros_retry_interval_s: int = 5
    scan_downsample_rays: int = 180
    # The robot's camera is cam2image on /image; semantic.launch.py runs an
    # image_transport republish that produces /image/compressed. The pre-dump
    # default (/camera/image_raw/compressed) belonged to usb_cam, which this
    # robot does not run. 14 Sep 2026.
    camera_topic: str = Field(default="/image/compressed", validation_alias="CAMERA_TOPIC")
    # The browser is on the laptop and the bridge on the Jetson, so the origin
    # is http://<jetson-ip>:3000, which no fixed list anticipates. No
    # credentials are used, so "*" costs nothing. 14 Sep 2026.
    cors_origins: list[str] = ["*"]

    # ---- stack console -------------------------------------------------
    #
    # WHY A PATH AND NOT ament_index_python. `make bridge` sources
    # /opt/ros/humble/setup.bash and NOT install/setup.bash, so
    # get_package_share_directory("my_bot") raises PackageNotFoundError in the
    # environment this process actually runs in -- verified 22 Sep. An ament
    # import would also be the only ROS-dependent import outside ros_node.py,
    # which defers every rclpy import on purpose so the app stays importable
    # with no ROS at all (SEMANTIC_BRIDGE_MOCK=1 and the pytest suite both
    # depend on that).
    cap_ws: Path = Field(default=Path.home() / "cap_ws", validation_alias="CAP_WS")
    ros_setup: Path = Field(default=Path("/opt/ros/humble/setup.bash"),
                            validation_alias="ROS_SETUP")
    tmux_session: str = Field(default="cap", validation_alias="CAP_TMUX_SESSION")

    # Off means the console routes still exist but refuse to act. A reviewer
    # or a laptop running the UI against a bag replay has no business starting
    # motors.
    stack_enabled: bool = Field(default=True, validation_alias="CAP_STACK_ENABLED")
    teleop_enabled: bool = Field(default=True, validation_alias="CAP_TELEOP_ENABLED")

    # How often the console re-reads tmux (cheap) and re-runs the readiness
    # gate (~4 s of ROS spinning, so much less often).
    stack_poll_s: float = 1.0
    stack_readiness_s: float = 10.0
    stack_log_lines: int = 400

    @property
    def ui_dist(self) -> Path:
        return Path.home() / "cap_ref" / "semantic-object" / "semantic_map_ui" / "dist"

    @property
    def stack_wait(self) -> Path:
        """Installed first, source tree as the fallback.

        --symlink-install makes the installed copy a symlink to the source, so
        in practice these are the same file; the fallback matters only before
        the first colcon build.
        """
        installed = self.cap_ws / "install/my_bot/lib/my_bot/stack_wait.py"
        if installed.exists():
            return installed
        return self.cap_ws / "src/my_bot/scripts/stack_wait.py"


settings = Settings()
