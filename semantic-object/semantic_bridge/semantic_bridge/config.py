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
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]


settings = Settings()
