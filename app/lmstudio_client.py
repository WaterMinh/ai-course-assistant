import re
from collections import Counter
from typing import List, Optional

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
    text = text or ""

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


# ============================================================
# LM Studio client
# ============================================================

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


# ============================================================
# General Chat / Course Chat
# ============================================================

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


# ============================================================
# Summary
# ============================================================

def summarize_course_lmstudio(context: str, language: str = "English") -> str:
    if language == "Traditional Chinese zh-TW":
        target_language = "Traditional Chinese zh-TW"
        language_instruction = """
TARGET LANGUAGE: Traditional Chinese zh-TW.

You must write the entire summary in Traditional Chinese.
Use Taiwan-style Traditional Chinese only.
Do not use Simplified Chinese.
Do not use Vietnamese.
Do not write English sentences.
English technical terms are allowed only if they are standard course terms, for example FastAPI, MySQL, BFS, DFS, Dijkstra.
All section titles, bullet points, explanations, and conclusions must be in Traditional Chinese.
"""
        section_names = """
1. 簡短總覽
2. 主要概念
3. 重要方法或演算法
4. 重要公式或複雜度
5. 應用場景
6. 複習重點
"""

    elif language == "Vietnamese":
        target_language = "Vietnamese"
        language_instruction = """
TARGET LANGUAGE: Vietnamese.

You must write the entire summary in Vietnamese.
Do not use Chinese.
Do not use Traditional Chinese section titles.
Do not use English sentences.
English technical terms are allowed only if they are standard course terms, for example FastAPI, MySQL, BFS, DFS, Dijkstra.
If the source document is Chinese or English, translate the content into Vietnamese.
All section titles, bullet points, explanations, and conclusions must be in Vietnamese.
"""
        section_names = """
1. Tổng quan ngắn
2. Khái niệm chính
3. Phương pháp hoặc thuật toán quan trọng
4. Công thức hoặc độ phức tạp quan trọng
5. Ứng dụng
6. Ghi nhớ khi ôn tập
"""

    else:
        target_language = "English"
        language_instruction = """
TARGET LANGUAGE: English.

You must write the entire summary in English.
Do not use Chinese.
Do not use Vietnamese.
Do not use Traditional Chinese section titles.
If the source document is Chinese or Vietnamese, translate the content into English.
All section titles, bullet points, explanations, and conclusions must be in English.
"""
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

STRICT LANGUAGE RULE:
{language_instruction}

The selected output language is: {target_language}

This rule is mandatory:
- If selected output language is English, output English only.
- If selected output language is Vietnamese, output Vietnamese only.
- If selected output language is Traditional Chinese zh-TW, output Traditional Chinese only.
- Never copy source-language sentences directly if they are not in the selected output language.
- Translate the document content into the selected output language when necessary.

Use only the document context below.
Do not use outside knowledge.
Do not add topics, algorithms, or formulas that are not clearly present in the document.

Important rules:
- Do not mix languages.
- Do not create extra sections.
- Do not repeat the same concept or algorithm in multiple sections.
- Do not create sections named "Detailed Algorithms", "Key Algorithms", "Detailed Concepts", or "Summary".
- Do not use Markdown symbols such as ###, ####, **bold**, or backticks.
- Use normal numbered sections.
- Use "-" for bullet points.
- Each section should contain 1-3 useful bullet points.
- If a section has no relevant information in the document, skip that section.
- Do not write a long essay.
- Do not write an introduction before section 1.
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

