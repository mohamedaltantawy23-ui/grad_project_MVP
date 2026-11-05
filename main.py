"""PhysioAI Egypt — Application Entry Point.

Validates core environment dependencies, initializes SQLite storage,
and starts the CustomTkinter rehabilitation application shell.
"""

from pathlib import Path
import os
import sys

# Ensure current package directory is in sys.path
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))


def check_dependencies() -> bool:
    """Verifies that mandatory desktop and vision packages are available."""
    missing = []
    try:
        import customtkinter
    except ImportError:
        missing.append("customtkinter")

    try:
        import cv2
    except ImportError:
        missing.append("opencv-python")

    try:
        import numpy
    except ImportError:
        missing.append("numpy")

    try:
        import PIL
    except ImportError:
        missing.append("pillow")

    if missing:
        print("\n" + "=" * 65)
        print("⚠️  تحذير: بعض المكتبات الأساسية غير مثبتة:")
        for pkg in missing:
            print(f"   - {pkg}")
        print("\nيرجى تثبيت المتطلبات عبر الأمر التالي:")
        print("   pip install -r requirements.txt")
        print("=" * 65 + "\n")
        return False
    return True


def main() -> None:
    """Application launcher."""
    print("=" * 60)
    print("🚀 بدء تشغيل PhysioAI Egypt (مساعد التأهيل الحركي الذكي)...")
    print("=" * 60)

    # Dependency verification
    deps_ok = check_dependencies()
    if not deps_ok:
        try:
            import tkinter as tk
            from tkinter import messagebox
            root = tk.Tk()
            root.withdraw()
            messagebox.showwarning(
                "PhysioAI Egypt — متطلبات ناقصة",
                "المكتبات الأساسية غير مكتملة.\nيرجى فتح الطرفية وتشغيل:\npip install -r requirements.txt",
            )
            root.destroy()
        except Exception:
            pass
        return

    # Initialize local SQLite storage
    from core.database import DatabaseManager
    db = DatabaseManager()
    db.init_db()
    print(f"✓ قاعدة البيانات جاهزة: {db.db_path}")

    # Launch UI
    from ui.main_window import MainWindow
    app = MainWindow()
    print("✓ تم فتح نافذة التطبيق بنجاح.")
    app.mainloop()


if __name__ == "__main__":
    main()
