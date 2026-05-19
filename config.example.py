from pathlib import Path


# =========================
# School CAS / Portal config
# =========================
CAS_LOGIN_URL = "https://auth.bupt.edu.cn/authserver/login"
NOTICE_LIST_URL = "http://my.bupt.edu.cn/list.jsp?urltype=tree.TreeTempUrl&wbtreeid=1154"
PORTAL_BASE_URL = "http://my.bupt.edu.cn"

# Fill in your credentials. Use os.getenv() in production.
SCHOOL_USERNAME = "your_student_id"
SCHOOL_PASSWORD = "your_password"


# =========================
# Runtime paths
# =========================
BASE_DIR = Path(__file__).resolve().parent
STATE_FILE = str(BASE_DIR / "auth_state.json")
DB_PATH = str(BASE_DIR / "notices.db")
LOG_DIR = str(BASE_DIR / "logs")


# =========================
# AI config: OpenAI-compatible API
# =========================
AI_API_KEY = "your_api_key"
AI_BASE_URL = "https://api.openai.com/v1"
AI_MODEL = "gpt-4o-mini"


# =========================
# OpenClaw config
# =========================
OPENCLAW_SEND_URL = "http://127.0.0.1:8000/send"


# =========================
# Playwright config
# =========================
RUN_HEADLESS = True

# BUPT CAS login selectors (iframe-based, "密码登录" tab)
USERNAME_SELECTOR = 'input[name="username"]'
PASSWORD_SELECTOR = 'input[name="password"]'
LOGIN_BUTTON_SELECTOR = 'input[type="submit"]'

# Keywords used to detect whether the current page is still the CAS login page.
CAS_KEYWORDS = ("统一身份认证", "登录", "CAS")

# Notice list fallback behavior.
NOTICE_LIST_LIMIT_WHEN_DATE_UNKNOWN = 10
