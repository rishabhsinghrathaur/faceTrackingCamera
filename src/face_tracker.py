"""
Face tracking script - main application loop.
Tracks teacher's face and controls servo to keep face centered.
"""

import argparse
import cv2
import logging
import time
import signal
import sys
from pathlib import Path
from typing import Optional, Tuple

from .config_loader import Config
from .camera import Camera
from .servo_controller import ServoController, SmoothedServo
from .face_recognizer import FaceRecognizer


class FaceTracker:
    """Main face tracking application."""

    def __init__(self, config: Config):
        """
        Initialize face tracker.

        Args:
            config: Configuration object
        """
        self.config = config
        self.logger = logging.getLogger(__name__)

        # Initialize components
        self.camera = Camera(
            index=config.camera.index,
            width=config.camera.width,
            height=config.camera.height,
            fps=config.camera.fps,
        )

        self.servo_controller = ServoController(
            port=config.serial.port,
            baud_rate=config.serial.baud_rate,
            timeout=config.serial.timeout,
            smoothing_alpha=config.tracking.smoothing_alpha,
            min_angle=min(config.servo.min_angle, config.servo.default_min),
            max_angle=max(config.servo.max_angle, config.servo.default_max),
        )

        self.servo = SmoothedServo(
            self.servo_controller,
            alpha=config.tracking.smoothing_alpha,
            dead_zone=config.tracking.min_servo_speed,
        )

        self.recognizer = FaceRecognizer(
            model_path=config.faces.model_path,
            tolerance=config.tracking.tolerance,
            multi_face=config.faces.multi_face,
            names=config.faces.names,
        )

        # State tracking
        self.running = False
        self.last_seen_time = time.time()
        self.searching_direction = 1  # 1 for right, -1 for left
        self.searching_frames = 0
        self.frame_count = 0
        self.fps_start_time = time.time()
        self.fps = 0.0
        self.current_face_name: Optional[str] = None

        # Set up signal handler for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """Handle Ctrl+C gracefully."""
        self.logger.info("\n⚠️  Shutdown signal received")
        self.running = False

    def connect(self) -> bool:
        """Connect to camera and Arduino."""
        self.logger.info("Connecting to hardware...")

        if not self.camera.open():
            self.logger.error("Failed to open camera")
            return False

        if not self.servo_controller.connect():
            self.logger.error("Failed to connect to Arduino")
            self.camera.close()
            return False

        # Center servo on start
        self.servo.reset()
        time.sleep(0.5)

        self.logger.info("✅ All hardware connected")
        return True

    def run(self) -> int:
        """
        Main tracking loop.

        Returns:
            Exit code (0 for success, 1 for error)
        """
        if not self.connect():
            return 1

        self.running = True
        self.logger.info("Starting face tracking loop...")
        print("\n" + "=" * 60)
        print("FACE TRACKING ACTIVE")
        print("Press 'q' to quit")
        print("=" * 60 + "\n")

        try:
            while self.running:
                # Read frame
                frame, ret = self.camera.read()
                if not ret:
                    self.logger.warning("Failed to read frame, retrying...")
                    time.sleep(0.1)
                    continue

                # Preprocess
                frame = self.camera.preprocess(frame, self.config.camera.flip_horizontal)
                height, width = self.camera.get_dimensions(frame)
                center_x = width // 2

                # Recognize faces
                rgb = self.camera.to_rgb(frame)
                recognized = self.recognizer.recognize(rgb)

                face_box = None
                servo_target = None

                if recognized[0] is not None:
                    # Face found!
                    encoding, name, distance = recognized
                    face_locations = face_recognition.face_locations(rgb, model="hog")
                    if face_locations:
                        face_box = face_locations[0]
                    self.current_face_name = name
                    self.last_seen_time = time.time()

                    # Calculate face center
                    face_center_x = self.recognizer.get_face_center(face_box)

                    # Calculate target servo angle
                    # Map face offset to servo angle adjustment
                    offset = face_center_x - center_x
                    adjustment = offset / (width / 2) * 45  # Scale to +/- 45 degrees

                    base_angle = self.config.servo.center_angle
                    servo_target = base_angle + adjustment

                    # Clamp to servo limits
                    servo_target = max(
                        self.servo_controller.min_angle,
                        min(self.servo_controller.max_angle, servo_target),
                    )

                    self.searching_frames = 0  # Reset search counter

                else:
                    # Face not seen - check timeout
                    time_since_seen = time.time() - self.last_seen_time
                    self.current_face_name = None

                    if time_since_seen > self.config.tracking.lost_face_timeout:
                        # Enter search mode
                        if self.searching_frames == 0:
                            self.logger.debug("Face lost - starting search")

                        servo_target = (
                            self.config.servo.center_angle
                            + self.searching_direction
                            * self.config.tracking.scanning_speed
                            * min(self.searching_frames / 20, 1.0)
                        )

                        # Clamp and reverse direction at limits
                        min_angle = min(self.servo_controller.min_angle, self.config.servo.default_min)
                        max_angle = max(self.servo_controller.max_angle, self.config.servo.default_max)
                        if servo_target >= max_angle or servo_target <= min_angle:
                            self.searching_direction *= -1
                            self.searching_frames = 0

                        self.searching_frames += 1

                # Update servo
                if servo_target is not None:
                    actual_angle = self.servo.update(servo_target)
                else:
                    actual_angle = self.servo.get_angle()

                # FPS calculation
                self.frame_count += 1
                if self.frame_count % 30 == 0:
                    elapsed = time.time() - self.fps_start_time
                    self.fps = self.frame_count / elapsed if elapsed > 0 else 0

                # Create overlay
                face_box_display = face_box if self.config.debug.show_guides else None
                status_text = "TRACKING" if self.current_face_name else "SEARCHING"
                if self.current_face_name:
                    status_text += f": {self.current_face_name}"

                frame = self.camera.add_overlay(
                    frame,
                    center_x,
                    height // 2,
                    self.config.tracking.center_tolerance,
                    status=status_text if self.config.debug.show_guides else "",
                    fps=self.fps if self.config.debug.show_fps else 0,
                    face_box=face_box_display,
                )

                # Display frame
                if self.config.debug.show_video:
                    cv2.imshow("Face Tracker", frame)

                # Check for quit key
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    self.logger.info("Quit requested")
                    break

            return 0

        except Exception as e:
            self.logger.exception(f"Error in tracking loop: {e}")
            return 1

        finally:
            self.shutdown()

    def shutdown(self):
        """Clean shutdown of all components."""
        self.logger.info("Shutting down...")

        self.running = False

        # Close camera
        try:
            self.camera.close()
        except Exception as e:
            self.logger.error(f"Error closing camera: {e}")

        # Center servo and close serial
        try:
            self.servo.reset()
            time.sleep(0.2)
            self.servo_controller.close()
        except Exception as e:
            self.logger.error(f"Error closing servo: {e}")

        cv2.destroyAllWindows()
        self.logger.info("Shutdown complete")


