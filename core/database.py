"""Local SQLite storage module for PhysioAI Egypt.

Manages patient profiles, rehabilitation workouts, VAS pain scores,
RPE surveys, and therapist clinical reports.
"""

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
import os
import sqlite3

from config import DB_PATH


class DatabaseManager:
    """Manages SQLite connections and queries for patient and workout data."""

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or DB_PATH
        # Ensure parent directory exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.init_db()

    def get_connection(self) -> sqlite3.Connection:
        """Returns a connection with Row factory enabled."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self) -> None:
        """Initializes tables: patients, workouts, and session_reports."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Patients Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS patients (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    age INTEGER,
                    gender TEXT,
                    condition TEXT,
                    phone TEXT,
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

            # Workouts Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS workouts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    patient_id INTEGER NOT NULL,
                    exercise_type TEXT NOT NULL,
                    target_reps INTEGER DEFAULT 10,
                    completed_reps INTEGER DEFAULT 0,
                    duration_seconds REAL DEFAULT 0.0,
                    avg_knee_angle REAL DEFAULT 0.0,
                    min_depth_angle REAL DEFAULT 180.0,
                    form_faults_count INTEGER DEFAULT 0,
                    status TEXT DEFAULT 'completed',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (patient_id) REFERENCES patients (id) ON DELETE CASCADE
                );
            """)

            # Session Reports Table (VAS Pain & RPE)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS session_reports (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    workout_id INTEGER NOT NULL,
                    patient_id INTEGER NOT NULL,
                    vas_pain_score INTEGER CHECK(vas_pain_score BETWEEN 0 AND 10),
                    rpe_score INTEGER CHECK(rpe_score BETWEEN 0 AND 10),
                    pain_location TEXT,
                    patient_feedback TEXT,
                    doctor_notes TEXT,
                    status TEXT DEFAULT 'pending_review',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (workout_id) REFERENCES workouts (id) ON DELETE CASCADE,
                    FOREIGN KEY (patient_id) REFERENCES patients (id) ON DELETE CASCADE
                );
            """)

            conn.commit()
            self._seed_default_patient_if_needed(conn)

    def _seed_default_patient_if_needed(self, conn: sqlite3.Connection) -> None:
        """Inserts a default demo patient if database is freshly created."""
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM patients")
        if cursor.fetchone()[0] == 0:
            cursor.execute("""
                INSERT INTO patients (name, age, gender, condition, notes)
                VALUES (?, ?, ?, ?, ?)
            """, ("أحمد محمود (مريض تجريبي)", 45, "ذكر", "تأهيل بعد جراحة غضروف الركبة", "مطلوب التركيز على فرد وثني الركبة بحذر"))
            conn.commit()

    # --- Patient CRUD ---
    def get_patients(self) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM patients ORDER BY id DESC")
            return [dict(row) for row in cursor.fetchall()]

    def add_patient(self, name: str, age: int, condition: str, gender: str = "غير محدد") -> int:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO patients (name, age, gender, condition)
                VALUES (?, ?, ?, ?)
            """, (name, age, gender, condition))
            conn.commit()
            return cursor.lastrowid

    # --- Workout & Session Logging ---
    def log_workout(
        self,
        patient_id: int,
        exercise_type: str,
        target_reps: int,
        completed_reps: int,
        duration_seconds: float = 0.0,
        avg_knee_angle: float = 0.0,
        min_depth_angle: float = 180.0,
        form_faults_count: int = 0,
    ) -> int:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO workouts (
                    patient_id, exercise_type, target_reps, completed_reps,
                    duration_seconds, avg_knee_angle, min_depth_angle, form_faults_count
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                patient_id, exercise_type, target_reps, completed_reps,
                duration_seconds, avg_knee_angle, min_depth_angle, form_faults_count
            ))
            conn.commit()
            return cursor.lastrowid

    def log_session_report(
        self,
        workout_id: int,
        patient_id: int,
        vas_pain_score: int,
        rpe_score: int,
        pain_location: str = "",
        patient_feedback: str = "",
        doctor_notes: str = "",
    ) -> int:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO session_reports (
                    workout_id, patient_id, vas_pain_score, rpe_score,
                    pain_location, patient_feedback, doctor_notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                workout_id, patient_id, vas_pain_score, rpe_score,
                pain_location, patient_feedback, doctor_notes
            ))
            conn.commit()
            return cursor.lastrowid

    def get_doctor_dashboard_reports(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Fetches joined workout and report records for clinical review."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    r.id AS report_id,
                    p.id AS patient_id,
                    p.name AS patient_name,
                    p.condition AS patient_condition,
                    w.exercise_type,
                    w.completed_reps,
                    w.target_reps,
                    w.avg_knee_angle,
                    r.vas_pain_score,
                    r.rpe_score,
                    r.patient_feedback,
                    r.doctor_notes,
                    r.created_at
                FROM session_reports r
                JOIN workouts w ON r.workout_id = w.id
                JOIN patients p ON r.patient_id = p.id
                ORDER BY r.created_at DESC
                LIMIT ?
            """, (limit,))
            return [dict(row) for row in cursor.fetchall()]
