"""
Face capture script - standalone entry point for capturing teacher face encoding.
"""

import argparse
import logging
from pathlib import Path
from .config_loader import Config
from .face_recognizer import capture_face_encoding, capture_multiple_faces


def setup_logging(level: str = "INFO", log_file: str = "logs/face_capture.log"):
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
    """Main entry point for face capture."""
    parser = argparse.ArgumentParser(
        description="Capture face encodings for face tracking system"
    )
    parser.add_argument(
        "-c",
        "--config",
        default="config.yaml",
        help="Path to configuration file",
    )
    parser.add_argument(
        "-o",
        "--output",
        help="Output path for face encoding (overrides config)",
    )
    parser.add_argument(
        "--multi",
        action="store_true",
        help="Capture multiple faces",
    )
    parser.add_argument(
        "--names",
        nargs="+",
        help="Names for multi-face capture (space-separated)",
    )
    parser.add_argument(
        "--camera",
        type=int,
        help="Camera index (overrides config)",
    )

    args = parser.parse_args()

    # Load config
    config = Config.load(args.config)
    faces_config = config.faces

    # Setup logging
    setup_logging(config.debug.log_level, "logs/face_capture.log")
    logger = logging.getLogger(__name__)

    # Determine output path
    output_path = args.output or faces_config.model_path
    camera_index = args.camera if args.camera is not None else config.camera.index

    logger.info("=" * 60)
    logger.info("FACE CAPTURE STARTED")
    logger.info(f"Camera index: {camera_index}")
    logger.info(f"Output: {output_path}")
    logger.info("=" * 60)

    try:
        if args.multi or faces_config.multi_face:
            names = args.names or faces_config.names
            logger.info(f"Multi-face mode: capturing {len(names)} face(s)")
            success = capture_multiple_faces(
                camera_index=camera_index,
                output_path=output_path,
                names=names,
            )
        else:
            logger.info("Single-face mode")
            encoding = capture_face_encoding(
                camera_index=camera_index,
                output_path=output_path,
            )
            success = encoding is not None

        if success:
            logger.info("✅ Face capture completed successfully")
            return 0
        else:
            logger.error("❌ Face capture failed")
            return 1

    except KeyboardInterrupt:
        logger.info("\n⚠️  Interrupted by user")
        return 130
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