Now write the summary in {target_language}.
"""

    raw_summary = call_lm_studio(
        prompt,
        timeout=300,
        max_output_tokens=1800
    )

    summary = clean_summary_output(raw_summary)

    return summary


# ============================================================
# Quiz helpers
# ============================================================

def normalize_quiz_text(text: str) -> str:
    text = clean_model_output(text)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = text.replace("---", "").strip()

    bad_phrases = [
        "Certainly! Here is a Vietnamese quiz based on the provided document, following your requirements:",
        "Certainly! Here is a quiz based on the provided document:",
        "Certainly! Here is",
        "Here is a quiz",
        "Quiz:",
        "Title:",
    ]

    for phrase in bad_phrases:
        text = text.replace(phrase, "")

    # Normalize question numbering: Question 1 / Q1 -> 1.
    text = re.sub(r"(?im)^\s*Question\s+(\d+)\s*[:：.-]\s*", r"\1. ", text)
    text = re.sub(r"(?im)^\s*Q\s*(\d+)\s*[:：.-]\s*", r"\1. ", text)

    # Split inline choices into new lines:
    # "question A. xxx B. xxx C. xxx D. xxx" -> separate lines
    text = re.sub(r"\s+([A-D])[\.\)]\s+", r"\n\1. ", text)
    text = re.sub(r"\s+([A-D])[:：]\s+", r"\n\1. ", text)
    text = re.sub(r"\s+([A-D])、\s+", r"\n\1. ", text)

    # Normalize choice labels at line start
    text = re.sub(r"(?m)^\s*([A-D])\)\s*", r"\1. ", text)
    text = re.sub(r"(?m)^\s*([A-D])[:：]\s*", r"\1. ", text)
    text = re.sub(r"(?m)^\s*([A-D])、\s*", r"\1. ", text)

    # Put Answer / Explanation on separate lines
    text = re.sub(
        r"\s+(Answer|Correct Answer|答案|解答|正確答案|正确答案)\s*[:：]",
        r"\n\1:",
        text,
        flags=re.IGNORECASE
    )
    text = re.sub(
        r"\s+(Explanation|解析|說明|解释|解釋)\s*[:：]",
        r"\n\1:",
        text,
        flags=re.IGNORECASE
    )

    # Keep only content starting from first numbered question when possible
    match = re.search(r"(?m)^\s*1[\.\)]\s+", text)
    if match:
        text = text[match.start():].strip()
    else:
        match = re.search(r"\b1[\.\)]\s+", text)
        if match:
            text = text[match.start():].strip()

    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


def split_quiz_questions(text: str) -> List[str]:
    text = normalize_quiz_text(text)

    blocks = re.split(r"\n(?=\s*\d+[\.\)]\s+)", text)
    blocks = [block.strip() for block in blocks if block.strip()]

    return blocks


def quiz_block_is_valid(block: str) -> bool:
    block = normalize_quiz_text(block)

    bad_placeholders = [
        "Question text",
        "Choice text",
        "Short explanation",
        "short explanation here",
        "choice here",
        "Write a real option",
        "Write a real question",
        "Write a real explanation",
        "This question asks for the correct option from a multiple-choice list",
        "requiring a direct selection without extra context",
    ]

    for bad in bad_placeholders:
        if bad.lower() in block.lower():
            return False

    has_a = re.search(r"(?m)^\s*A[\.\)]\s+\S+", block)
    has_b = re.search(r"(?m)^\s*B[\.\)]\s+\S+", block)
    has_c = re.search(r"(?m)^\s*C[\.\)]\s+\S+", block)
    has_d = re.search(r"(?m)^\s*D[\.\)]\s+\S+", block)

    has_answer = re.search(
        r"(?m)^\s*(Answer|Correct Answer|答案|解答|正確答案|正确答案)\s*[:：]\s*[ABCD]",
        block,
        re.IGNORECASE
    )

    has_explanation = re.search(
        r"(?m)^\s*(Explanation|解析|說明|解释|解釋)\s*[:：]\s+\S+",
        block,
        re.IGNORECASE
    )

    return bool(has_a and has_b and has_c and has_d and has_answer and has_explanation)


def renumber_quiz_block(block: str, number: int) -> str:
    block = normalize_quiz_text(block)

    # If the model returned several questions, keep only the first one here.
    blocks = split_quiz_questions(block)
    if blocks:
        block = blocks[0]

    block = re.sub(
        r"^\s*\d+[\.\)]\s*",
        f"{number}. ",
        block,
        count=1
    ).strip()

    return block


def clean_quiz_output(text: str, question_count: Optional[int] = None) -> str:
    blocks = split_quiz_questions(text)

    valid_blocks = []

    for block in blocks:
        if quiz_block_is_valid(block):
            valid_blocks.append(block)

    if question_count is not None:
        try:
            question_count = int(question_count)
        except (TypeError, ValueError):
            question_count = 5

        question_count = max(1, min(question_count, 10))
        valid_blocks = valid_blocks[:question_count]

    renumbered_blocks = []

    for index, block in enumerate(valid_blocks, start=1):
        renumbered_blocks.append(renumber_quiz_block(block, index))

    return "\n\n".join(renumbered_blocks).strip()


def quiz_format_is_valid(text: str, question_count: int) -> bool:
    try:
        question_count = int(question_count)
    except (TypeError, ValueError):
        question_count = 5

    question_count = max(1, min(question_count, 10))

    blocks = split_quiz_questions(text)
    valid_blocks = [block for block in blocks if quiz_block_is_valid(block)]

    return len(valid_blocks) >= question_count


def extract_topic_from_context(context: str, language: str = "English") -> str:
    if language == "Traditional Chinese zh-TW":
        cjk_matches = re.findall(r"[\u4e00-\u9fff]{2,8}", context)
        if cjk_matches:
            return Counter(cjk_matches).most_common(1)[0][0]
        return "課程文件內容"

    words = re.findall(r"\b[A-Za-z][A-Za-z0-9_-]{3,}\b", context)

    stopwords = {
        "this", "that", "with", "from", "have", "which", "will", "their",
        "there", "about", "document", "course", "using", "used", "also",
        "when", "where", "what", "each", "such", "into", "than", "then",
        "these", "those", "based", "because", "between", "through"
    }

    cleaned = [word.lower() for word in words if word.lower() not in stopwords]

    if not cleaned:
        return "the uploaded document topic"

    most_common = Counter(cleaned).most_common(1)[0][0]

    return most_common.title()


def make_fallback_quiz_question(
    context: str,
    language: str,
    question_number: int
) -> str:
    topic = extract_topic_from_context(context, language)

    if language == "Traditional Chinese zh-TW":
        return f"""
{question_number}. 根據上傳的課程文件，下列哪一項最符合文件中討論的主題？
A. {topic}
B. 烹飪方法
C. 旅遊安排
D. 電影評論
Answer: A
Explanation: 文件內容主要與「{topic}」相關，因此 A 是最適合的答案。
""".strip()

    return f"""
{question_number}. According to the uploaded course document, which option is most related to the document content?
A. {topic}
B. Cooking methods
C. Travel planning
D. Movie reviews
Answer: A
Explanation: The document content is mainly related to {topic}, so option A is the best answer.
""".strip()


def generate_one_quiz_question(
    context: str,
    language: str,
    question_number: int
) -> str:
    if language == "Traditional Chinese zh-TW":
        target_language = "Traditional Chinese zh-TW"
        language_instruction = """
