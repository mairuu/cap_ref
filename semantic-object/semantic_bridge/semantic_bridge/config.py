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


settings = Settings()
