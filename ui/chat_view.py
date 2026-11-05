"""Dedicated Physiotherapy Q&A Consultation Chat Interface for PhysioAI Egypt."""

import threading
from typing import Optional
import customtkinter as ctk

from core.chat_engine import PhysioChatEngine


class ChatView(ctk.CTkFrame):
    """Physiotherapy-constrained chatbot consultation view with message history and quick suggestion chips."""

    SUGGESTIONS = [
        "هل طبيعي أحس بشد عضلي بعد التمرين؟",
        "إزاي أظبط وضعية ركبتي في السكوات؟",
        "إمتى لازم أوقف التمرين فوراً وأستريح؟",
        "كم ثانية يفضل أثبت فيها في نهاية الحركة؟",
    ]

    def __init__(self, parent, chat_engine: Optional[PhysioChatEngine] = None):
        super().__init__(parent, corner_radius=12)
        self.chat_engine = chat_engine or PhysioChatEngine()
        self._build_ui()

    def _build_ui(self) -> None:
        # Header Info Banner
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=25, pady=(20, 10))

        title = ctk.CTkLabel(
            header,
            text="المساعد الطبي الذكي — استشارات العلاج الطبيعي والتأهيل",
            font=ctk.CTkFont(size=20, weight="bold"),
        )
        title.pack(anchor="e")

        desc = ctk.CTkLabel(
            header,
            text="اسأل عن وضعيات التمارين، آليات الاستشفاء الحركي، وتسكين إجهاد المفاصل والعضلات.",
            font=ctk.CTkFont(size=12),
            text_color="gray70",
        )
        desc.pack(anchor="e", pady=(2, 0))

        # Quick Suggestions Strip
        sugg_frame = ctk.CTkFrame(self, fg_color="transparent")
        sugg_frame.pack(fill="x", padx=25, pady=(0, 10))

        for text in self.SUGGESTIONS:
            btn = ctk.CTkButton(
                sugg_frame,
                text=text,
                font=ctk.CTkFont(size=11),
                height=28,
                fg_color=("gray85", "gray25"),
                text_color=("gray10", "gray90"),
                hover_color=("gray75", "gray35"),
                corner_radius=14,
                command=lambda t=text: self._send_suggestion(t),
            )
            btn.pack(side="right", padx=(5, 0))

        # Scrollable Conversation Area
        self.chat_scroll = ctk.CTkScrollableFrame(self, corner_radius=10)
        self.chat_scroll.pack(fill="both", expand=True, padx=25, pady=(0, 15))

        # Welcome Message from Bot
        self._add_message(
            "أهلاً بك يا بطل! أنا فيزيو، مساعدك الذكي للتأهيل الحركي. "
            "تقدر تسألني عن أي حاجة تخص تمرينك أو حركات المفاصل، وأنا معاك خطوة بخطوة.",
            is_user=False,
        )

        # Input & Control Bottom Bar
        input_bar = ctk.CTkFrame(self, fg_color="transparent")
        input_bar.pack(fill="x", padx=25, pady=(0, 20))

        self.send_btn = ctk.CTkButton(
            input_bar,
            text="إرسال",
            width=100,
            height=42,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#3b82f6",
            hover_color="#2563eb",
            command=self._on_send,
        )
        self.send_btn.pack(side="left")

        self.input_entry = ctk.CTkEntry(
            input_bar,
            placeholder_text="اكتب استفسارك هنا واضغط Enter...",
            height=42,
            font=ctk.CTkFont(size=13),
        )
        self.input_entry.pack(side="right", fill="x", expand=True, padx=(10, 0))
        self.input_entry.bind("<Return>", lambda _e: self._on_send())

    def _send_suggestion(self, prompt: str) -> None:
        self.input_entry.delete(0, "end")
        self.input_entry.insert(0, prompt)
        self._on_send()

    def _on_send(self) -> None:
        question = self.input_entry.get().strip()
        if not question:
            return

        self.input_entry.delete(0, "end")
        self._add_message(question, is_user=True)

        # Disable send while generating
        self.send_btn.configure(state="disabled", text="جارِ الرد...")

        def _worker():
            reply = self.chat_engine.ask(question)
            self.after(0, lambda: self._on_reply_received(reply))

        threading.Thread(target=_worker, daemon=True).start()

    def _on_reply_received(self, reply: str) -> None:
        self._add_message(reply, is_user=False)
        self.send_btn.configure(state="normal", text="إرسال")

    def _add_message(self, message: str, is_user: bool) -> None:
        bubble_row = ctk.CTkFrame(self.chat_scroll, fg_color="transparent")
        bubble_row.pack(fill="x", pady=6)

        bubble_color = ("#e0e7ff", "#1e3a8a") if is_user else ("#f3f4f6", "#1f2937")
        text_color = ("#1e1b4b", "#eff6ff") if is_user else ("#111827", "#f9fafb")
        anchor = "w" if is_user else "e"

        bubble = ctk.CTkFrame(bubble_row, fg_color=bubble_color, corner_radius=12)
        bubble.pack(anchor=anchor, padx=10)

        sender_tag = "أنت" if is_user else "كوتش فيزيو (PhysioAI)"
        tag_lbl = ctk.CTkLabel(
            bubble,
            text=sender_tag,
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color="gray50",
        )
        tag_lbl.pack(anchor="e", padx=14, pady=(6, 2))

        msg_lbl = ctk.CTkLabel(
            bubble,
            text=message,
            font=ctk.CTkFont(size=13),
            text_color=text_color,
            wraplength=620,
            justify="right",
        )
        msg_lbl.pack(anchor="e", padx=14, pady=(0, 8))