Traditional Chinese zh-TW only.
Use Taiwan-style Traditional Chinese.
The question, choices, answer, and explanation must all be in Traditional Chinese.
Use the labels "Answer:" and "Explanation:" exactly.
Do not use Simplified Chinese.
"""
    else:
        target_language = "English"
        language_instruction = """
English only.
The question, choices, answer, and explanation must all be in English.
Use the labels "Answer:" and "Explanation:" exactly.
"""

    prompt = f"""
You are an AI course assistant.

Create ONE real multiple-choice question based ONLY on the uploaded course document.

STRICT LANGUAGE RULE:
{language_instruction}

CONTENT RULES:
- The question must be about a real concept from the document.
- The choices must be real answer choices.
- Do not use placeholder text.
- Do not write "Question text".
- Do not write "Choice text".
- Do not write "Short explanation".
- Do not create a generic template.
- Do not create a short-answer question.
- Do not create an open-ended question.
- Do not use outside knowledge.

FORMAT RULES:
- Create exactly ONE question.
- Start directly with "{question_number}."
- The question must have exactly four choices.
- Each choice must start on a new line with A., B., C., D.
- Include one answer line starting with Answer:
- Include one explanation line starting with Explanation:
- Do not write a title.
- Do not write an introduction.

Line order:
1. numbered question line
2. A. choice line
3. B. choice line
4. C. choice line
5. D. choice line
6. Answer line
7. Explanation line

