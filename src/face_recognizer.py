"""
Face recognition module.
Handles loading face encodings and recognizing faces in frames.
"""

import pickle
import face_recognition
import numpy as np
import logging
from typing import Dict, List, Tuple, Optional
from pathlib import Path


class FaceRecognizer:
    """
    Recognizes faces from stored encodings.
    Supports single or multiple face recognition.
    """

    def __init__(
        self,
        model_path: str = "models/teacher_face.pkl",
        tolerance: float = 0.5,
        multi_face: bool = False,
        names: Optional[List[str]] = None,
    ):
        """
        Initialize face recognizer.

        Args:
            model_path: Path to pickle file with face encodings
            tolerance: Recognition tolerance (0-1, lower = stricter)
            multi_face: Whether to recognize multiple different faces
            names: List of names corresponding to stored encodings
        """
        self.model_path = model_path
        self.tolerance = tolerance
        self.multi_face = multi_face
        self.names = names or ["teacher"]
        self.known_encodings: List[np.ndarray] = []
        self.known_names: List[str] = []
        self.logger = logging.getLogger(__name__)
        self.loaded = False

        self.load()

    def load(self) -> bool:
        """
        Load face encodings from pickle file.

        Returns:
            True if loaded successfully
        """
        try:
            path = Path(self.model_path)
            if not path.exists():
                self.logger.error(f"Face model not found: {self.model_path}")
                return False

            with open(self.model_path, "rb") as f:
                data = pickle.load(f)

            if isinstance(data, dict):
                # Multiple faces stored as dict: {name: encoding}
                self.known_encodings = list(data.values())
                self.known_names = list(data.keys())
            elif isinstance(data, np.ndarray):
                # Single encoding stored as array
                self.known_encodings = [data]
                self.known_names = self.names[:1]
            else:
                self.logger.error(f"Unknown pickle format: {type(data)}")
                return False

            self.logger.info(
                f"Loaded {len(self.known_encodings)} face(s): {', '.join(self.known_names)}"
            )
            self.loaded = True
            return True

        except Exception as e:
            self.logger.error(f"Failed to load face encodings: {e}")
            return False

    def reload(self) -> bool:
        """Reload face encodings from disk."""
        return self.load()

    def recognize(self, frame_rgb: np.ndarray) -> Tuple[Optional[np.ndarray], str, float]:
        """
        Recognize faces in RGB frame.

        Args:
            frame_rgb: RGB image as numpy array

        Returns:
            Tuple of (encoding, name, distance) or (None, "", 1.0) if no match
        """
        if not self.loaded:
            self.logger.error("Face recognizer not loaded")
            return None, "", 1.0

        # Detect all faces in frame
        boxes = face_recognition.face_locations(frame_rgb, model="hog")
        if not boxes:
            return None, "", 1.0

        # Get encodings for all detected faces
        encodings = face_recognition.face_encodings(frame_rgb, boxes)

        for encoding in encodings:
            # Compare against known faces
            distances = face_recognition.face_distance(self.known_encodings, encoding)
            min_distance_idx = np.argmin(distances)
            min_distance = distances[min_distance_idx]

            if min_distance < self.tolerance:
                name = self.known_names[min_distance_idx]
                self.logger.debug(f"Recognized: {name} (distance: {min_distance:.3f})")
                return encoding, name, min_distance

        # No match found
        return None, "", 1.0

    def recognize_multiple(
        self, frame_rgb: np.ndarray
    ) -> List[Tuple[np.ndarray, str, float, Tuple[int, int, int, int]]]:
        """
        Recognize all matching faces in frame.

        Args:
            frame_rgb: RGB image

        Returns:
            List of tuples: (encoding, name, distance, face_box)
        """
        if not self.loaded or not self.multi_face:
            enc, name, dist = self.recognize(frame_rgb)
            if enc is not None:
                # Get the box for this face
                boxes = face_recognition.face_locations(frame_rgb, model="hog")
                if boxes:
                    return [(enc, name, dist, boxes[0])]
            return []

        results = []
        boxes = face_recognition.face_locations(frame_rgb, model="hog")
        encodings = face_recognition.face_encodings(frame_rgb, boxes)

        for box, encoding in zip(boxes, encodings):
            distances = face_recognition.face_distance(self.known_encodings, encoding)
            min_idx = np.argmin(distances)
            min_dist = distances[min_idx]

            if min_dist < self.tolerance:
                name = self.known_names[min_idx]
                results.append((encoding, name, min_dist, box))

        return results

    def get_face_center(self, box: Tuple[int, int, int, int]) -> int:
        """
        Get horizontal center of face bounding box.

        Args:
            box: Face box as (top, right, bottom, left)

        Returns:
            X coordinate of face center
        """
        top, right, bottom, left = box
        return (left + right) // 2

    def get_known_faces(self) -> List[str]:
        """Get list of known face names."""
        return self.known_names.copy()


