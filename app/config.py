import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "mysql+pymysql://root:rootpassword@127.0.0.1:3307/ai_course_assistant"
)

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:7b")
SECRET_KEY = os.getenv("SECRET_KEY", "change-this-secret")
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "uploads")