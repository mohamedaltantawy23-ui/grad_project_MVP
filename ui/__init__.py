"""User Interface modules for PhysioAI Egypt."""

from .main_window import MainWindow
from .camera_view import CameraView
from .survey_dialog import SurveyDialog
from .doctor_dashboard import DoctorDashboard
from .chat_view import ChatView

__all__ = [
    "MainWindow",
    "CameraView",
    "SurveyDialog",
    "DoctorDashboard",
    "ChatView",
]
