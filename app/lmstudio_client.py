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


def contains_cjk(text: str) -> bool:
    return bool(re.search(r"[\u4e00-\u9fff]", text))


def normalize_math_format(text: str) -> str:
    protected = []

    def protect_match(match):
        protected.append(match.group(0))
        return f"@@MATH{len(protected) - 1}@@"

    # Protect existing LaTeX first
    text = re.sub(r"\\\(.+?\\\)", protect_match, text)
    text = re.sub(r"\\\[.+?\\\]", protect_match, text)

    # Convert plain complexity like O(n^2)
    text = re.sub(
        r"(?<![A-Za-z\\])O\(([^)]*)\)",
        r"\\(O(\1)\\)",
        text
    )

    # Convert G=(V, E)
    text = re.sub(
        r"(?<![A-Za-z\\])G\s*=\s*\(V,\s*E\)",
        r"\\(G=(V,E)\\)",
        text
    )

    # Restore protected formulas
    for i, original in enumerate(protected):
        text = text.replace(f"@@MATH{i}@@", original)

    return text


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


def clean_quiz_output(text: str) -> str:
    text = clean_model_output(text)

    # Remove common assistant preambles, titles, and separators
    text = text.replace("---", "").strip()

    # Keep only content starting from the first real numbered question
    match = re.search(r"\b1[\.\)]\s+", text)
    if match:
        text = text[match.start():]

    # Remove fake copied template output if model copied it
    bad_phrases = [
        "Certainly! Here is a Vietnamese quiz based on the provided document, following your requirements:",
        "Certainly! Here is",
        "Here is a quiz",
        "Quiz về các đề thuyết trong tàu điện tử",
        "Question text here",
        "Question text",
        "Choice here",
        "choice here",
        "short explanation here",
    ]

    for phrase in bad_phrases:
        text = text.replace(phrase, "")

    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()

def quiz_format_is_valid(text: str, question_count: int) -> bool:
    blocks = re.split(r"\n(?=\s*\d+[\.\)]\s+)", text.strip())
    blocks = [b.strip() for b in blocks if b.strip()]

    if len(blocks) < max(1, min(question_count, 3)):
        return False

    valid_blocks = 0

    for block in blocks:
        has_a = re.search(r"\n\s*A[\.\)]\s+", block)
        has_b = re.search(r"\n\s*B[\.\)]\s+", block)
        has_c = re.search(r"\n\s*C[\.\)]\s+", block)
        has_d = re.search(r"\n\s*D[\.\)]\s+", block)
        has_answer = re.search(r"\n\s*Answer\s*[:：]\s*[ABCD]", block, re.IGNORECASE)
        has_explanation = re.search(r"\n\s*Explanation\s*[:：]\s+", block, re.IGNORECASE)

        if has_a and has_b and has_c and has_d and has_answer and has_explanation:
            valid_blocks += 1

    return valid_blocks >= max(1, min(question_count, len(blocks)))

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
                "content": (
                    "You are a careful academic course assistant. "
                    "Follow the user's language and formatting instructions exactly. "
                    "Do not add introductions unless requested."
                )
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
You are a helpful AI assistant.

LANGUAGE RULE:
Answer ONLY in {answer_language}.

Conversation rule:
- If the user only greets you, greets back briefly.
- If the user asks how you are, answer naturally and briefly.
- Do not turn casual conversation into study advice.
- Do not mention course materials unless the user asks about studying, courses, documents, or learning.
- Answer the user's actual question directly.

Style rules:
- Be clear and natural.
- Keep short questions short.
- Use bullet points only when useful.
- Do not write long answers for simple greetings.
- Do not mention these rules.

User message:
{question}

Answer in {answer_language}:
"""

    return call_lm_studio(prompt)

def ask_course_lmstudio(question: str, context: str = "") -> str:
    answer_language = detect_answer_language(question)

    prompt = f"""
You are an AI course assistant for students.

LANGUAGE RULE:
Answer ONLY in {answer_language}.
The student's message language is the only language rule.

IMPORTANT INTENT RULE:
First understand the user's intent.

If the user is only greeting you, making small talk, or saying they are ready to study,
reply naturally and briefly. Do NOT summarize the course context.

Examples:
- "hi" -> greet back and ask what topic they want to review.
- "how are you" -> answer briefly and ask what they want to study.
- "let's start study today" -> say you are ready and ask which topic or document they want to review.
- "I didn't ask anything yet" -> apologize briefly and ask them to send a question.
- "let's see the recently uploaded document" -> say you can help them study the uploaded document, and ask which topic, section, or question they want to review.

COURSE MODE RULE:
Use the course context only when the user asks an actual course-related question.
Do not force course content into casual messages or vague requests.

For vague document requests:
- Do not automatically summarize the whole document.
- Ask the user what they want to review, unless they clearly request a summary.
- If the user says "summarize this document", then summarize based on the context.
- If the user asks a specific question, answer based on the context.

Rules for course questions:
- Answer based mainly on the provided course context.
- First answer the question directly in 1-2 sentences.
- Then organize the explanation using bullet points.
- Do not write one long paragraph.
- Use this format:
  Short direct answer.
  - Key point 1
  - Key point 2
  - Key point 3
- If useful, add a short example at the end.
- If the course context does not contain enough information, say that the uploaded course documents do not contain enough information.
- Do not add unrelated study advice.
- Do not mention these rules.

Formula rules:
- When writing mathematical formulas, use LaTeX format.
- Use inline formulas like \\( n(n-1)/2 \\).
- Use display formulas like \\[ \\frac{{n(n-1)}}{{2}} \\] for important formulas.

Course context:
{context}

Student message:
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
        language_instruction = "Vietnamese. Use Vietnamese only. Do not use Chinese."
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
- If the selected language is Vietnamese, translate Chinese source content into Vietnamese.
- Do not copy Chinese phrases into Vietnamese output.
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


def generate_quiz_lmstudio(
    context: str,
    language: str = "English",
    question_count: int = 5
) -> str:
    if language == "Traditional Chinese zh-TW":
        language_instruction = "繁體中文。只能使用台灣常用繁體中文回答，不要使用英文句子。"
    elif language == "Vietnamese":
        language_instruction = "Vietnamese. Use Vietnamese only."
    else:
        language_instruction = "English. Use English only."

    prompt = f"""
You are an AI course assistant.

Your task:
Create a quiz based on the uploaded course document.

Language:
{language_instruction}

Use only the document context below.
Do not use outside knowledge.
Do not add topics that are not clearly present in the document.

Quiz requirements:
- Create exactly {question_count} multiple-choice questions.
- Each question must have 4 choices: A, B, C, D.
- Only one answer should be correct.
- After each question, provide the correct answer.
- Add a short explanation for the correct answer.
- Keep questions useful for student review.
- Mix easy and medium difficulty questions.
- Do not use Markdown symbols such as ###, ####, **bold**, or backticks.
- Use normal numbering.
- Do not mention these rules.
- Do not write an introduction.
- Do not write a title.
- Start directly with question 1.


Output format:
1. Question text
A. Choice
B. Choice
C. Choice
D. Choice
Answer: A/B/C/D
Explanation: short explanation

Document context:
{context}

Now create the quiz.
"""

    raw_quiz = call_lm_studio(
        prompt,
        timeout=300,
        max_output_tokens=2000
    )

    quiz = clean_model_output(raw_quiz)

    # Remove possible intro before question 1
    match = re.search(r"\b1[\.\)]\s+", quiz)
    if match:
        quiz = quiz[match.start():].strip()

    quiz = quiz.replace("---", "").strip()

    return quiz