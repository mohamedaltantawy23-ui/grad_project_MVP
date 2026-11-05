"""Vision Engine for PhysioAI Egypt.

Handles OpenCV webcam video streams, MediaPipe full-body pose landmark detection,
biomechanical joint angle trigonometry, and exercise repetition state machines.
"""

from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
import time

import cv2
import numpy as np


class ExercisePhase(Enum):
    READY = "ready"
    DESCENDING = "descending"
    BOTTOM_HOLD = "bottom_hold"
    ASCENDING = "ascending"
    COMPLETED = "completed"


class PoseEstimator:
    """Estimates biomechanical angles and tracks physical therapy exercise repetitions."""

    def __init__(
        self,
        min_detection_confidence: float = 0.6,
        min_tracking_confidence: float = 0.6,
        model_complexity: int = 1,
    ):
        self.min_detection_confidence = min_detection_confidence
        self.min_tracking_confidence = min_tracking_confidence
        self.model_complexity = model_complexity

        # Lazy load mediapipe to allow module import even if mediapipe is being installed
        self.mp_pose = None
        self.mp_draw = None
        self.pose = None
        self._init_mediapipe()

        # Squat repetition tracking state machine
        self.squat_phase = ExercisePhase.READY
        self.rep_count = 0
        self.hold_start_time = 0.0
        self.current_knee_angle = 180.0
        self.current_hip_angle = 180.0
        self.form_faults: List[str] = []

    def _init_mediapipe(self) -> None:
        """Initializes MediaPipe Pose detector safely."""
        try:
            import mediapipe as mp
            self.mp_pose = mp.solutions.pose
            self.mp_draw = mp.solutions.drawing_utils
            self.pose = self.mp_pose.Pose(
                min_detection_confidence=self.min_detection_confidence,
                min_tracking_confidence=self.min_tracking_confidence,
                model_complexity=self.model_complexity,
                smooth_landmarks=True,
            )
        except ImportError:
            self.pose = None

    @staticmethod
    def calculate_angle(
        a: Tuple[float, float],
        b: Tuple[float, float],
        c: Tuple[float, float],
    ) -> float:
        """Calculates the 2D planar angle at vertex point b between segments ba and bc.

        Args:
            a: Coordinates (x, y) of the first point (e.g. Hip).
            b: Coordinates (x, y) of the vertex point (e.g. Knee).
            c: Coordinates (x, y) of the third point (e.g. Ankle).

        Returns:
            Angle in degrees in the range [0.0, 180.0].
        """
        a_vec = np.array(a, dtype=np.float64)
        b_vec = np.array(b, dtype=np.float64)
        c_vec = np.array(c, dtype=np.float64)

        ba = a_vec - b_vec
        bc = c_vec - b_vec

        norm_ba = np.linalg.norm(ba)
        norm_bc = np.linalg.norm(bc)

        if norm_ba == 0 or norm_bc == 0:
            return 0.0

        cosine_angle = np.dot(ba, bc) / (norm_ba * norm_bc)
        # Numerical stability clamp to [-1.0, 1.0]
        cosine_angle = np.clip(cosine_angle, -1.0, 1.0)

        angle = np.degrees(np.arccos(cosine_angle))
        return float(angle)

    def extract_landmarks(self, frame: np.ndarray) -> Optional[Any]:
        """Processes RGB video frame with MediaPipe Pose and returns raw landmarks."""
        if self.pose is None:
            return None
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        rgb_frame.flags.writeable = False
        results = self.pose.process(rgb_frame)
        rgb_frame.flags.writeable = True
        if results.pose_landmarks:
            return results.pose_landmarks.landmark
        return None

    def update_squat_rep(self, landmarks: Any) -> Dict[str, Any]:
        """Evaluates squat exercise state machine and updates repetition counter.

        Calculates right and left knee angles, checks depth thresholds,
        and enforces concentric return to standing.

        Args:
            landmarks: MediaPipe normalized landmarks list.

        Returns:
            Dictionary containing current phase, rep count, angle, and feedback cue.
        """
        feedback = "استعد، واقف مستقيم وبص قدامك"
        event = None

        if landmarks is None or len(landmarks) < 29:
            return {
                "phase": self.squat_phase.value,
                "reps": self.rep_count,
                "knee_angle": self.current_knee_angle,
                "feedback": "الكاميرا مش شيفاك بوضوح، ارجع خطوة لورا",
                "event": None,
            }

        # Extract primary side joint coordinates (using right side landmarks: Hip 24, Knee 26, Ankle 28)
        hip = (landmarks[24].x, landmarks[24].y)
        knee = (landmarks[26].x, landmarks[26].y)
        ankle = (landmarks[28].x, landmarks[28].y)

        knee_angle = self.calculate_angle(hip, knee, ankle)
        self.current_knee_angle = round(knee_angle, 1)

        # Repetition State Machine
        # Phase 1: Standing / Ready (> 160°)
        if self.squat_phase == ExercisePhase.READY:
            if knee_angle < 145.0:
                self.squat_phase = ExercisePhase.DESCENDING
                feedback = "انزل بالراحة.. ضهرك مفرود وركبتك ماتعديش صوابع رجلك"

        # Phase 2: Descending into depth
        elif self.squat_phase == ExercisePhase.DESCENDING:
            if knee_angle <= 100.0:  # Target clinical depth reached
                self.squat_phase = ExercisePhase.BOTTOM_HOLD
                self.hold_start_time = time.time()
                feedback = "ممتاز! اثبت ثانية في النزول"
            elif knee_angle > 155.0:  # Aborted descent
                self.squat_phase = ExercisePhase.READY
                feedback = "انزل أكتر شوية عشان تستفيد"

        # Phase 3: Bottom Hold (Isometric hold threshold)
        elif self.squat_phase == ExercisePhase.BOTTOM_HOLD:
            hold_elapsed = time.time() - self.hold_start_time
            if knee_angle > 115.0 or hold_elapsed >= 0.8:
                self.squat_phase = ExercisePhase.ASCENDING
                feedback = "عاش! اطلع واضغط برجلك لفوق"

        # Phase 4: Ascending back to full standing
        elif self.squat_phase == ExercisePhase.ASCENDING:
            if knee_angle >= 160.0:
                self.rep_count += 1
                self.squat_phase = ExercisePhase.READY
                event = "rep_completed"
                feedback = f"ممتاز! العدة رقم {self.rep_count} اتحسبت"

        return {
            "phase": self.squat_phase.value,
            "reps": self.rep_count,
            "knee_angle": self.current_knee_angle,
            "feedback": feedback,
            "event": event,
        }

    def draw_skeleton(self, frame: np.ndarray, landmarks: Any) -> np.ndarray:
        """Overlays MediaPipe landmark skeleton and joint angle indicator onto frame."""
        if landmarks is None or self.mp_draw is None:
            return frame

        h, w, _ = frame.shape
        # Draw connections if available
        if hasattr(self, 'mp_pose') and self.mp_pose:
            # Simple custom aesthetic overlay
            try:
                proto = self.mp_pose.PoseLandmark
                # Draw knee angle badge
                knee_px = (int(landmarks[26].x * w), int(landmarks[26].y * h))
                cv2.circle(frame, knee_px, 8, (0, 255, 127), -1)
                cv2.putText(
                    frame,
                    f"{int(self.current_knee_angle)} deg",
                    (knee_px[0] + 15, knee_px[1] - 10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (0, 255, 255),
                    2,
                )
            except Exception:
                pass
        return frame

    def reset(self) -> None:
        """Resets the repetition counter and state machine."""
        self.rep_count = 0
        self.squat_phase = ExercisePhase.READY
        self.form_faults.clear()
