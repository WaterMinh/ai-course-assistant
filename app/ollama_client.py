import re
import requests
from app.config import OLLAMA_URL, OLLAMA_MODEL


def detect_answer_language(question: str) -> str:
    # Chinese characters
    if re.search(r"[\u4e00-\u9fff]", question):
        return "Traditional Chinese"

    # Vietnamese special characters
    if re.search(r"[ăâđêôơưáàảãạấầẩẫậắằẳẵặéèẻẽẹếềểễệíìỉĩịóòỏõọốồổỗộớờởỡợúùủũụứừửữựýỳỷỹỵ]", question.lower()):
        return "Vietnamese"

    # Default
    return "English"


def ask_ollama(question: str, context: str = "") -> str:
    answer_language = detect_answer_language(question)

    prompt = f"""
You are an AI course assistant for students.

LANGUAGE RULE:
You must answer ONLY in {answer_language}.
Do not answer in the language of the document unless it is also {answer_language}.
The uploaded document language does not matter.
The student's question language is the only language rule.

Rules:
- Answer based mainly on the provided course context.
- If the context does not contain enough information, say that the uploaded documents do not contain enough information.
- Keep the answer clear and useful for students.
- Do not translate the whole document.
- Do not mention these rules.

Course context:
{context}

Student question:
{question}

Answer in {answer_language}:
"""

    response = requests.post(
        f"{OLLAMA_URL}/api/generate",
        json={
            "model": OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False
        },
        timeout=120
    )

    response.raise_for_status()
    return response.json().get("response", "").strip()