"""Unit Tests for Vision Engine Joint Angle Mathematics in PhysioAI Egypt."""

from pathlib import Path
import sys
import unittest

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.vision_engine import PoseEstimator


class TestJointAngleCalculation(unittest.TestCase):
    """Verifies 2D trigonometric joint angle calculation accuracy."""

    def test_straight_line_180_degrees(self):
        """Points forming a colinear straight line should return exactly 180 degrees."""
        hip = (0.0, 0.0)
        knee = (0.0, 1.0)
        ankle = (0.0, 2.0)
        angle = PoseEstimator.calculate_angle(hip, knee, ankle)
        self.assertAlmostEqual(angle, 180.0, places=1)

    def test_right_angle_90_degrees(self):
        """Points forming an L-shape right angle should return 90 degrees."""
        hip = (0.0, 0.0)
        knee = (0.0, 1.0)
        ankle = (1.0, 1.0)
        angle = PoseEstimator.calculate_angle(hip, knee, ankle)
        self.assertAlmostEqual(angle, 90.0, places=1)

    def test_acute_angle_45_degrees(self):
        """Points forming a 45 degree angle."""
        hip = (0.0, 0.0)
        knee = (0.0, 1.0)
        ankle = (1.0, 0.0)
        angle = PoseEstimator.calculate_angle(hip, knee, ankle)
        self.assertAlmostEqual(angle, 45.0, places=1)

    def test_obtuse_angle_135_degrees(self):
        """Points forming a 135 degree angle (e.g. partial knee bend)."""
        hip = (0.0, 0.0)
        knee = (0.0, 1.0)
        ankle = (1.0, 2.0)
        angle = PoseEstimator.calculate_angle(hip, knee, ankle)
        self.assertAlmostEqual(angle, 135.0, places=1)

    def test_zero_vector_degenerate_case(self):
        """Coincident points should gracefully return 0.0 without divide-by-zero exception."""
        hip = (1.0, 1.0)
        knee = (1.0, 1.0)
        ankle = (2.0, 2.0)
        angle = PoseEstimator.calculate_angle(hip, knee, ankle)
        self.assertEqual(angle, 0.0)

    def test_inverted_coordinates_order(self):
        """Angle between BA and BC must equal angle between BC and BA."""
        a = (0.2, 0.5)
        b = (0.5, 0.5)
        c = (0.5, 0.9)
        angle1 = PoseEstimator.calculate_angle(a, b, c)
        angle2 = PoseEstimator.calculate_angle(c, b, a)
        self.assertAlmostEqual(angle1, angle2, places=4)


if __name__ == "__main__":
    unittest.main()
