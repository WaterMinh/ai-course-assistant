import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "mysql+pymysql://root:rootpassword@127.0.0.1:3307/ai_course_assistant"
)

LM_STUDIO_URL = os.getenv("LM_STUDIO_URL", "http://localhost:1234/v1")
LM_STUDIO_MODEL = os.getenv("LM_STUDIO_MODEL", "google/gemma-4-e2b")
SECRET_KEY = os.getenv("SECRET_KEY", "change-this-secret")
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "uploads")
