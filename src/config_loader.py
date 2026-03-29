"""
Configuration loader for Face Tracking Camera.
Loads YAML configuration with defaults and environment overrides.
"""

import os
import yaml
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class CameraConfig:
    index: int = 1
    width: int = 640
    height: int = 480
    fps: int = 15
    flip_horizontal: bool = True


@dataclass
class SerialConfig:
    port: str = "auto"
    baud_rate: int = 9600
    timeout: float = 2.0


@dataclass
class TrackingConfig:
    tolerance: float = 0.5
    smoothing_alpha: float = 0.4
    min_servo_speed: float = 0.5
    scanning_speed: float = 2.0
    scanning_dir_change_delay: int = 100
    lost_face_timeout: float = 1.0
    center_tolerance: int = 40


@dataclass
class ServoConfig:
    center_angle: int = 90
    min_angle: int = 0
    max_angle: int = 180
    default_min: int = 30
    default_max: int = 150


@dataclass
class LEDConfig:
    pin: int = 13
    enabled: bool = True


@dataclass
class FacesConfig:
    model_path: str = "models/teacher_face.pkl"
    multi_face: bool = False
    names: List[str] = field(default_factory=lambda: ["teacher"])


@dataclass
class DebugConfig:
    show_video: bool = True
    show_guides: bool = True
    show_fps: bool = True
    log_level: str = "INFO"
    log_file: str = "logs/face_tracker.log"
    save_snapshot: bool = False


@dataclass
class Config:
    camera: CameraConfig
    serial: SerialConfig
    tracking: TrackingConfig
    servo: ServoConfig
    led: LEDConfig
    faces: FacesConfig
    debug: DebugConfig

    @classmethod
    def load(cls, config_path: str = "config.yaml") -> "Config":
        """Load configuration from YAML file with defaults."""
        if os.path.exists(config_path):
            with open(config_path, "r") as f:
                data = yaml.safe_load(f) or {}
        else:
            data = {}

        # Create nested dataclasses from dict
        camera = CameraConfig(**data.get("camera", {}))
        serial = SerialConfig(**data.get("serial", {}))
        tracking = TrackingConfig(**data.get("tracking", {}))
        servo = ServoConfig(**data.get("servo", {}))
        led = LEDConfig(**data.get("led", {}))
        faces = FacesConfig(**data.get("faces", {}))
        debug = DebugConfig(**data.get("debug", {}))

        return cls(
            camera=camera,
            serial=serial,
            tracking=tracking,
            servo=servo,
            led=led,
            faces=faces,
            debug=debug,
        )

    def save(self, config_path: str = "config.yaml") -> None:
        """Save current configuration to YAML file."""
        data = {
            "camera": self.camera.__dict__,
            "serial": self.serial.__dict__,
            "tracking": self.tracking.__dict__,
            "servo": self.servo.__dict__,
            "led": self.led.__dict__,
            "faces": self.faces.__dict__,
            "debug": self.debug.__dict__,
        }
        os.makedirs(os.path.dirname(config_path) or ".", exist_ok=True)
        with open(config_path, "w") as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)
