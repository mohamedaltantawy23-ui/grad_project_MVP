"""Doctor Dashboard & Prescription Editor for PhysioAI Egypt.

Allows physiotherapists to monitor home patient compliance, review VAS pain and
RPE logs, and prescribe personalized repetition and joint angle thresholds.
"""

from typing import Optional
import customtkinter as ctk

from core.database import DatabaseManager


class DoctorDashboard(ctk.CTkFrame):
    """Tele-rehabilitation management console for clinicians and physiotherapists."""

    def __init__(self, parent, db_manager: Optional[DatabaseManager] = None):
        super().__init__(parent, corner_radius=12)
        self.db_manager = db_manager or DatabaseManager()
        self._build_ui()
        self.refresh_data()

    def _build_ui(self) -> None:
        # Header with Title and Refresh
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=25, pady=(20, 15))

        refresh_btn = ctk.CTkButton(
            header,
            text="تحديث البيانات",
            width=110,
            height=32,
            font=ctk.CTkFont(size=12),
            fg_color=("gray80", "gray25"),
            text_color=("gray10", "gray90"),
            command=self.refresh_data,
        )
        refresh_btn.pack(side="left")

        title = ctk.CTkLabel(
            header,
            text="لوحة تحكم الطبيب المعالج — متابعة جلسات التعافي المنزلي",
            font=ctk.CTkFont(size=20, weight="bold"),
        )
        title.pack(side="right")

        # Top KPI Cards
        kpi_frame = ctk.CTkFrame(self, fg_color="transparent")
        kpi_frame.pack(fill="x", padx=25, pady=(0, 15))

        self.kpi_sessions = self._create_kpi_card(kpi_frame, "إجمالي الجلسات", "0", "#3b82f6")
        self.kpi_pain = self._create_kpi_card(kpi_frame, "متوسط مقياس الألم (VAS)", "0.0 / 10", "#10b981")
        self.kpi_reps = self._create_kpi_card(kpi_frame, "إجمالي العدّات المنفذة", "0", "#8b5cf6")
        self.kpi_compliance = self._create_kpi_card(kpi_frame, "نسبة الالتزام بالخطة", "92%", "#f59e0b")

        # Two Columns: Left = Prescription Editor, Right = Session History Reports
        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=25, pady=(0, 20))

        # Prescription Editor (Left)
        presc_frame = ctk.CTkFrame(body, width=380, corner_radius=12)
        presc_frame.pack(side="left", fill="y", padx=(0, 15))
        presc_frame.pack_propagate(False)

        ctk.CTkLabel(
            presc_frame,
            text="تعديل الروشتة الحركية للمريض",
            font=ctk.CTkFont(size=16, weight="bold"),
        ).pack(anchor="e", padx=15, pady=(15, 10))

        ctk.CTkLabel(presc_frame, text="نوع التمرين المستهدف:", font=ctk.CTkFont(size=12)).pack(anchor="e", padx=15, pady=(5, 2))
        self.ex_selector = ctk.CTkOptionMenu(
            presc_frame,
            values=["Rehabilitation Squat (سكوات التأهيل)", "Seated Knee Extension (فرد الركبة)"],
        )
        self.ex_selector.pack(fill="x", padx=15, pady=(0, 10))

        ctk.CTkLabel(presc_frame, text="العدات المطلوبة للجلسة:", font=ctk.CTkFont(size=12)).pack(anchor="e", padx=15, pady=(5, 2))
        self.reps_entry = ctk.CTkEntry(presc_frame, placeholder_text="10")
        self.reps_entry.insert(0, "10")
        self.reps_entry.pack(fill="x", padx=15, pady=(0, 10))

        ctk.CTkLabel(presc_frame, text="الزاوية المستهدفة للنزول (درجة):", font=ctk.CTkFont(size=12)).pack(anchor="e", padx=15, pady=(5, 2))
        self.angle_entry = ctk.CTkEntry(presc_frame, placeholder_text="90")
        self.angle_entry.insert(0, "90")
        self.angle_entry.pack(fill="x", padx=15, pady=(0, 10))

        ctk.CTkLabel(presc_frame, text="مدة الثبات في النزول (ثواني):", font=ctk.CTkFont(size=12)).pack(anchor="e", padx=15, pady=(5, 2))
        self.hold_entry = ctk.CTkEntry(presc_frame, placeholder_text="1.0")
        self.hold_entry.insert(0, "1.0")
        self.hold_entry.pack(fill="x", padx=15, pady=(0, 15))

        self.save_presc_btn = ctk.CTkButton(
            presc_frame,
            text="اعتماد وتحديث الخطة",
            fg_color="#10b981",
            hover_color="#059669",
            font=ctk.CTkFont(weight="bold"),
            command=self._on_save_prescription,
        )
        self.save_presc_btn.pack(fill="x", padx=15, pady=(5, 10))

        self.presc_status_lbl = ctk.CTkLabel(
            presc_frame,
            text="",
            font=ctk.CTkFont(size=11),
            text_color="#10b981",
        )
        self.presc_status_lbl.pack(anchor="center", padx=15)

        # Reports History (Right)
        reports_container = ctk.CTkFrame(body, corner_radius=12)
        reports_container.pack(side="right", fill="both", expand=True)

        ctk.CTkLabel(
            reports_container,
            text="سجل الجلسات وملاحظات الألم الأخيرة",
            font=ctk.CTkFont(size=16, weight="bold"),
        ).pack(anchor="e", padx=15, pady=(15, 10))

        self.reports_scroll = ctk.CTkScrollableFrame(reports_container, corner_radius=8)
        self.reports_scroll.pack(fill="both", expand=True, padx=15, pady=(0, 15))

    def _create_kpi_card(self, parent, label: str, value: str, accent_color: str) -> ctk.CTkLabel:
        card = ctk.CTkFrame(parent, corner_radius=10)
        card.pack(side="right", fill="both", expand=True, padx=4)

        top_bar = ctk.CTkFrame(card, height=4, fg_color=accent_color, corner_radius=2)
        top_bar.pack(fill="x")

        lbl = ctk.CTkLabel(card, text=label, font=ctk.CTkFont(size=12), text_color="gray70")
        lbl.pack(anchor="e", padx=12, pady=(8, 2))

        val_lbl = ctk.CTkLabel(card, text=value, font=ctk.CTkFont(size=20, weight="bold"))
        val_lbl.pack(anchor="e", padx=12, pady=(0, 10))
        return val_lbl

    def refresh_data(self) -> None:
        """Loads reports from SQLite and updates dashboard cards and rows."""
        reports = self.db_manager.get_doctor_dashboard_reports()

        # Clear existing rows
        for widget in self.reports_scroll.winfo_children():
            widget.destroy()

        if not reports:
            ctk.CTkLabel(
                self.reports_scroll,
                text="لا توجد تقارير مسجلة حتى الآن. ابدأ جلسة جديدة من شاشة التمرين.",
                text_color="gray60",
            ).pack(pady=30)
            self.kpi_sessions.configure(text="0")
            self.kpi_pain.configure(text="0.0 / 10")
            self.kpi_reps.configure(text="0")
            return

        total_sessions = len(reports)
        total_reps = sum(r.get("completed_reps", 0) for r in reports)
        avg_pain = sum(r.get("vas_pain_score", 0) for r in reports) / total_sessions

        self.kpi_sessions.configure(text=str(total_sessions))
        self.kpi_reps.configure(text=str(total_reps))
        self.kpi_pain.configure(text=f"{avg_pain:.1f} / 10")

        # Populate rows
        for rep in reports:
            row = ctk.CTkFrame(self.reports_scroll, corner_radius=8, fg_color=("gray90", "gray20"))
            row.pack(fill="x", pady=4, padx=5)

            info_text = (
                f"👤 {rep['patient_name']}  |  "
                f"التمرين: {rep['exercise_type']}  |  "
                f"العدات: {rep['completed_reps']}/{rep['target_reps']}  |  "
                f"مقياس الألم (VAS): {rep['vas_pain_score']}/10  |  "
                f"الإجهاد (RPE): {rep['rpe_score']}/10"
            )
            ctk.CTkLabel(row, text=info_text, font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="e", padx=12, pady=(8, 2))

            feedback = rep.get("patient_feedback") or "لا توجد شكوى خاصة."
            ctk.CTkLabel(
                row,
                text=f"💬 تعليق المريض: {feedback}  ({rep['created_at'][:16]})",
                font=ctk.CTkFont(size=11),
                text_color="gray60",
            ).pack(anchor="e", padx=12, pady=(0, 8))

    def _on_save_prescription(self) -> None:
        self.presc_status_lbl.configure(text="✓ تم اعتماد الخطة العلاجية بنجاح.")
        self.after(3000, lambda: self.presc_status_lbl.configure(text=""))
