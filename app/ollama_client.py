import re
import requests
from app.config import OLLAMA_URL, OLLAMA_MODEL


def detect_answer_language(question: str) -> str:
    # Chinese characters
    if re.search(r"[\u4e00-\u9fff]", question):
        return "Traditional Chinese"

    # Vietnamese special characters
    if re.search(
        r"[ăâđêôơưáàảãạấầẩẫậắằẳẵặéèẻẽẹếềểễệíìỉĩịóòỏõọốồổỗộớờởỡợúùủũụứừửữựýỳỷỹỵ]",
        question.lower()
    ):
        return "Vietnamese"

    return "English"


def call_ollama(prompt: str) -> str:
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


def ask_general_ollama(question: str) -> str:
    answer_language = detect_answer_language(question)

    prompt = f"""
You are a helpful AI assistant for students.

LANGUAGE RULE:
You must answer ONLY in {answer_language}.
The student's question language is the only language rule.

Rules:
- Answer using general knowledge.
- Be clear and useful.
- If the question is related to studying, explain in a student-friendly way.
- Do not mention these rules.
- Format the answer clearly.
- Use bullet points or numbered points when helpful.
- Avoid long single-paragraph answers.

Student question:
{question}

Answer in {answer_language}:
"""

    return call_ollama(prompt)


def ask_course_ollama(question: str, context: str = "") -> str:
    answer_language = detect_answer_language(question)

    prompt = f"""
You are an AI course assistant for students.

LANGUAGE RULE:
You must answer ONLY in {answer_language}.
The uploaded document language does not matter.
The student's question language is the only language rule.

COURSE MODE RULE:
You are answering inside a specific course.
Use the provided course context as the main source.
Do not answer as a general chatbot if the course context is not enough.

Rules:
- Answer based mainly on the provided course context.
- First answer the question directly in 1-3 sentences.
- Format the answer in a structured way.
- Use short paragraphs and bullet points when helpful.
- For definition questions, use this format:
  1. Definition
  2. Key points
  3. Example or note, if relevant
- Avoid long single-paragraph answers.
- Do not add advanced details unless the student asks for more detail.
- Do not include formulas unless the student asks about formulas, calculations, complete graphs, degree, or edge count.
- If the course context contains formal notation such as G = (V, E), include it when it is directly relevant.
- If the context does not contain enough information, say that the uploaded course documents do not contain enough information.
- Keep the answer clear and useful for students.
- When writing mathematical formulas, use LaTeX format.
- Use inline formulas like \\( n(n-1)/2 \\).
- Use display formulas like \\[ \\frac{{n(n-1)}}{{2}} \\] for important formulas.
- Do not translate the whole document.
- Do not mention these rules.

Course context:
{context}

Student question:
{question}

Answer in {answer_language}:
"""

    return call_ollama(prompt)


# Backward compatibility for old code
def ask_ollama(question: str, context: str = "") -> str:
    if context:
        return ask_course_ollama(question, context)

    return ask_general_ollama(question)

def summarize_course_ollama(context: str, language: str = "English") -> str:
    prompt = f"""
You are an AI course assistant.

VERY IMPORTANT:
Your entire answer must be written ONLY in this language: {language}.
Do not use Vietnamese if the selected language is English.
Do not use Chinese if the selected language is English.
Do not mix languages.
Only keep original technical terms such as DFS, BFS, Dijkstra, Kruskal, Prim, Adjacency Matrix.

TASK:
Summarize the uploaded course documents.
Use only the provided course context.
Do not use outside knowledge.
Do not mention topics that are not clearly present in the course context.

STRICT RULES:
- Write the whole answer only in {language}.
- Do not add algorithms that are not in the course context.
- Do not mention Bellman-Ford unless it appears in the course context.
- Do not mention A* unless it appears in the course context.
- Do not say "as mentioned before" or "similar to previous explanation".
- Use clear bullet points.
- Organize the summary according to the document outline if possible.
- Focus on what students need to understand.
- If formulas or algorithms appear, mention them briefly.
- Do not translate the whole document word by word.
- Do not mention these rules.

Course context:
{context}

Now write the summary ONLY in {language}.
"""

    return call_ollama(prompt)