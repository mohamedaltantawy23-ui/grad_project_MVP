"""Post-workout VAS Pain & RPE Survey Modal Dialog for PhysioAI Egypt.

Captures standardized Visual Analog Scale (VAS 0-10) pain scores and
Borg Rating of Perceived Exertion (RPE 0-10) to monitor recovery progression.
"""

from typing import Callable, Optional
import customtkinter as ctk


class SurveyDialog(ctk.CTkToplevel):
    """Modal dialog gathering subjective patient recovery metrics after exercise completion."""

    def __init__(
        self,
        parent,
        workout_id: int,
        patient_id: int,
        on_submit: Optional[Callable[[int, int, str], None]] = None,
    ):
        super().__init__(parent)
        self.workout_id = workout_id
        self.patient_id = patient_id
        self.on_submit = on_submit

        self.title("استبيان التقييم بعد الجلسة — VAS & RPE")
        self.geometry("540x620")
        self.resizable(False, False)

        # Make modal
        self.transient(parent)
        self.grab_set()

        self._build_ui()

    def _build_ui(self) -> None:
        # Title & Subtitle Header
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=25, pady=(20, 10))

        title_lbl = ctk.CTkLabel(
            header_frame,
            text="توثيق مستوى الألم والمجهود",
            font=ctk.CTkFont(size=20, weight="bold"),
        )
        title_lbl.pack(anchor="e")

        sub_lbl = ctk.CTkLabel(
            header_frame,
            text="إجاباتك تساعد طبيب العلاج الطبيعي على متابعة تحسنك وتعديل الخطة العلاجية.",
            font=ctk.CTkFont(size=12),
            text_color="gray70",
            wraplength=480,
            justify="right",
        )
        sub_lbl.pack(anchor="e", pady=(4, 0))

        # Main Form Container
        form_frame = ctk.CTkFrame(self, corner_radius=12)
        form_frame.pack(fill="both", expand=True, padx=25, pady=10)

        # 1. VAS Pain Scale (0-10)
        vas_header = ctk.CTkFrame(form_frame, fg_color="transparent")
        vas_header.pack(fill="x", padx=20, pady=(15, 5))
        
        ctk.CTkLabel(
            vas_header,
            text="١. مقياس شدة الألم (VAS 0–10):",
            font=ctk.CTkFont(size=14, weight="bold"),
        ).pack(side="right")

        self.vas_val_lbl = ctk.CTkLabel(
            vas_header,
            text="0 (لا يوجد ألم إطلاقاً)",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#2ecc71",
        )
        self.vas_val_lbl.pack(side="left")

        self.vas_slider = ctk.CTkSlider(
            form_frame,
            from_=0,
            to=10,
            number_of_steps=10,
            command=self._on_vas_changed,
        )
        self.vas_slider.set(0)
        self.vas_slider.pack(fill="x", padx=20, pady=(0, 15))

        # 2. RPE Exertion Scale (0-10)
        rpe_header = ctk.CTkFrame(form_frame, fg_color="transparent")
        rpe_header.pack(fill="x", padx=20, pady=(10, 5))

        ctk.CTkLabel(
            rpe_header,
            text="٢. معدل الجهد المبذول (RPE 0–10):",
            font=ctk.CTkFont(size=14, weight="bold"),
        ).pack(side="right")

        self.rpe_val_lbl = ctk.CTkLabel(
            rpe_header,
            text="3 (مجهود خفيف ومريح)",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#3498db",
        )
        self.rpe_val_lbl.pack(side="left")

        self.rpe_slider = ctk.CTkSlider(
            form_frame,
            from_=0,
            to=10,
            number_of_steps=10,
            command=self._on_rpe_changed,
        )
        self.rpe_slider.set(3)
        self.rpe_slider.pack(fill="x", padx=20, pady=(0, 15))

        # 3. Patient Feedback Notes
        ctk.CTkLabel(
            form_frame,
            text="٣. ملاحظاتك أو أي شعور غير مريح أثناء الحركة:",
            font=ctk.CTkFont(size=14, weight="bold"),
        ).pack(anchor="e", padx=20, pady=(5, 5))

        self.feedback_txt = ctk.CTkTextbox(
            form_frame,
            height=90,
            font=ctk.CTkFont(size=13),
            corner_radius=8,
        )
        self.feedback_txt.pack(fill="x", padx=20, pady=(0, 15))
        self.feedback_txt.insert("1.0", "التمرين كان جيد، لا توجد شكوى خاصة.")

        # Bottom Actions
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=25, pady=(5, 20))

        cancel_btn = ctk.CTkButton(
            btn_frame,
            text="تخطي مؤقتاً",
            fg_color="transparent",
            border_width=1,
            text_color=("gray20", "gray80"),
            command=self.destroy,
            width=120,
        )
        cancel_btn.pack(side="left")

        save_btn = ctk.CTkButton(
            btn_frame,
            text="حفظ التقرير وإرساله للدكتور",
            fg_color="#10b981",
            hover_color="#059669",
            font=ctk.CTkFont(weight="bold"),
            command=self._save_and_close,
            width=220,
        )
        save_btn.pack(side="right")

    def _on_vas_changed(self, value: float) -> None:
        score = int(round(value))
        labels = {
            0: "0 (لا يوجد ألم إطلاقاً)",
            1: "1 (ألم طفيف جداً يكاد لا يُذكر)",
            2: "2 (ألم بسيط محتمل)",
            3: "3 (ألم ملحوظ خفيف)",
            4: "4 (ألم متوسط محتمل)",
            5: "5 (ألم متوسط مزعج)",
            6: "6 (ألم متزايد يؤثر على الحركة)",
            7: "7 (ألم شديد يعيق التمرين)",
            8: "8 (ألم شديد جداً وصعب تحمله)",
            9: "9 (ألم فظيع لا يمكن تحمله)",
            10: "10 (أقصى ألم ممكن)",
        }
        color = "#2ecc71" if score <= 3 else ("#f39c12" if score <= 6 else "#e74c3c")
        self.vas_val_lbl.configure(text=labels.get(score, str(score)), text_color=color)

    def _on_rpe_changed(self, value: float) -> None:
        score = int(round(value))
        labels = {
            0: "0 (راحة تامة)",
            1: "1 (مجهود ضعيف جداً)",
            2: "2 (مجهود خفيف)",
            3: "3 (معتدل - مريح)",
            4: "4 (شديد نوعاً ما)",
            5: "5 (مجهود قوي)",
            6: "6 (شديد)",
            7: "7 (شديد جداً)",
            8: "8 (شاق وصعب)",
            9: "9 (شاق جداً وقريب من الإرهاق)",
            10: "10 (أقصى طاقة لا يمكن الزيادة)",
        }
        self.rpe_val_lbl.configure(text=labels.get(score, str(score)))

    def _save_and_close(self) -> None:
        vas = int(round(self.vas_slider.get()))
        rpe = int(round(self.rpe_slider.get()))
        feedback = self.feedback_txt.get("1.0", "end-1c").strip()
        if self.on_submit:
            self.on_submit(vas, rpe, feedback)
        self.destroy()
