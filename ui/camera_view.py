"""Camera View with Real-time Pose Tracking and HUD Metrics for PhysioAI Egypt."""

import threading
import time
from typing import Callable, Optional
import customtkinter as ctk
import cv2
import numpy as np
from PIL import Image, ImageTk

from core.database import DatabaseManager
from core.vision_engine import PoseEstimator
from core.voice_agent import GeminiLiveVoiceAgent
from ui.survey_dialog import SurveyDialog


class CameraView(ctk.CTkFrame):
    """Interactive rehabilitation canvas featuring OpenCV live feed, MediaPipe skeleton, and real-time HUD."""

    def __init__(
        self,
        parent,
        db_manager: Optional[DatabaseManager] = None,
        voice_agent: Optional[GeminiLiveVoiceAgent] = None,
    ):
        super().__init__(parent, corner_radius=12)
        self.db_manager = db_manager or DatabaseManager()
        self.voice_agent = voice_agent
        self.pose_estimator = PoseEstimator()

        self.cap = None
        self.is_running = False
        self.active_workout_id: Optional[int] = None
        self.target_reps = 10
        self.start_time = 0.0

        self._build_ui()

    def _build_ui(self) -> None:
        # Top Header Bar
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(15, 10))

        self.phase_badge = ctk.CTkLabel(
            header,
            text="حالة الحركة: في الانتظار",
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color=("gray85", "gray25"),
            corner_radius=8,
            padx=12,
            pady=4,
        )
        self.phase_badge.pack(side="left")

        title = ctk.CTkLabel(
            header,
            text="تمرين القرفصاء التأهيلي — Rehabilitation Squat",
            font=ctk.CTkFont(size=18, weight="bold"),
        )
        title.pack(side="right")

        # Main Workspace: Left = Video Canvas, Right = Metrics HUD
        content = ctk.CTkFrame(self, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=20, pady=(0, 10))

        # Video Canvas (Left)
        video_box = ctk.CTkFrame(content, corner_radius=10, fg_color="black")
        video_box.pack(side="left", fill="both", expand=True, padx=(0, 15))

        self.canvas_label = ctk.CTkLabel(video_box, text="الكاميرا مغلقة حالياً\nاضغط 'بدء تشغيل الكاميرا' للبدء", text_color="gray60")
        self.canvas_label.pack(fill="both", expand=True)

        # Metrics HUD (Right)
        hud_box = ctk.CTkFrame(content, width=320, corner_radius=12)
        hud_box.pack(side="right", fill="y")
        hud_box.pack_propagate(False)

        # Rep Counter Big Display
        rep_card = ctk.CTkFrame(hud_box, corner_radius=10, fg_color=("#e0e7ff", "#1e3a8a"))
        rep_card.pack(fill="x", padx=15, pady=(15, 10))

        ctk.CTkLabel(
            rep_card,
            text="العدّات المكتملة",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=("gray30", "gray80"),
        ).pack(pady=(10, 0))

        self.rep_count_lbl = ctk.CTkLabel(
            rep_card,
            text="0 / 10",
            font=ctk.CTkFont(size=36, weight="bold"),
            text_color=("#1e1b4b", "#ffffff"),
        )
        self.rep_count_lbl.pack(pady=(0, 10))

        # Joint Angle Gauge Card
        angle_card = ctk.CTkFrame(hud_box, corner_radius=10)
        angle_card.pack(fill="x", padx=15, pady=(0, 10))

        ctk.CTkLabel(
            angle_card,
            text="زاوية مفصل الركبة الحالية",
            font=ctk.CTkFont(size=12),
            text_color="gray70",
        ).pack(anchor="e", padx=12, pady=(10, 2))

        self.angle_lbl = ctk.CTkLabel(
            angle_card,
            text="180° (فرد كامل)",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color="#10b981",
        )
        self.angle_lbl.pack(anchor="e", padx=12, pady=(0, 10))

        # Real-time Voice Coach Guidance Bubble
        coach_card = ctk.CTkFrame(hud_box, corner_radius=10, fg_color=("#fef3c7", "#451a03"))
        coach_card.pack(fill="x", padx=15, pady=(0, 10))

        ctk.CTkLabel(
            coach_card,
            text="🗣️ توجيه الكوتش المصري:",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=("#92400e", "#fde68a"),
        ).pack(anchor="e", padx=12, pady=(8, 2))

        self.coach_feedback_lbl = ctk.CTkLabel(
            coach_card,
            text="عاش يا بطل! اقف مظبوط قدام الكاميرا واستعد.",
            font=ctk.CTkFont(size=13),
            text_color=("#78350f", "#fef3c7"),
            wraplength=280,
            justify="right",
        )
        self.coach_feedback_lbl.pack(anchor="e", padx=12, pady=(0, 10))

        # Safety Alert Banner (Hidden by default)
        self.safety_banner = ctk.CTkFrame(hud_box, corner_radius=8, fg_color="#ef4444")
        self.safety_lbl = ctk.CTkLabel(
            self.safety_banner,
            text="⚠️ تم إيقاف التمرين لسلامتك!",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="white",
        )
        self.safety_lbl.pack(padx=10, pady=8)

        # Bottom Control Buttons
        ctrl_frame = ctk.CTkFrame(hud_box, fg_color="transparent")
        ctrl_frame.pack(fill="x", padx=15, pady=(15, 15), side="bottom")

        self.start_btn = ctk.CTkButton(
            ctrl_frame,
            text="بدء تشغيل الكاميرا",
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#10b981",
            hover_color="#059669",
            height=38,
            command=self._toggle_camera,
        )
        self.start_btn.pack(fill="x", pady=(0, 8))

        self.finish_btn = ctk.CTkButton(
            ctrl_frame,
            text="إنهاء الجلسة وتسجيل الاستبيان",
            font=ctk.CTkFont(size=13),
            fg_color="#3b82f6",
            hover_color="#2563eb",
            height=36,
            command=self._finish_workout_and_survey,
        )
        self.finish_btn.pack(fill="x")

    def _toggle_camera(self) -> None:
        if not self.is_running:
            self._start_camera()
        else:
            self._stop_camera()

    def _start_camera(self) -> None:
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            self.canvas_label.configure(text="تعذر فتح الكاميرا!\nيرجى التأكد من توصيل كاميرا الويب وتصريح الوصول.")
            return

        self.is_running = True
        self.start_time = time.time()
        self.start_btn.configure(text="إيقاف مؤقت", fg_color="#ef4444", hover_color="#dc2626")
        self.safety_banner.pack_forget()

        # Start thread
        self.worker_thread = threading.Thread(target=self._capture_loop, daemon=True)
        self.worker_thread.start()

    def _stop_camera(self) -> None:
        self.is_running = False
        if self.cap:
            self.cap.release()
            self.cap = None
        self.start_btn.configure(text="استئناف الكاميرا", fg_color="#10b981", hover_color="#059669")
        self.canvas_label.configure(text="الكاميرا متوقفة مؤقتاً")

    def _capture_loop(self) -> None:
        while self.is_running and self.cap and self.cap.isOpened():
            ret, frame = self.cap.read()
            if not ret:
                break

            # Mirror frame horizontally for intuitive tele-rehab mirror view
            frame = cv2.flip(frame, 1)

            # MediaPipe Pose tracking
            landmarks = self.pose_estimator.extract_landmarks(frame)
            metrics = self.pose_estimator.update_squat_rep(landmarks)

            # Draw skeleton
            frame = self.pose_estimator.draw_skeleton(frame, landmarks)

            # Convert to PIL Image for CustomTkinter
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, _ = rgb.shape
            # Target display resolution maintaining aspect ratio
            disp_w = 640
            disp_h = int(h * (disp_w / w))
            resized = cv2.resize(rgb, (disp_w, disp_h))
            img = Image.fromarray(resized)
            ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(disp_w, disp_h))

            # Dispatch UI update to main thread
            self.after(0, lambda m=metrics, ci=ctk_img: self._update_hud(m, ci))

            time.sleep(0.03)

    def _update_hud(self, metrics: dict, ctk_img: ctk.CTkImage) -> None:
        if not self.is_running:
            return

        self.canvas_label.configure(image=ctk_img, text="")
        self.canvas_label.image = ctk_img

        reps = metrics.get("reps", 0)
        angle = metrics.get("knee_angle", 180.0)
        phase = metrics.get("phase", "ready")
        feedback = metrics.get("feedback", "")

        self.rep_count_lbl.configure(text=f"{reps} / {self.target_reps}")
        self.angle_lbl.configure(text=f"{int(angle)}°")
        self.phase_badge.configure(text=f"حالة الحركة: {phase}")
        self.coach_feedback_lbl.configure(text=feedback)

    def _finish_workout_and_survey(self) -> None:
        """Stops workout capture, logs workout to SQLite, and launches post-session survey dialog."""
        self._stop_camera()
        duration = time.time() - self.start_time if self.start_time else 0.0

        # Log workout record to database
        workout_id = self.db_manager.log_workout(
            patient_id=1,
            exercise_type="Rehabilitation Squat",
            target_reps=self.target_reps,
            completed_reps=self.pose_estimator.rep_count,
            duration_seconds=round(duration, 1),
            avg_knee_angle=self.pose_estimator.current_knee_angle,
        )

        def _on_survey_submitted(vas: int, rpe: int, feedback: str):
            self.db_manager.log_session_report(
                workout_id=workout_id,
                patient_id=1,
                vas_pain_score=vas,
                rpe_score=rpe,
                patient_feedback=feedback,
            )
            # Reset exercise state
            self.pose_estimator.reset()
            self.rep_count_lbl.configure(text="0 / 10")

        # Open Survey modal
        SurveyDialog(
            parent=self.winfo_toplevel(),
            workout_id=workout_id,
            patient_id=1,
            on_submit=_on_survey_submitted,
        )
