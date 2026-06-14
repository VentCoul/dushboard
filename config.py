"""Читання конфігу з .env. Усі налаштування дашборда — в одному місці."""
import os
from dotenv import load_dotenv

load_dotenv()

# Базова директорія проєкту (щоб відносні шляхи працювали з будь-якого CWD)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def _path(value: str) -> str:
    """Відносний шлях рахуємо від BASE_DIR, абсолютний лишаємо як є."""
    return value if os.path.isabs(value) else os.path.join(BASE_DIR, value)


# --- Auth ---
DASHBOARD_PASSWORD = os.environ.get("DASHBOARD_PASSWORD", "change-me")
SECRET_KEY = os.environ.get("SECRET_KEY", "dev-insecure-secret")

# --- База ---
DB_PATH = _path("data/dushboard.db")

# --- Obsidian ---
VAULT_PATH = _path(os.environ.get("VAULT_PATH", "data/vault"))
VAULT_PROJECTS_DIR = os.environ.get("VAULT_PROJECTS_DIR", "Projects")
VAULT_GIT_ENABLED = os.environ.get("VAULT_GIT_ENABLED", "0") == "1"

# --- Погода ---
WEATHER_LAT = float(os.environ.get("WEATHER_LAT", "50.45"))
WEATHER_LON = float(os.environ.get("WEATHER_LON", "30.52"))
WEATHER_CITY = os.environ.get("WEATHER_CITY", "Kyiv")

# --- Крипта ---
CRYPTO_IDS = [s.strip() for s in os.environ.get("CRYPTO_IDS", "bitcoin,ethereum").split(",") if s.strip()]

# --- GitHub ---
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
GITHUB_USER = os.environ.get("GITHUB_USER", "")

# --- Календар / пошта ---
ICAL_URL = os.environ.get("ICAL_URL", "")
IMAP_HOST = os.environ.get("IMAP_HOST", "imap.gmail.com")
IMAP_USER = os.environ.get("IMAP_USER", "")
IMAP_PASSWORD = os.environ.get("IMAP_PASSWORD", "")

# --- Боти ---
BOT_SERVICES = [s.strip() for s in os.environ.get("BOT_SERVICES", "").split(",") if s.strip()]

# --- Job-hunter бот (зовнішня БД для імпорту вакансій) ---
# На VPS: /root/job-hunter/data/jobs.db  (або де фактично лежить)
JOB_HUNTER_DB = os.environ.get("JOB_HUNTER_DB", "")