def setup_logging(level: str = "INFO", log_file: str = "logs/face_tracker.log"):
    """Configure logging."""
    log_level = getattr(logging, level.upper(), logging.INFO)
    Path(log_file).parent.mkdir(parents=True, exist_ok=True)

    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(),
        ],
    )


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Face tracking camera system for classrooms"
    )
    parser.add_argument(
        "-c",
        "--config",
        default="config.yaml",
        help="Path to configuration file",
    )
    parser.add_argument(
        "--camera",
        type=int,
        help="Camera index (overrides config)",
    )
    parser.add_argument(
        "--port",
        help="Serial port (overrides config, 'auto' for auto-detect)",
    )
    parser.add_argument(
        "--tolerance",
        type=float,
        help="Face recognition tolerance (lower = stricter)",
    )
    parser.add_argument(
        "--smoothing",
        type=float,
        help="Servo smoothing factor (0-1)",
    )
    parser.add_argument(
        "--no-video",
        action="store_true",
        help="Hide video window",
    )

    args = parser.parse_args()

    # Load config
    config = Config.load(args.config)

    # Override config with command-line args
    if args.camera is not None:
        config.camera.index = args.camera
    if args.port:
        config.serial.port = args.port
    if args.tolerance is not None:
        config.tracking.tolerance = args.tolerance
    if args.smoothing is not None:
        config.tracking.smoothing_alpha = args.smoothing
    if args.no_video:
        config.debug.show_video = False

    # Setup logging
    setup_logging(config.debug.log_level, config.debug.log_file)
    logger = logging.getLogger(__name__)

    logger.info("=" * 60)
    logger.info("FACE TRACKER STARTED")
    logger.info(f"Config: {args.config}")
    logger.info(f"Camera index: {config.camera.index}")
    logger.info(f"Serial port: {config.serial.port}")
    logger.info(f"Tolerance: {config.tracking.tolerance}")
    logger.info(f"Smoothing: {config.tracking.smoothing_alpha}")
    logger.info("=" * 60)

    try:
        tracker = FaceTracker(config)
        return tracker.run()

    except KeyboardInterrupt:
        logger.info("\n⚠️  Interrupted by user")
        return 130
    except Exception as e:
        logger.exception(f"Fatal error: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
