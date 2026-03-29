#!/usr/bin/env python3
"""
Face Tracking Camera - Unified command-line interface.
Provides subcommands for capture, track, calibrate, and list ports.
"""

import sys
import argparse
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from src.config_loader import Config
    from src.face_capture import main as capture_main
    from src.face_tracker import main as track_main
    from src.camera import list_available_serial_ports, list_available_cameras
except ImportError as e:
    print(f"Error importing modules: {e}")
    print("Make sure you've run: pip install -r requirements.txt")
    sys.exit(1)


def list_cameras_command(args):
    """List available cameras."""
    cameras = list_available_cameras()
    print("Available cameras:")
    for idx in cameras:
        print(f"  - Camera {idx}")
    if not cameras:
        print("  No cameras found!")
    return 0


def list_ports_command(args):
    """List available serial ports."""
    ports = list_available_serial_ports()
    print("Available serial ports:")
    for port in ports:
        print(f"  - {port}")
    if not ports:
        print("  No serial ports found!")
    return 0


def calibrate_command(args):
    """Run servo calibration."""
    from src.servo_controller import ServoController
    import time

    print("=" * 60)
    print("SERVO CALIBRATION MODE")
    print("=" * 60)
    print("This will help you find the correct servo angle range.")
    print("The servo will sweep through its full range.")
    print("Use UP/DOWN arrows to adjust, ENTER to confirm.")
    print("=" * 60 + "\n")

    config = Config.load(args.config)

    servo = ServoController(
        port=config.serial.port,
        baud_rate=config.serial.baud_rate,
        min_angle=0,
        max_angle=180,
    )

    if not servo.connect():
        print("❌ Failed to connect to Arduino. Check connections.")
        return 1

    try:
        # Sweep to find limits
        print("Sweeping servo from 0 to 180 degrees...")
        print("Watch the camera movement and note min/max positions.")
        print("Press ENTER to stop sweep and continue.")

        import threading
        import sys

        stop_sweep = False

        def wait_for_enter():
            input()
            nonlocal stop_sweep
            stop_sweep = True

        # Start listener thread
        thread = threading.Thread(target=wait_for_enter, daemon=True)
        thread.start()

        angle = 0
        direction = 3  # Sweep speed
        while not stop_sweep:
            angle += direction
            if angle >= 180 or angle <= 0:
                direction *= -1
                angle = max(0, min(180, angle))
            servo.set_angle(angle)
            time.sleep(0.05)
            if cv2 and cv2.waitKey(1) & 0xFF == ord("q"):
                break

        servo.set_angle(90)
        print(f"\nCurrent calibration in config:")
        print(f"  servo.min_angle: {config.servo.default_min}")
        print(f"  servo.max_angle: {config.servo.default_max}")

        print("\nEnter new limits based on your observation:")

        try:
            new_min = input(f"  Min angle (default {config.servo.default_min}): ") or config.servo.default_min
            new_min = int(new_min)
            new_max = input(f"  Max angle (default {config.servo.default_max}): ") or config.servo.default_max
            new_max = int(new_max)
        except ValueError:
            print("Invalid input. Using defaults.")
            new_min, new_max = config.servo.default_min, config.servo.default_max

        # Update config
        config.servo.default_min = new_min
        config.servo.default_max = new_max
        config.servo.min_angle = min(new_min, new_max)
        config.servo.max_angle = max(new_min, new_max)

        config.save(args.config)
        print(f"\n✅ Calibration saved to {args.config}")
        print(f"   servo.default_min: {new_min}")
        print(f"   servo.default_max: {new_max}")

        return 0

    except KeyboardInterrupt:
        print("\n⚠️  Calibration interrupted")
        return 130
    finally:
        servo.close()


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Face Tracking Camera System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Capture command
    capture_parser = subparsers.add_parser("capture", help="Capture face encoding(s)")
    capture_parser.add_argument(
        "-c",
        "--config",
        default="config.yaml",
        help="Path to configuration file",
    )
    capture_parser.add_argument(
        "-o",
        "--output",
        help="Output path for face encoding",
    )
    capture_parser.add_argument(
        "--multi",
        action="store_true",
        help="Capture multiple faces",
    )
    capture_parser.add_argument(
        "--names",
        nargs="+",
        help="Names for multi-face capture",
    )
    capture_parser.add_argument(
        "--camera",
        type=int,
        help="Camera index",
    )

    # Track command
    track_parser = subparsers.add_parser("track", help="Run face tracking")
    track_parser.add_argument(
        "-c",
        "--config",
        default="config.yaml",
        help="Path to configuration file",
    )
    track_parser.add_argument(
        "--camera",
        type=int,
        help="Camera index",
    )
    track_parser.add_argument(
        "--port",
        help="Serial port (or 'auto' for auto-detect)",
    )
    track_parser.add_argument(
        "--tolerance",
        type=float,
        help="Face recognition tolerance",
    )
    track_parser.add_argument(
        "--smoothing",
        type=float,
        help="Servo smoothing factor",
    )
    track_parser.add_argument(
        "--no-video",
        action="store_true",
        help="Hide video window",
    )

    # Calibrate command
    calibrate_parser = subparsers.add_parser("calibrate", help="Calibrate servo range")
    calibrate_parser.add_argument(
        "-c",
        "--config",
        default="config.yaml",
        help="Path to configuration file",
    )
    calibrate_parser.add_argument(
        "--port",
        help="Serial port (overrides config)",
    )

    # List cameras command
    list_cameras_parser = subparsers.add_parser("cameras", help="List available cameras")

    # List ports command
    list_ports_parser = subparsers.add_parser("ports", help="List available serial ports")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    # Route to appropriate command
    try:
        if args.command == "capture":
            return capture_main([sys.argv[0]] + sys.argv[2:]) if len(sys.argv) > 2 else capture_main([])
        elif args.command == "track":
            return track_main([sys.argv[0]] + sys.argv[2:]) if len(sys.argv) > 2 else track_main([])
        elif args.command == "calibrate":
            # Need cv2 for calibrate
            import cv2  # lazy import
            globals()['cv2'] = cv2
            return calibrate_command(args)
        elif args.command == "cameras":
            return list_cameras_command(args)
        elif args.command == "ports":
            return list_ports_command(args)
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
