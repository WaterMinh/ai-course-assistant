# AI Course Assistant

A local AI-powered learning platform that transforms static course materials into interactive learning experiences using local Large Language Models (LLMs).

<p align="center">
  <img src="images/Admin_Dashboard.png" alt="Dashboard" width="900">
</p>

## ✨ Highlights

- 🤖 Local AI learning assistant powered by LM Studio
- 📚 Course-grounded chat based on uploaded documents
- 📝 AI-generated multilingual summaries
- ❓ Automatic quiz generation with answer explanations
- 📄 One-click PDF export for summaries and quizzes
- 👨‍🏫 Role-based admin dashboard for course and document management
  
---
## Overview

AI Course Assistant is a locally hosted learning platform designed to transform static course materials into interactive study resources.

Administrators can create courses and upload learning documents, while students can interact with course content through AI-powered conversations, multilingual summaries, automatically generated quizzes, and PDF exports.

The project integrates FastAPI, MySQL, Docker, and LM Studio to demonstrate how modern AI technologies can enhance personalized learning while keeping all data processed locally.
---
## 🏗️ Architecture

```mermaid
flowchart TD
    U[Browser]

    U --> F[FastAPI Backend]

    F --> DB[(MySQL Database)]

    F --> DOC[Document Processing]

    DOC --> CHUNK[Text Chunking]

    CHUNK --> LLM[LM Studio Local LLM]

    LLM --> CHAT[Course Chat]

    LLM --> SUM[Summary Generator]

    LLM --> QUIZ[Quiz Generator]

    DB --> CACHE[Summary & Quiz Cache]

    CHAT --> U
    SUM --> U
    QUIZ --> U
```
---
![Python](https://img.shields.io/badge/Python-3.11-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-Framework-green)
![MySQL](https://img.shields.io/badge/MySQL-Database-blue)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED)
![LM Studio](https://img.shields.io/badge/Local%20LLM-LM%20Studio-orange)
---
## Features

* User login system

* Admin and student roles

* Course management

* Upload documents into specific courses

* General AI chatbot

* Course-specific AI chatbot based on uploaded documents

* Document-level AI summaries

* Multilingual summaries:

  * English
  * Vietnamese
  * Traditional Chinese

* Quiz generator for each document

* Stable quiz languages:

  * English
  * Traditional Chinese

* Hidden quiz answers with click-to-reveal

* Regenerate Summary button

* Regenerate Quiz button

* Export Summary to PDF

* Export Quiz to PDF

* Chat history

* Taiwan time display for chat history

* MySQL database storage

* Summary cache by document and language

* Quiz cache by document, language, and question count

* Math formula rendering with MathJax

* Local LLM support through LM Studio

* Improved Admin Dashboard with statistics

* Improved UI layout for chat, courses, summaries, quizzes, and admin pages

* Improved chat intent handling for greetings, small talk, course questions, and real-time information questions

* Improved AI answer formatting with bullet points

---

## Tech Stack

* Python
* FastAPI
* SQLAlchemy
* MySQL
* Docker Compose
* Jinja2 Templates
* Bootstrap
* JavaScript
* MathJax
* LM Studio local LLM API
* PyMySQL
* Uvicorn

---

## Project Structure

```text
ai_course_assistant/
├── app/
│   ├── main.py
│   ├── models.py
│   ├── database.py
│   ├── config.py
│   ├── auth.py
│   ├── document_utils.py
│   └── lmstudio_client.py
├── templates/
│   ├── base.html
│   ├── login.html
│   ├── chat.html
│   ├── admin.html
│   ├── courses.html
│   ├── course_detail.html
│   ├── summary.html
│   ├── document_summary.html
│   ├── document_quiz.html
│   └── history.html
├── static/
│   ├── style.css
│   └── chat.js
├── uploads/
├── docker-compose.yml
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

---

## Requirements

* Python 3.11+
* Docker Desktop
* LM Studio
* A local model loaded in LM Studio, for example Gemma or another OpenAI-compatible local model
* macOS, Linux, or Windows

---

## Setup

### 1. Clone the repository

```bash
git clone <your-repository-url>
cd ai_course_assistant
```

### 2. Create a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

For Windows:

```bash
.venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Start MySQL with Docker

```bash
docker compose up -d mysql
```

### 5. Create `.env`

Create a `.env` file in the project root.

For security reasons, do not commit your real `.env` file to GitHub.
Use `.env.example` for public examples only.

Example `.env.example`:

```env
DATABASE_URL=mysql+pymysql://<username>:<password>@127.0.0.1:3307/<database_name>
SECRET_KEY=<your-secret-key>
UPLOAD_DIR=uploads

LM_STUDIO_URL=http://127.0.0.1:1234/v1
LM_STUDIO_MODEL=<your-local-model-name>
```

Example for local development:

```env
DATABASE_URL=mysql+pymysql://root:your_mysql_password@127.0.0.1:3307/ai_course_assistant
SECRET_KEY=your_secret_key_here
UPLOAD_DIR=uploads

LM_STUDIO_URL=http://127.0.0.1:1234/v1
LM_STUDIO_MODEL=your_model_name_here
```

The model name must match the model currently loaded in LM Studio.

Make sure `.env` is included in `.gitignore`:

```gitignore
.env
```

---

## Start LM Studio

Open LM Studio and start the local server:

```text
Developer / Local Server → Start Server
```

Default server URL:

```text
http://127.0.0.1:1234/v1
```

Check that LM Studio is running:

```bash
curl http://127.0.0.1:1234/v1/models
```

If it returns JSON with model information, the server is working.

---

## Run the App

Activate the virtual environment:

```bash
source .venv/bin/activate
```

Start FastAPI:

```bash
uvicorn app.main:app --reload --port 8010
```

Open the app:

```text
http://127.0.0.1:8010
```

---

## Default Users

Demo users are created automatically on startup.

Check the exact usernames and passwords in:

```text
app/auth.py
```

Typical roles:

```text
admin
student
```

Admin users can create courses and upload documents.

Student users can use chat, summaries, quizzes, PDF export, and history features.

---

## Main Workflow

### Admin Workflow

1. Log in as admin.
2. Open the Admin Dashboard.
3. Create a course.
4. Upload course documents.
5. The system extracts text and creates document chunks.
6. Students can open the course and use AI learning features.

### Student Workflow

1. Log in.
2. Open Courses.
3. Choose a course.
4. Ask questions in Course Chat.
5. Generate document summaries.
6. Generate document quizzes.
7. Reveal quiz answers.
8. Export summaries or quizzes to PDF.
9. Review previous chat history.

---

## General Chat vs Course Chat

### General Chat

General Chat does not use uploaded course documents.

It works like a normal local AI assistant and answers using general knowledge from the loaded LM Studio model.

The assistant handles simple conversation naturally. For example:

* `hi`
* `how are you`
* `how is the weather today?`

If the user asks about real-time information such as weather, live news, prices, or current events, the app clearly explains that the local system does not have access to real-time data.

### Course Chat

Course Chat answers mainly based on uploaded course documents.

The app searches relevant document chunks and sends them to the local model as course context.

Course Chat is designed for questions such as:

* What is web scraping?
* What is BeautifulSoup used for?
* What does this document say about CSS selectors?
* Explain the formula (G=(V,E)).
* Summarize this concept from the uploaded course file.

If the user only sends a greeting or small talk inside Course Chat, the assistant responds naturally instead of forcing document content into the answer.

If the document context does not contain enough information, the assistant should say that the uploaded course documents do not contain enough information.

---

## Document Upload

Each document is uploaded into a specific course.

When a document is uploaded, the system:

1. Saves the uploaded file.
2. Extracts text from the document.
3. Splits the text into smaller chunks.
4. Stores the document metadata in MySQL.
5. Stores document chunks in MySQL.

The chunks are later used for Course Chat, Document Summary, and Document Quiz.

---

## Document Summary

Each document can have a generated summary.

Supported languages:

```text
English
Vietnamese
Traditional Chinese
```

Summaries are cached in the database by:

```text
document_id + language
```

This means:

```text
Graph.pdf + English
Graph.pdf + Vietnamese
Graph.pdf + Traditional Chinese
```

are stored separately.

The first generation may be slow because LM Studio has to generate the text.

The next time the same document and same language are selected, the summary is loaded from MySQL and appears faster.

Users can also click:

```text
Regenerate
```

to force the system to generate a new summary and update the saved cache.

---

## Document Quiz

Each document can have a generated quiz.

The quiz generator creates multiple-choice questions with:

```text
A, B, C, D
Answer
Explanation
```

Answers are hidden by default and can be revealed by clicking the Show Answer button.

Quizzes are cached in the database by:

```text
document_id + language + question_count
```

Example:

```text
Graph.pdf + English + 5 questions
Graph.pdf + Traditional Chinese + 10 questions
```

Users can click:

```text
Regenerate
```

to force the system to create a new quiz and update the saved cache.

### Stable Quiz Languages

The final stable version supports quiz generation in:

```text
English
Traditional Chinese
```

Vietnamese quiz generation was tested, but the local model output was less stable for strict quiz formatting. Therefore, Vietnamese quiz generation is not included in the final stable quiz interface.

---

## Show / Hide Quiz Answers

Quiz answers are hidden by default.

Each quiz question appears as a separate card. The user can click:

```text
Show Answer
```

to reveal the answer and explanation.

After revealing the answer, the user can click:

```text
Hide Answer
```

to hide it again.

This design supports active recall and self-testing instead of passive reading.

---

## PDF Export

Summary and Quiz pages include an Export PDF button.

The system uses browser print mode with custom print CSS.

During PDF export, the page hides:

* Navigation bar
* Forms
* Buttons
* Unnecessary UI elements

The exported PDF keeps the main learning content clean and readable.

Recommended browser setting:

```text
More settings → Headers and footers → Off
```

This prevents browser date and page title from appearing in the exported PDF.

---

## Chat History

The system saves previous chat interactions.

Each history item includes:

* User question
* AI answer
* Timestamp

The displayed time is adjusted to Taiwan time:

```text
UTC+8
```

This prevents the history page from showing UTC time that is 8 hours behind Taiwan local time.

---

## Admin Dashboard

The Admin Dashboard allows admin users to:

* Create courses
* Upload documents
* View uploaded documents
* View system statistics

Dashboard statistics include:

* Number of courses
* Number of uploaded documents
* Number of generated summaries
* Number of generated quizzes

The dashboard UI was improved with cards, tables, cleaner spacing, and a more professional layout.

---

## Math Rendering

The project uses MathJax to render mathematical notation.

Examples:

```text
\(O(n^2)\)
\(O(n+e)\)
\(G=(V,E)\)
```

These should appear as formatted math in the browser.

MathJax is loaded in:

```text
templates/base.html
```

Summary, quiz, and chat pages also trigger MathJax rendering after content is displayed.

---

## Database

The project uses MySQL inside Docker.

Start MySQL:

```bash
docker compose up -d mysql
```

Check running containers:

```bash
docker ps
```

Open MySQL:

```bash
docker exec -it ai_course_mysql mysql -uroot -p ai_course_assistant
```

If your local MySQL password is different, use your own password.

Show tables:

```sql
SHOW TABLES;
```

Check saved summaries:

```sql
SELECT id, document_id, language, created_at
FROM document_summaries;
```

Check saved quizzes:

```sql
SELECT id, document_id, language, question_count, created_at
FROM document_quizzes;
```

Exit MySQL:

```sql
exit;
```

---

## Main Database Tables

The main database tables include:

```text
users
courses
documents
document_chunks
chat_history
document_summaries
document_quizzes
```

### users

Stores user accounts and roles.

### courses

Stores course code, course name, and course description.

### documents

Stores uploaded document metadata.

### document_chunks

Stores extracted document text chunks.

### chat_history

Stores user questions and AI answers.

### document_summaries

Stores generated summaries by document and language.

### document_quizzes

Stores generated quizzes by document, language, and question count.

---

## Docker Volume Warning

Database data is stored in a Docker volume.

Safe command:

```bash
docker compose down
```

Dangerous command, deletes database data:

```bash
docker compose down -v
```

Do not use `docker compose down -v` unless you want to delete all MySQL data.

---

## Useful Commands

Start MySQL:

```bash
docker compose up -d mysql
```

Check LM Studio:

```bash
curl http://127.0.0.1:1234/v1/models
```

Start the app:

```bash
source .venv/bin/activate
uvicorn app.main:app --reload --port 8010
```

Check database summaries:

```bash
docker exec -it ai_course_mysql mysql -uroot -p ai_course_assistant -e "SELECT id, document_id, language, created_at FROM document_summaries;"
```

Check database quizzes:

```bash
docker exec -it ai_course_mysql mysql -uroot -p ai_course_assistant -e "SELECT id, document_id, language, question_count, created_at FROM document_quizzes;"
```

Check Git status:

```bash
git status
```

Commit changes:

```bash
git add .
git commit -m "Update project"
git push
```

---

## Environment Variables

Create a `.env` file in the project root.

Do not commit your real `.env` file to GitHub.
Only commit `.env.example`.

Example `.env.example`:

```env
DATABASE_URL=mysql+pymysql://<username>:<password>@127.0.0.1:3307/<database_name>
SECRET_KEY=<your-secret-key>
UPLOAD_DIR=uploads

LM_STUDIO_URL=http://127.0.0.1:1234/v1
LM_STUDIO_MODEL=<your-local-model-name>
```

Example for local development:

```env
DATABASE_URL=mysql+pymysql://root:your_mysql_password@127.0.0.1:3307/ai_course_assistant
SECRET_KEY=your_secret_key_here
UPLOAD_DIR=uploads

LM_STUDIO_URL=http://127.0.0.1:1234/v1
LM_STUDIO_MODEL=your_model_name_here
```

### Notes

`DATABASE_URL` connects FastAPI to MySQL.

`SECRET_KEY` is used for session security.

`UPLOAD_DIR` is where uploaded documents are stored.

`LM_STUDIO_URL` is the local LM Studio OpenAI-compatible API endpoint.

`LM_STUDIO_MODEL` must match the loaded model in LM Studio.

Make sure `.env` is included in `.gitignore`:

```gitignore
.env
```

---

## Final Stable Feature Set

The current final version includes:

* Login and logout
* Admin and student roles
* General Chat
* Course Chat with document context
* Course management
* Document upload
* Document text extraction
* Document chunking
* Document Summary
* Regenerate Summary
* Document Quiz
* Regenerate Quiz
* Show / Hide Answer
* Export Summary to PDF
* Export Quiz to PDF
* Chat History
* Taiwan time display
* Admin Dashboard
* Dashboard statistics
* MathJax formula rendering
* Improved chat intent handling
* Improved answer formatting with bullet points
* Improved UI styling

---

## Known Limitations

* The app does not have access to real-time information such as weather, live news, or current prices.
* The app uses simple text chunk matching, not vector embeddings.
* Summary and quiz quality depends on the local LLM model used in LM Studio.
* Large PDFs may require better chunking.
* Scanned PDFs may not work well without OCR.
* Vietnamese quiz generation is not included in the final stable quiz interface because the tested local model did not consistently follow the required quiz format.
* No production-grade user management yet.
* No deployment configuration yet.
* No per-course student enrollment system yet.

---

## Future Improvements

* Vector search with embeddings
* OCR support for scanned PDFs
* Flashcard generator
* More advanced PDF export templates
* Student progress tracking
* Per-course student enrollment
* Better file parsing for slides and scanned PDFs
* More stable multilingual quiz generation
* API authentication
* Production deployment
* Learning analytics dashboard
* More advanced admin tools
* Better validation for AI-generated quiz format

---

## Project Purpose

The main purpose of AI Course Assistant is to transform static course documents into interactive learning resources.

Instead of only reading course files, students can:

* Ask questions
* Generate summaries
* Create quizzes
* Reveal answers
* Export learning content
* Review previous chat history

This project demonstrates how web development, databases, document processing, and artificial intelligence can be combined into a practical learning tool.

---

## License

This project is for educational and prototype use.
