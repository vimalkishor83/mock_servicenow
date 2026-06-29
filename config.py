import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent

HOST = os.getenv("HOST", "127.0.0.1")
PORT = int(os.getenv("PORT", "8080"))

DB_CONNECTION_STRING = os.getenv(
    "DB_CONNECTION_STRING",
    f"sqlite:///{BASE_DIR / 'database' / 'mock_snow.db'}",
)

ENABLE_AUTH = os.getenv("ENABLE_AUTH", "true").lower() == "true"
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "change-this-secret-for-non-local-use")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRATION_MINUTES = int(os.getenv("JWT_EXPIRATION_MINUTES", "60"))

DEFAULT_ADMIN_USERNAME = os.getenv("DEFAULT_ADMIN_USERNAME", "admin")
DEFAULT_ADMIN_PASSWORD = os.getenv("DEFAULT_ADMIN_PASSWORD", "admin123")

AUTO_SEED_DUMMY_DATA = os.getenv("AUTO_SEED_DUMMY_DATA", "true").lower() == "true"
DUMMY_USER_COUNT = int(os.getenv("DUMMY_USER_COUNT", "100"))
DUMMY_GROUP_COUNT = int(os.getenv("DUMMY_GROUP_COUNT", "10"))
DUMMY_INCIDENT_COUNT = int(os.getenv("DUMMY_INCIDENT_COUNT", "5000"))

ENABLE_SCHEDULER = os.getenv("ENABLE_SCHEDULER", "true").lower() == "true"
SCHEDULER_INTERVAL_SECONDS = int(os.getenv("SCHEDULER_INTERVAL_SECONDS", "300"))
SCHEDULER_INCIDENTS_PER_RUN = int(os.getenv("SCHEDULER_INCIDENTS_PER_RUN", "3"))

LOG_FILE = os.getenv("LOG_FILE", str(BASE_DIR / "logs" / "application.log"))

SQLALCHEMY_DATABASE_URI = DB_CONNECTION_STRING
SQLALCHEMY_TRACK_MODIFICATIONS = False
JSON_SORT_KEYS = False
