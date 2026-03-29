"""
Camera handling utilities for face tracking.
Provides camera capture, frame preprocessing, and camera utilities.
"""

import cv2
import logging
from typing import Optional, Tuple, Any, List
import time


class Camera:
    """Camera handler with preprocessing capabilities."""

    def __init__(self, index: int = 0, width: int = 640, height: int = 480, fps: int = 15):
        """
        Initialize camera.

        Args:
            index: Camera device index (usually 0 or 1)
            width: Desired frame width
            height: Desired frame height
            fps: Target FPS (will set if supported)
        """
        self.index = index
        self.width = width
        self.height = height
        self.fps = fps
        self.cap: Optional[cv2.VideoCapture] = None
        self.logger = logging.getLogger(__name__)

    def open(self) -> bool:
        """Open camera device."""
        try:
            self.cap = cv2.VideoCapture(self.index)
            if not self.cap.isOpened():
                self.logger.error(f"Failed to open camera {self.index}")
                return False

            # Set camera properties
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
            self.cap.set(cv2.CAP_PROP_FPS, self.fps)

            # Verify settings
            actual_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            actual_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            actual_fps = int(self.cap.get(cv2.CAP_PROP_FPS))

            self.logger.info(
                f"Camera opened: {self.index} - "
                f"{actual_width}x{actual_height} @ {actual_fps}fps"
            )
            return True
        except Exception as e:
            self.logger.error(f"Error opening camera: {e}")
            return False

    def read(self) -> Tuple[Optional[Any], bool]:
        """Read a frame from camera."""
        if self.cap is None or not self.cap.isOpened():
            self.logger.error("Camera not opened")
            return None, False

        ret, frame = self.cap.read()
        if not ret:
            self.logger.warning("Failed to read frame")
        return frame, ret

    def preprocess(self, frame: Any, flip: bool = True) -> Any:
        """
        Preprocess frame for face recognition.

        Args:
            frame: Input BGR frame
            flip: Whether to horizontally flip (mirror)

        Returns:
            Preprocessed frame
        """
        processed = frame.copy()
        if flip:
            processed = cv2.flip(processed, 1)
        return processed

    def to_rgb(self, frame: Any) -> Any:
        """Convert BGR frame to RGB."""
        return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    def get_dimensions(self, frame: Any) -> Tuple[int, int]:
        """Get frame height and width."""
        return frame.shape[:2]

    def add_overlay(
        self,
        frame: Any,
        center_x: int,
        center_y: int,
        tolerance: int,
        status: str = "",
        fps: float = 0.0,
        face_box: Optional[Tuple[int, int, int, int]] = None,
    ) -> Any:
        """
        Add visual guide overlays to frame.

        Args:
            frame: Input frame
            center_x: Horizontal center of tracking area
            center_y: Vertical center
            tolerance: Acceptable deviation from center
            status: Status text to display
            fps: Current FPS to display
            face_box: Face bounding box (top, right, bottom, left)

        Returns:
            Frame with overlays
        """
        height, width = frame.shape[:2]

        # Draw center guide line (vertical)
        cv2.line(frame, (center_x, 0), (center_x, height), (255, 0, 0), 2)

        # Draw tolerance zone
        cv2.line(
            frame,
            (center_x - tolerance, 0),
            (center_x - tolerance, height),
            (0, 255, 255),
            1,
        )
        cv2.line(
            frame,
            (center_x + tolerance, 0),
            (center_x + tolerance, height),
            (0, 255, 255),
            1,
        )

        # Draw face bounding box if provided
        if face_box:
            top, right, bottom, left = face_box
            cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)

        # Draw status text
        if status:
            cv2.putText(
                frame,
                status,
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 0),
                2,
            )

        # Draw FPS
        if fps > 0:
            cv2.putText(
                frame,
                f"FPS: {fps:.1f}",
                (10, height - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (255, 255, 0),
                2,
            )

        return frame

    def close(self) -> None:
        """Release camera resources."""
        if self.cap is not None:
            self.cap.release()
            self.cap = None
            self.logger.info("Camera released")

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


def list_available_cameras(max_cameras: int = 10) -> List[int]:
    """
    List all available camera indices.

    Returns:
        List of working camera indices
    """
    available = []
    for i in range(max_cameras):
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            available.append(i)
            cap.release()
    return available


def list_available_serial_ports():
    """List all available serial ports."""
    import serial.tools.list_ports

    ports = serial.tools.list_ports.comports()
    return [port.device for port in ports]
