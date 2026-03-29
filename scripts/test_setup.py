#!/usr/bin/env python3
"""
Setup verification script for Face Tracking Camera.
Tests all components without actually tracking.
"""

import sys
from pathlib import Path

# Add parent dir to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import argparse
import logging

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def test_config():
    """Test configuration loading."""
    logger.info("Testing configuration loading...")
    try:
        from src.config_loader import Config
        config = Config.load("config.yaml")
        logger.info("✓ Config loaded successfully")
        logger.info(f"  Camera index: {config.camera.index}")
        logger.info(f"  Serial port: {config.serial.port}")
        return True
    except Exception as e:
        logger.error(f"✗ Config load failed: {e}")
        return False


def test_camera():
    """Test camera access."""
    logger.info("Testing camera access...")
    try:
        from src.camera import Camera, list_available_cameras
        cameras = list_available_cameras()
        if not cameras:
            logger.warning("✗ No cameras found")
            return False
        logger.info(f"✓ Found cameras: {cameras}")

        # Try opening configured camera
        config = Config.load("config.yaml")
        cam = Camera(index=config.camera.index)
        if cam.open():
            logger.info(f"✓ Opened camera {config.camera.index}")
            cam.close()
            return True
        else:
            logger.error(f"✗ Failed to open camera {config.camera.index}")
            return False
    except Exception as e:
        logger.error(f"✗ Camera test failed: {e}")
        return False


def test_serial():
    """Test serial port detection."""
    logger.info("Testing serial port detection...")
    try:
        from src.camera import list_available_serial_ports
        from src.servo_controller import ServoController

        ports = list_available_serial_ports()
        if not ports:
            logger.warning("✗ No serial ports found")
            return False
        logger.info(f"✓ Found serial ports: {ports}")

        # Try connecting
        config = Config.load("config.yaml")
        servo = ServoController(port=config.serial.port)
        if servo.connect():
            logger.info(f"✓ Connected to Arduino on {servo.ser.port}")
            servo.close()
            return True
        else:
            logger.warning("✗ Could not connect to Arduino")
            logger.info("  Arduino might be turned off or on different port")
            return False
    except Exception as e:
        logger.error(f"✗ Serial test failed: {e}")
        return False


def test_face_recognition():
    """Test face recognition library."""
    logger.info("Testing face recognition library...")
    try:
        import face_recognition
        logger.info("✓ face_recognition module loaded")

        # Check for model file
        config = Config.load("config.yaml")
        model_path = Path(config.faces.model_path)
        if model_path.exists():
            logger.info(f"✓ Face model found: {model_path}")
            try:
                import pickle
                with open(model_path, "rb") as f:
                    data = pickle.load(f)
                encodings = list(data.values()) if isinstance(data, dict) else [data]
                logger.info(f"  Loaded {len(encodings)} face encoding(s)")
            except Exception as e:
                logger.warning(f"✗ Failed to load face model: {e}")
                return False
        else:
            logger.warning(f"✗ Face model not found: {model_path}")
            logger.info("  Run: python scripts/run.py capture")
            return False

        return True
    except ImportError:
        logger.error("✗ face_recognition library not installed")
        logger.info("  Run: pip install -r requirements.txt")
        return False
    except Exception as e:
        logger.error(f"✗ Face recognition test failed: {e}")
        return False


def test_all():
    """Run all tests."""
    logger.info("=" * 60)
    logger.info("FACE TRACKING CAMERA - SETUP VERIFICATION")
    logger.info("=" * 60)
    logger.info("")

    results = []
    results.append(("Configuration", test_config()))
    logger.info("")
    results.append(("Camera", test_camera()))
    logger.info("")
    results.append(("Serial/Arduino", test_serial()))
    logger.info("")
    results.append(("Face Recognition", test_face_recognition()))

    logger.info("")
    logger.info("=" * 60)
    logger.info("SUMMARY")
    logger.info("=" * 60)

    all_passed = True
    for name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        logger.info(f"{name:.<40} {status}")
        if not passed:
            all_passed = False

    logger.info("=" * 60)

    if all_passed:
        logger.info("✅ All tests passed! System ready for tracking.")
        logger.info("Run: python scripts/run.py track")
        return 0
    else:
        logger.error("❌ Some tests failed. See above for details.")
        return 1


def main():
    parser = argparse.ArgumentParser(description="Verify setup")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    return test_all()


if __name__ == "__main__":
    sys.exit(main())
