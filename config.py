"""PhysioAI Egypt - Configuration & Environment Constants.

Handles safe loading of API keys, model parameters, database paths,
and Arabic clinical prompts for both text and voice agents.
"""

from pathlib import Path
import os

# Base Directories
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
ASSETS_DIR = BASE_DIR / "assets"
ICONS_DIR = ASSETS_DIR / "icons"
AUDIO_DIR = ASSETS_DIR / "audio"

# Ensure runtime directories exist
DATA_DIR.mkdir(parents=True, exist_ok=True)
ICONS_DIR.mkdir(parents=True, exist_ok=True)
AUDIO_DIR.mkdir(parents=True, exist_ok=True)

# Safe .env loader (without requiring python-dotenv as strict dependency)
def _load_env_file():
    env_path = BASE_DIR / ".env"
    if env_path.is_file():
        try:
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        os.environ.setdefault(k.strip(), v.strip().strip("'\""))
        except Exception:
            pass

_load_env_file()

# API Keys & Secrets (Must NOT be hardcoded)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# AI Model Constants
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
GEMINI_LIVE_MODEL = os.getenv("GEMINI_LIVE_MODEL", "gemini-2.0-flash-exp")
GEMINI_LIVE_URI = "wss://generativelanguage.googleapis.com/ws/google.ai.generativelanguage.v1alpha.GenerativeService.BidiGenerateContent"

# Local Storage Database
DB_PATH = DATA_DIR / "physio_ai.db"

# Application Metadata & UI Settings
APP_NAME = "PhysioAI Egypt"
APP_TITLE = "PhysioAI Egypt — مساعد العلاج الطبيعي والتأهيل الحركي الذكي"
APP_VERSION = "1.0.0"
WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 800

# Audio Capture Parameters
AUDIO_SAMPLE_RATE = 16000
AUDIO_CHANNELS = 1
AUDIO_CHUNK_SIZE = 1024

# Camera & Vision Parameters
DEFAULT_CAMERA_INDEX = 0
TARGET_FPS = 30
CONFIDENCE_THRESHOLD = 0.65

# System Prompts (Egyptian Arabic Dialect & Clinical Boundaries)
VOICE_AGENT_SYSTEM_PROMPT = """
أنت 'فيزيو-إيه آي' (PhysioAI)، كوتش وأخصائي تأهيل حركي مصري ذكي وودود جداً.
مهمتك: توجيه ومرافقة المريض المصري أثناء أداء تمارين العلاج الطبيعي المنزلية في أيام التعافي غير المخصصة للعيادة.
اللهجة: اللهجة المصرية البيضاء المحبوبة والواضحة (زي: 'عاش يا بطل'، 'افرد ركبتك بالراحة'، 'ممتاز كمل على كده'، 'ريح ثانية وخد نَفَس').
قواعد السلامة الطبية الصارمة:
1. لو المريض اشتكى من وجع شديد أو دوخة أو إرهاق ('بيوجعني'، 'مش قادر'، 'تعبان')، أمره فوراً وبحزم يوقف التمرين ويستريح، واقترح عليه يبلغ دكتوره.
2. خلي كلامك تشجيعي ومختصر جداً ومباشر عشان المريض بيتحرك ومش فاضي يسمع كلام طويل.
3. التزم بتوجيهات زوايا المفاصل وعدد العدات وماتألفش أي تشخيصات طبية خارج التمرين.
""".strip()

CHATBOT_SYSTEM_PROMPT = """
أنت 'PhysioAI Chatbot'، المساعد الطبي المتخصص حصرياً في استشارات العلاج الطبيعي وإعادة التأهيل الحركي.
النطاق والحدود:
- أجب فقط على الأسئلة المتعلقة بتمارين العلاج الطبيعي، آليات الحركة، الاستشفاء العضلي، تحسين القوام، وتسكين آلام العضلات والمفاصل البسيطة.
- إذا سألك المستخدم عن أي موضوع خارج العلاج الطبيعي (مثل الأمراض الباطنية، الجراحة، الأدوية، أو أي موضوع عام)، اعتذر بلطف ووجهه للتخصص المناسب.
- قدم نصائح آمنة وتحفظية، واختم النصائح الهامة دائماً بتذكير المريض باستشارة طبيبه المعالج.
- تحدث بلغة عربية تجمع بين الدقة والمفردات المصرية الدارجة السهلة.
""".strip()