Document context:
{context}

Now create question {question_number} in {target_language}.
"""

    raw = call_lm_studio(
        prompt,
        timeout=300,
        max_output_tokens=800
    )

    block = renumber_quiz_block(raw, question_number)

    return block


def generate_full_quiz_once(
    context: str,
    language: str,
    question_count: int
) -> str:
    if language == "Traditional Chinese zh-TW":
        target_language = "Traditional Chinese zh-TW"
        language_instruction = """
Traditional Chinese zh-TW only.
Use Taiwan-style Traditional Chinese.
Questions, choices, answers, and explanations must all be in Traditional Chinese.
Use the labels "Answer:" and "Explanation:" exactly.
Do not use Simplified Chinese.
"""
    else:
        target_language = "English"
        language_instruction = """
English only.
Questions, choices, answers, and explanations must all be in English.
Use the labels "Answer:" and "Explanation:" exactly.
"""

    prompt = f"""
You are an AI course assistant.

Create a real multiple-choice quiz based ONLY on the uploaded course document.

STRICT LANGUAGE RULE:
{language_instruction}

CONTENT RULES:
- Every question must be about a real concept from the document.
- Every choice must be a real answer choice.
- Do not use placeholder text.
- Do not write "Question text".
- Do not write "Choice text".
- Do not write "Short explanation".
- Do not create generic template questions.
- Do not create short-answer questions.
- Do not create open-ended questions.
- Do not use outside knowledge.

FORMAT RULES:
- Create exactly {question_count} questions.
- Number questions from 1 to {question_count}.
- Each question must have exactly four choices.
- Each choice must start on a new line with A., B., C., D.
- Each question must include one answer line starting with Answer:
- Each question must include one explanation line starting with Explanation:
- Do not write a title.
- Do not write an introduction.
- Start directly with question 1.

Document context:
{context}

Now create exactly {question_count} real multiple-choice questions in {target_language}.
"""

    max_tokens = max(1500, question_count * 450)

    raw_quiz = call_lm_studio(
        prompt,
        timeout=300,
        max_output_tokens=max_tokens
    )

    return raw_quiz


def generate_quiz_lmstudio(
    context: str,
    language: str = "English",
    question_count: int = 5
) -> str:
    try:
        question_count = int(question_count)
    except (TypeError, ValueError):
        question_count = 5

    question_count = max(1, min(question_count, 10))

    final_questions = []

    # First try generating the full quiz.
    # If the local model makes bad first questions, keep only valid blocks.
    for _ in range(2):
        raw_quiz = generate_full_quiz_once(
            context=context,
            language=language,
            question_count=question_count
        )

        cleaned_quiz = clean_quiz_output(raw_quiz, question_count=question_count)
        blocks = split_quiz_questions(cleaned_quiz)

        for block in blocks:
            if len(final_questions) >= question_count:
                break

            if quiz_block_is_valid(block):
                final_questions.append(
                    renumber_quiz_block(block, len(final_questions) + 1)
                )

        if len(final_questions) >= question_count:
            return "\n\n".join(final_questions[:question_count]).strip()

    # Generate missing questions one by one.
    while len(final_questions) < question_count:
        question_number = len(final_questions) + 1
        valid_block = None

        for _ in range(4):
            block = generate_one_quiz_question(
                context=context,
                language=language,
                question_number=question_number
            )

            if quiz_block_is_valid(block):
                valid_block = block
                break

        if valid_block is None:
            valid_block = make_fallback_quiz_question(
                context=context,
                language=language,
                question_number=question_number
            )

        final_questions.append(
            renumber_quiz_block(valid_block, question_number)
        )

    return "\n\n".join(final_questions[:question_count]).strip()