def capture_face_encoding(
    camera_index: int = 0,
    output_path: str = "models/teacher_face.pkl",
) -> Optional[np.ndarray]:
    """
    Capture a single face encoding from camera.

    Args:
        camera_index: Camera device index
        output_path: Where to save the encoding

    Returns:
        Captured encoding or None if cancelled
    """
    import cv2

    cap = cv2.VideoCapture(camera_index)
    if not cap.isOpened():
        logging.error(f"Cannot open camera {camera_index}")
        return None

    print("\n" + "=" * 50)
    print("FACE CAPTURE MODE")
    print("=" * 50)
    print("Position your face in the camera view.")
    print("Press SPACE when ready to capture.")
    print("Press Q to quit without saving.")
    print("=" * 50 + "\n")

    encoding = None

    while True:
        ret, frame = cap.read()
        if not ret:
            continue

        frame = cv2.flip(frame, 1)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Detect faces
        boxes = face_recognition.face_locations(rgb)
        for top, right, bottom, left in boxes:
            cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 255), 2)
            cv2.putText(
                frame,
                "Face Detected - Press SPACE",
                (left, top - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 255, 255),
                2,
            )

        cv2.imshow("Capture Face", frame)
        key = cv2.waitKey(1) & 0xFF

        if key == ord(" "):  # SPACE
            if boxes:
                encodings = face_recognition.face_encodings(rgb, boxes)
                encoding = encodings[0]

                # Save to file
                Path(output_path).parent.mkdir(parents=True, exist_ok=True)
                with open(output_path, "wb") as f:
                    pickle.dump(encoding, f)

                print(f"\n✅ Face saved to {output_path}")
                break
            else:
                print("\n⚠️  No face detected! Please position your face in view.")

        elif key == ord("q"):
            print("\n❌ Capture cancelled")
            break

    cap.release()
    cv2.destroyAllWindows()
    return encoding


def capture_multiple_faces(
    camera_index: int = 0,
    output_path: str = "models/faces.pkl",
    names: Optional[List[str]] = None,
) -> bool:
    """
    Capture multiple face encodings (for multi-face mode).

    Args:
        camera_index: Camera device index
        output_path: Where to save encodings
        names: List of names to capture

    Returns:
        True if successful
    """
    import cv2

    if names is None:
        names = ["person1", "person2"]

    cap = cv2.VideoCapture(camera_index)
    if not cap.isOpened():
        logging.error(f"Cannot open camera {camera_index}")
        return False

    encodings = {}
    print("\n" + "=" * 50)
    print("MULTI-FACE CAPTURE MODE")
    print("=" * 50)

    for name in names:
        print(f"\nCapturing face for: {name}")
        print("Press SPACE when ready, or Q to skip")
        print("-" * 50)

        while True:
            ret, frame = cap.read()
            if not ret:
                continue

            frame = cv2.flip(frame, 1)
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            boxes = face_recognition.face_locations(rgb)
            for top, right, bottom, left in boxes:
                cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 255), 2)
                cv2.putText(
                    frame,
                    f"Face: {name}",
                    (left, top - 10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (0, 255, 255),
                    2,
                )

            cv2.imshow("Capture Face", frame)
            key = cv2.waitKey(1) & 0xFF

            if key == ord(" "):
                if boxes:
                    encs = face_recognition.face_encodings(rgb, boxes)
                    encodings[name] = encs[0]
                    print(f"✅ Captured {name}")
                    break
                else:
                    print("⚠️  No face detected!")
            elif key == ord("q"):
                print(f"⏭️  Skipped {name}")
                break

    # Save all encodings
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "wb") as f:
        pickle.dump(encodings, f)

    print(f"\n✅ Saved {len(encodings)} face(s) to {output_path}")

    cap.release()
    cv2.destroyAllWindows()
    return True
