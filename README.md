# AI Course Assistant

AI Course Assistant is a local AI-powered learning platform for courses and uploaded study documents.

The system allows an admin to create courses, upload course documents, and let students ask questions, generate document summaries, and create quizzes based on course materials.

The project runs locally with FastAPI, MySQL, Docker, and LM Studio.

---

## Features

* User login system
* Admin and student roles
* Course management
* Upload documents into specific courses
* General AI chatbot
* Course-specific AI chatbot
* Document-level AI summaries
* Multilingual summaries:

  * English
  * Vietnamese
  * Traditional Chinese
* Quiz generator for each document
* Hidden quiz answers with click-to-reveal
* Chat history
* MySQL database storage
* Summary cache by document and language
* Quiz cache by document, language, and question count
* Math formula rendering with MathJax
* Local LLM support through LM Studio

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
* A local model loaded in LM Studio, for example Gemma
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

Example:

```env
DATABASE_URL=mysql+pymysql://root:rootpassword@127.0.0.1:3307/ai_course_assistant
SECRET_KEY=change-this-secret
UPLOAD_DIR=uploads

LM_STUDIO_URL=http://127.0.0.1:1234/v1
LM_STUDIO_MODEL=gemma
```

The model name should match the model loaded in LM Studio.

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

---

## Main Workflow

### Admin Workflow

1. Log in as admin
2. Open Admin page
3. Create a course
4. Upload course documents
5. Students can open the course and use AI features

### Student Workflow

1. Log in
2. Open Courses
3. Choose a course
4. Ask questions in Course Chat
5. Generate document summaries
6. Generate document quizzes
7. Review previous chat history

---

## General Chat vs Course Chat

### General Chat

General Chat does not use uploaded course documents.

It works like a normal local AI assistant and answers using general knowledge from the loaded LM Studio model.

### Course Chat

Course Chat answers mainly based on uploaded course documents.

The app searches relevant document chunks and sends them to the local model as course context.

If the document context does not contain enough information, the assistant should say that the uploaded course documents do not contain enough information.

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

---

## Document Quiz

Each document can have a generated quiz.

The quiz generator creates multiple-choice questions with:

```text
A, B, C, D
Answer
Explanation
```

Answers are hidden by default and can be revealed by clicking a button.

Quizzes are cached in the database by:

```text
document_id + language + question_count
```

Example:

```text
Graph.pdf + English + 5 questions
Graph.pdf + Vietnamese + 5 questions
Graph.pdf + Traditional Chinese + 10 questions
```

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

Summary and quiz pages also trigger MathJax rendering after content is displayed.

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
docker exec -it ai_course_mysql mysql -uroot -prootpassword ai_course_assistant
```

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
docker exec -it ai_course_mysql mysql -uroot -prootpassword ai_course_assistant -e "SELECT id, document_id, language, created_at FROM document_summaries;"
```

Check database quizzes:

```bash
docker exec -it ai_course_mysql mysql -uroot -prootpassword ai_course_assistant -e "SELECT id, document_id, language, question_count, created_at FROM document_quizzes;"
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

Example `.env`:

```env
DATABASE_URL=mysql+pymysql://root:rootpassword@127.0.0.1:3307/ai_course_assistant
SECRET_KEY=change-this-secret
UPLOAD_DIR=uploads

LM_STUDIO_URL=http://127.0.0.1:1234/v1
LM_STUDIO_MODEL=gemma
```

### Notes

`DATABASE_URL` connects FastAPI to MySQL.

`SECRET_KEY` is used for session security.

`UPLOAD_DIR` is where uploaded documents are stored.

`LM_STUDIO_URL` is the local LM Studio OpenAI-compatible API endpoint.

`LM_STUDIO_MODEL` must match the loaded model in LM Studio.

---

## Current Limitations

* The app uses simple text chunk matching, not vector embeddings.
* Summary and quiz quality depends on the local LLM model.
* Large PDFs may require better chunking.
* Scanned PDFs may not work well without OCR.
* No production-grade user management yet.
* No deployment configuration yet.
* No per-course student enrollment system yet.

---

## Future Improvements

* Vector search with embeddings
* Regenerate Summary button
* Regenerate Quiz button
* Flashcard generator
* Export quiz to PDF
* Export summary to PDF
* Per-course student enrollment
* Better admin dashboard
* Better file parsing for slides and scanned PDFs
* Student progress tracking
* API authentication
* Production deployment

---

## License

This project is for educational and prototype use.
