import re
from openai import OpenAI
from app.config import LM_STUDIO_URL, LM_STUDIO_MODEL


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

def clean_model_output(text: str) -> str:
    text = text.replace("####", "")
    text = text.replace("###", "")
    text = text.replace("##", "")
    text = text.replace("#", "")
    text = text.replace("**", "")
    text = text.replace("__", "")
    text = text.replace("`", "")

    text = normalize_math_format(text)

    return text.strip()

def clean_summary_output(text: str) -> str:
    text = clean_model_output(text)

    stop_patterns = [
        r"\n\s*Detailed Algorithms\s*\n",
        r"\n\s*Key Algorithms\s*\n",
        r"\n\s*Detailed Concepts\s*\n",
        r"\n\s*Time Complexities\s*\n",
        r"\n\s*Applications and Considerations\s*\n",
        r"\n\s*Additional Details\s*\n",
        r"\n\s*詳細演算法\s*\n",
        r"\n\s*關鍵演算法\s*\n",
        r"\n\s*Chi tiết thuật toán\s*\n",
        r"\n\s*Thuật toán chính\s*\n",
    ]

    for pattern in stop_patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            text = text[:match.start()]
            break

    return text.strip()


client = OpenAI(
    base_url=LM_STUDIO_URL,
    api_key="lm-studio"
)


def call_lm_studio(prompt: str, timeout: int = 300, max_output_tokens: int = 1200) -> str:
    response = client.with_options(timeout=timeout).chat.completions.create(
        model=LM_STUDIO_MODEL,
        messages=[
            {
                "role": "system",
                "content": "You are a careful academic course assistant. Follow the user's language and formatting instructions exactly."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.1,
        max_tokens=max_output_tokens
    )

    return clean_model_output(response.choices[0].message.content or "")


def ask_general_lmstudio(question: str) -> str:
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

    return call_lm_studio(prompt)


def ask_course_lmstudio(question: str, context: str = "") -> str:
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

    return call_lm_studio(prompt)


def ask_lmstudio(question: str, context: str = "") -> str:
    if context:
        return ask_course_lmstudio(question, context)

    return ask_general_lmstudio(question)

def summarize_course_lmstudio(context: str, language: str = "English") -> str:
    if language == "Traditional Chinese zh-TW":
        language_instruction = "繁體中文。只能使用台灣常用繁體中文回答，不要使用英文句子。"
        section_names = """
1. 簡短總覽
2. 主要概念
3. 重要方法或演算法
4. 重要公式或複雜度
5. 應用場景
6. 複習重點
"""
    elif language == "Vietnamese":
        language_instruction = "Vietnamese. Use Vietnamese only."
        section_names = """
1. Tổng quan ngắn
2. Khái niệm chính
3. Phương pháp hoặc thuật toán quan trọng
4. Công thức hoặc độ phức tạp quan trọng
5. Ứng dụng
6. Ghi nhớ khi ôn tập
"""
    else:
        language_instruction = "English. Use English only."
        section_names = """
1. Short overview
2. Main concepts
3. Important methods or algorithms
4. Important formulas or complexity
5. Applications or use cases
6. Short review conclusion
"""

    prompt = f"""
You are an AI course assistant.

Your task:
Summarize the uploaded course document.

Language:
{language_instruction}
This language rule is mandatory.
If the selected language is Traditional Chinese, all section titles and bullet points must be in Traditional Chinese.
If the selected language is Vietnamese, all section titles and bullet points must be in Vietnamese.
If the selected language is English, all section titles and bullet points must be in English.

Use only the document context below.
Do not use outside knowledge.
Do not add topics, algorithms, or formulas that are not clearly present in the document.

Important rules:
- Do not mix languages.
- Do not repeat the same concept or algorithm in multiple sections.
- Do not create extra sections.
- Do not create sections named "Detailed Algorithms", "Key Algorithms", "Detailed Concepts", or "Summary".
- Do not use Markdown symbols such as ###, ####, **bold**, or backticks.
- Use normal numbered sections.
- Use "-" for bullet points.
- Each section should contain 1-3 useful bullet points.
- If a section has no relevant information in the document, skip that section.
- Do not write a long essay.
- Stop after the final review/conclusion section.

Formula rules:
- If formulas, notation, or complexity appear, write them in LaTeX format.
- Always wrap mathematical notation in inline LaTeX using \\( ... \\).
- Write \\(O(n^2)\\), \\(O(n+e)\\), \\(O(e \\log e)\\), not plain O(n^2).
- Write \\(G=(V,E)\\), not plain G=(V, E).
- Write powers with LaTeX syntax, for example \\(n^2\\), \\(V^3\\), \\(2^n\\).
- Do not use code formatting or backticks for formulas.

Required section structure:
{section_names}

Document context:
{context}

Now write the summary.
"""

    raw_summary = call_lm_studio(
        prompt,
        timeout=300,
        max_output_tokens=1800
    )

    return clean_summary_output(raw_summary)

def normalize_math_format(text: str) -> str:
    # Protect existing LaTeX inline formulas first
    protected = []

    def protect_match(match):
        protected.append(match.group(0))
        return f"@@MATH{len(protected) - 1}@@"

    text = re.sub(r"\\\(.+?\\\)", protect_match, text)

    # Convert plain complexity like O(n^2), O(n+e), O(e log e)
    text = re.sub(
        r"(?<![A-Za-z\\])O\(([^)]*)\)",
        r"\\(O(\1)\\)",
        text
    )

    # Convert G=(V, E) or G = (V, E)
    text = re.sub(
        r"(?<![A-Za-z\\])G\s*=\s*\(V,\s*E\)",
        r"\\(G=(V,E)\\)",
        text
    )

    # Restore protected LaTeX
    for i, formula in enumerate(protected):
        text = text.replace(f"@@MATH{i}@@", formula)

    return text