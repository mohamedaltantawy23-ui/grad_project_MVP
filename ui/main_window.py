"""Main Window Shell with Navigation Sidebar and Canvas Views for PhysioAI Egypt."""

from typing import Dict
import customtkinter as ctk

from config import (
    APP_NAME,
    APP_TITLE,
    APP_VERSION,
    GEMINI_API_KEY,
    WINDOW_HEIGHT,
    WINDOW_WIDTH,
)
from core.chat_engine import PhysioChatEngine
from core.database import DatabaseManager
from core.voice_agent import GeminiLiveVoiceAgent
from ui.camera_view import CameraView
from ui.chat_view import ChatView
from ui.doctor_dashboard import DoctorDashboard


class MainWindow(ctk.CTk):
    """Main desktop application window hosting the navigation sidebar and views."""

    def __init__(self):
        super().__init__()

        self.title(APP_TITLE)
        self.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.minsize(980, 650)

        # Theme settings
        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")

        # Core subsystems
        self.db_manager = DatabaseManager()
        self.voice_agent = GeminiLiveVoiceAgent()
        self.chat_engine = PhysioChatEngine()

        self.views: Dict[str, ctk.CTkFrame] = {}
        self.active_view_name = "exercise"

        self._build_layout()
        self._show_view("exercise")

    def _build_layout(self) -> None:
        # Navigation Sidebar (Left in LTR, Right for Arabic feel)
        self.sidebar = ctk.CTkFrame(self, width=240, corner_radius=0)
        self.sidebar.pack(side="right", fill="y")
        self.sidebar.pack_propagate(False)

        # App Logo & Branding in Sidebar
        logo_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        logo_frame.pack(fill="x", padx=15, pady=(25, 20))

        ctk.CTkLabel(
            logo_frame,
            text=f"🏥 {APP_NAME}",
            font=ctk.CTkFont(size=20, weight="bold"),
        ).pack(anchor="e")

        ctk.CTkLabel(
            logo_frame,
            text="مساعد التأهيل الحركي الذكي",
            font=ctk.CTkFont(size=12),
            text_color="gray70",
        ).pack(anchor="e", pady=(2, 0))

        # Nav Buttons Container
        nav_container = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        nav_container.pack(fill="x", padx=15, pady=10)

        self.nav_btns = {}
        items = [
            ("exercise", "🎥  تمرين الكاميرا"),
            ("chat", "💬  شات فيزيو الطبي"),
            ("dashboard", "🩺  لوحة تحكم الطبيب"),
        ]

        for key, label in items:
            btn = ctk.CTkButton(
                nav_container,
                text=label,
                font=ctk.CTkFont(size=14, weight="bold"),
                height=42,
                corner_radius=8,
                fg_color="transparent",
                text_color=("gray20", "gray85"),
                hover_color=("gray80", "gray25"),
                anchor="e",
                command=lambda k=key: self._show_view(k),
            )
            btn.pack(fill="x", pady=4)
            self.nav_btns[key] = btn

        # Sidebar Bottom Patient Profile & Status
        bottom_profile = ctk.CTkFrame(self.sidebar, corner_radius=10, fg_color=("gray85", "gray20"))
        bottom_profile.pack(side="bottom", fill="x", padx=15, pady=20)

        ctk.CTkLabel(
            bottom_profile,
            text="👤 المريض الحالي:",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="gray60",
        ).pack(anchor="e", padx=12, pady=(10, 2))

        ctk.CTkLabel(
            bottom_profile,
            text="أحمد محمود (تأهيل ركبة)",
            font=ctk.CTkFont(size=12, weight="bold"),
        ).pack(anchor="e", padx=12, pady=(0, 4))

        api_status = "✓ جيميناي متصل" if GEMINI_API_KEY else "⚠️ وضع أوفلاين (بلا API Key)"
        status_color = "#10b981" if GEMINI_API_KEY else "#f59e0b"
        ctk.CTkLabel(
            bottom_profile,
            text=api_status,
            font=ctk.CTkFont(size=10),
            text_color=status_color,
        ).pack(anchor="e", padx=12, pady=(0, 10))

        # Main Viewport Container
        self.viewport = ctk.CTkFrame(self, corner_radius=0, fg_color=("gray95", "gray10"))
        self.viewport.pack(side="left", fill="both", expand=True)

        # Initialize View Instances
        self.views["exercise"] = CameraView(self.viewport, db_manager=self.db_manager, voice_agent=self.voice_agent)
        self.views["chat"] = ChatView(self.viewport, chat_engine=self.chat_engine)
        self.views["dashboard"] = DoctorDashboard(self.viewport, db_manager=self.db_manager)

    def _show_view(self, view_name: str) -> None:
        """Switches active view and highlights sidebar button."""
        if view_name not in self.views:
            return

        # Hide current views
        for v in self.views.values():
            v.pack_forget()

        # Update sidebar styling
        for k, btn in self.nav_btns.items():
            if k == view_name:
                btn.configure(fg_color=("#3b82f6", "#2563eb"), text_color="white")
            else:
                btn.configure(fg_color="transparent", text_color=("gray20", "gray85"))

        # Display selected view
        self.views[view_name].pack(fill="both", expand=True)
        self.active_view_name = view_name
