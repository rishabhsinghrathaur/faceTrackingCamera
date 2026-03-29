#!/usr/bin/env python3
"""
Servo calibration tool for Face Tracking Camera.
Helps find the correct servo angle range for your specific camera mount.
"""

import sys
import argparse
import time
import logging
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config_loader import Config
from src.servo_controller import ServoController


def setup_logging():
    """Configure logging."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s: %(message)s",
    )


def interactive_calibration(servo: ServoController, config: Config):
    """
    Run interactive calibration session.

    Args:
        servo: ServoController instance
        config: Current configuration
    """
    print("\n" + "=" * 70)
    print(" SERVO CALIBRATION WIZARD")
    print("=" * 70)
    print("\nGoal: Find the servo angles where your camera's left and right limits occur.")
    print("\nInstructions:")
    print("  1. Watch the camera movement")
    print("  2. Use arrow keys or manual input to adjust")
    print("  3. When left limit is reached, press ENTER")
    print("  4. Then adjust to right limit")
    print("  5. Values will be saved to config.yaml")
    print("\nCommands during sweep:")
    print("  - UP/DOWN arrows or + / - : adjust angle")
    print("  - ENTER : confirm current position")
    print("  - Q : quit without saving")
    print("=" * 70)

    input("\nPress ENTER to start calibration...")

    # Sweep to find initial limits
    print("\n[Step 1] sweeping full range (0-180)...")
    print("Watch for the physical limits of your camera mount.")
    print("Press ENTER to stop sweep when near desired end point.")

    import threading

    stop_sweep = False

    def wait_for_enter():
        input()
        nonlocal stop_sweep
        stop_sweep = True

    thread = threading.Thread(target=wait_for_enter, daemon=True)
    thread.start()

    angle = 0
    direction = 3
    try:
        import cv2
        cv2.namedWindow("Calibration", cv2.WINDOW_NORMAL)
    except:
        pass

    while not stop_sweep:
        angle += direction
        if angle >= 180 or angle <= 0:
            direction *= -1
            angle = max(0, min(180, angle))

        servo.set_angle(angle)

        try:
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
        except:
            pass

        time.sleep(0.05)

    servo.set_angle(90)
    print("\nCurrent config limits:")
    print(f"  min_angle: {config.servo.default_min}")
    print(f"  max_angle: {config.servo.default_max}")

    # Get user input
    print("\n--- Enter new limits ---")

    try:
        new_min = input(
            f"Minimum angle (left limit) [{config.servo.default_min}]: "
        )
        new_min = int(new_min) if new_min else config.servo.default_min

        new_max = input(
            f"Maximum angle (right limit) [{config.servo.default_max}]: "
        )
        new_max = int(new_max) if new_max else config.servo.default_max

        # Validate
        if new_min >= new_max:
            print("❌ Error: min must be less than max!")
            return False

        if not (0 <= new_min <= 180 and 0 <= new_max <= 180):
            print("❌ Error: angles must be between 0 and 180!")
            return False

        # Test the limits
        print("\n[Testing] Moving to min angle...")
        servo.set_angle(new_min)
        time.sleep(1)

        print("[Testing] Moving to max angle...")
        servo.set_angle(new_max)
        time.sleep(1)

        print("[Testing] Moving to center...")
        servo.set_angle(90)
        time.sleep(0.5)

        # Confirm
        confirm = input(
            f"\nSave these limits? (min={new_min}, max={new_max}) [y/N]: "
        ).lower()

        if confirm == "y":
            config.servo.default_min = new_min
            config.servo.default_max = new_max
            config.servo.min_angle = min(new_min, new_max)
            config.servo.max_angle = max(new_min, new_max)

            config.save()
            print(f"\n✅ Calibration saved to config.yaml")
            print(f"   servo.default_min: {new_min}")
            print(f"   servo.default_max: {new_max}")

            # Optional: test tracking behavior
            test = input("\nRun a quick tracking test? [y/N]: ").lower()
            if test == "y":
                print("\n[Test] Move your face in front of camera.")
                print("Servo should follow. Press ENTER to finish test.")
                threading.Thread(target=lambda: input(), daemon=True).start()

                # Simple test loop (30 seconds or until enter)
                start = time.time()
                while not stop_sweep and time.time() - start < 30:
                    # In a real scenario, this would use the face tracker
                    # For now, just move servo in sine wave to demonstrate
                    import math
                    test_angle = 90 + int(30 * math.sin(time.time() * 2))
                    servo.set_angle(test_angle)
                    time.sleep(0.05)

                stop_sweep = True
                print("Test complete.")

            return True
        else:
            print("Calibration cancelled.")
            return False

    except KeyboardInterrupt:
        print("\n⚠️  Calibration interrupted")
        return False
    except ValueError:
        print("❌ Invalid input. Please enter numbers.")
        return False


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Calibrate servo range for face tracking camera"
    )
    parser.add_argument(
        "-c",
        "--config",
        default="config.yaml",
        help="Path to configuration file",
    )
    parser.add_argument(
        "-p",
        "--port",
        help="Serial port (overrides config)",
    )
    parser.add_argument(
        "--min",
        type=int,
        help="Set minimum angle directly (skip interactive)",
    )
    parser.add_argument(
        "--max",
        type=int,
        help="Set maximum angle directly (skip interactive)",
    )

    args = parser.parse_args()
    setup_logging()

    logger = logging.getLogger(__name__)

    try:
        # Load config
        config = Config.load(args.config)
        logger.info(f"Loaded config from {args.config}")

        # Override port if specified
        if args.port:
            config.serial.port = args.port

        # Connect to servo
        logger.info("Connecting to Arduino...")
        servo = ServoController(
            port=config.serial.port,
            baud_rate=config.serial.baud_rate,
            min_angle=0,
            max_angle=180,
        )

        if not servo.connect():
            logger.error("Failed to connect to Arduino")
            print("\n❌ Connection failed!")
            print("\nTroubleshooting:")
            print("  1. Check USB cable connection")
            print("  2. Make sure Arduino is powered")
            print("  3. Verify port in config.yaml or use --port")
            print("  4. List available ports: python scripts/run.py ports")
            return 1

        print("\n✅ Connected to Arduino!")

        # Direct set mode?
        if args.min is not None and args.max is not None:
            if 0 <= args.min < args.max <= 180:
                config.servo.default_min = args.min
                config.servo.default_max = args.max
                config.servo.min_angle = args.min
                config.servo.max_angle = args.max
                config.save()
                print(f"\n✅ Set limits: min={args.min}, max={args.max}")
                print("Calibration saved to config.yaml")
                return 0
            else:
                print("❌ Invalid angles. min < max, both in [0, 180].")
                return 1

        # Interactive mode
        success = interactive_calibration(servo, config)
        servo.close()

        return 0 if success else 1

    except KeyboardInterrupt:
        print("\n⚠️  Calibration interrupted")
        return 130
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        print(f"\n❌ Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
