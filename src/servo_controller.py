"""
Servo controller for Arduino-based camera pan-tilt.
Handles serial communication, smoothing, and LED status.
"""

import serial
import serial.tools.list_ports
import time
import logging
from typing import Optional, List
from threading import Lock


class ServoController:
    """
    Controls servo motor via Arduino with smoothing and LED status.
    """

    def __init__(
        self,
        port: str = "auto",
        baud_rate: int = 9600,
        timeout: float = 2.0,
        smoothing_alpha: float = 0.4,
        led_pin: int = 13,
        min_angle: int = 0,
        max_angle: int = 180,
    ):
        """
        Initialize servo controller.

        Args:
            port: Serial port name or "auto" for auto-detection
            baud_rate: Serial baud rate
            timeout: Read timeout in seconds
            smoothing_alpha: Smoothing factor (0-1, higher = more responsive)
            led_pin: Arduino pin for status LED
            min_angle: Minimum allowed servo angle
            max_angle: Maximum allowed servo angle
        """
        self.port = port
        self.baud_rate = baud_rate
        self.timeout = timeout
        self.smoothing_alpha = smoothing_alpha
        self.led_pin = led_pin
        self.min_angle = min_angle
        self.max_angle = max_angle

        self.ser: Optional[serial.Serial] = None
        self.last_angle: float = 90.0  # Start at center
        self.logger = logging.getLogger(__name__)
        self._lock = Lock()
        self._connected = False

    def _clamp(self, angle: float) -> int:
        """Clamp angle to valid range."""
        return max(self.min_angle, min(self.max_angle, int(angle)))

    def _auto_detect_port(self) -> Optional[str]:
        """Auto-detect Arduino serial port."""
        self.logger.info("Auto-detecting serial port...")
        ports = serial.tools.list_ports.comports()

        # Common Arduino identifiers
        arduino_keywords = ["arduino", "ttyACM", "ttyUSB", "usbmodem", "wchusbserial"]

        for port in ports:
            desc = port.description.lower()
            device = port.device.lower()
            self.logger.debug(f"Found port: {port.device} - {port.description}")

            for keyword in arduino_keywords:
                if keyword in desc or keyword in device:
                    self.logger.info(f"Detected Arduino on {port.device}")
                    return port.device

        # If no Arduino found, return first available port as fallback
        if ports:
            self.logger.warning(
                f"No Arduino detected. Using first available port: {ports[0].device}"
            )
            return ports[0].device

        self.logger.error("No serial ports found!")
        return None

    def connect(self, max_retries: int = 3) -> bool:
        """
        Connect to Arduino.

        Args:
            max_retries: Number of connection attempts

        Returns:
            True if connected successfully
        """
        port_to_use = self.port
        if self.port == "auto":
            port_to_use = self._auto_detect_port()
            if not port_to_use:
                return False

        for attempt in range(max_retries):
            try:
                self.logger.info(
                    f"Connecting to Arduino on {port_to_use} (attempt {attempt + 1})"
                )
                self.ser = serial.Serial(
                    port=port_to_use,
                    baudrate=self.baud_rate,
                    timeout=self.timeout,
                )
                time.sleep(2)  # Wait for Arduino to reset
                self._connected = True
                self.logger.info("Connected successfully")
                return True
            except serial.SerialException as e:
                self.logger.error(f"Connection failed: {e}")
                if attempt < max_retries - 1:
                    time.sleep(1)
                else:
                    self.logger.error("All connection attempts failed")
                    return False

        return False

    def set_angle(self, target_angle: float) -> int:
        """
        Set servo angle with smoothing.

        Args:
            target_angle: Desired angle (0-180)

        Returns:
            Actual angle sent to servo
        """
        with self._lock:
            # Apply exponential moving average smoothing
            smoothed_angle = (
                self.smoothing_alpha * target_angle
                + (1 - self.smoothing_alpha) * self.last_angle
            )

            # Apply minimum movement threshold (avoid jitter)
            diff = abs(smoothed_angle - self.last_angle)
            if diff < 0.5:  # Less than half degree, ignore
                return int(self.last_angle)

            # Clamp to valid range
            final_angle = self._clamp(smoothed_angle)
            self.last_angle = smoothed_angle

            # Send to Arduino
            self._send_angle(final_angle)

            return final_angle

    def _send_angle(self, angle: int) -> bool:
        """Send angle command to Arduino."""
        if not self.ser or not self.ser.is_open:
            self.logger.error("Serial port not open")
            return False

        try:
            # Format: "ANGLE\n" where ANGLE is integer
            command = f"{angle}\n"
            self.ser.write(command.encode())
            self.logger.debug(f"Sent angle: {angle}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to send angle: {e}")
            return False

    def set_led(self, on: bool) -> bool:
        """
        Set status LED on Arduino.

        Args:
            on: True for LED ON, False for OFF

        Returns:
            Success status
        """
        # Optional: Send LED command (requires Arduino code support)
        # For now, just log
        self.logger.debug(f"LED {'ON' if on else 'OFF'}")
        return True

    def center(self) -> int:
        """Center the servo."""
        return self.set_angle(90)

    def get_angle(self) -> int:
        """Get current servo angle (last sent)."""
        return int(self.last_angle)

    def close(self) -> None:
        """Close serial connection."""
        if self.ser and self.ser.is_open:
            try:
                self.ser.close()
                self.logger.info("Serial connection closed")
            except Exception as e:
                self.logger.error(f"Error closing serial: {e}")
        self._connected = False

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


class SmoothedServo:
    """
    Smoothing wrapper for any servo controller.
    Implements exponential moving average with dead zone.
    """

    def __init__(self, controller: ServoController, alpha: float = 0.4, dead_zone: float = 0.5):
        """
        Initialize smoothed servo.

        Args:
            controller: Underlying ServoController instance
            alpha: Smoothing factor (0-1)
            dead_zone: Minimum angle change to trigger movement (degrees)
        """
        self.controller = controller
        self.alpha = alpha
        self.dead_zone = dead_zone
        self._current_angle = 90.0

    def update(self, target_angle: float) -> int:
        """
        Update servo to target angle with smoothing.

        Args:
            target_angle: Target angle (0-180)

        Returns:
            Final angle sent
        """
        # Apply smoothing
        smoothed = self.alpha * target_angle + (1 - self.alpha) * self._current_angle

        # Apply dead zone
        diff = abs(smoothed - self._current_angle)
        if diff < self.dead_zone:
            return int(self._current_angle)

        self._current_angle = smoothed
        return self.controller.set_angle(smoothed)

    def reset(self) -> int:
        """Reset to center."""
        self._current_angle = 90.0
        return self.controller.set_angle(90)
