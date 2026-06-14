import os
import shutil


from fastapi import FastAPI, Request, Depends, Form, UploadFile, File, HTTPException
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from starlette.middleware.sessions import SessionMiddleware
from datetime import timedelta

from app.config import SECRET_KEY, UPLOAD_DIR
from app.database import Base, engine, get_db, SessionLocal
from app.models import User, Course, Document, DocumentChunk, DocumentSummary, DocumentQuiz, ChatHistory
from app.auth import verify_password, create_demo_users
from app.document_utils import (
    extract_text_from_file,
    chunk_text,
    find_relevant_chunks,
    get_course_context,
    get_document_context
)

from app.lmstudio_client import (
    ask_general_lmstudio,
    ask_course_lmstudio,
    summarize_course_lmstudio,
    generate_quiz_lmstudio
)

os.makedirs(UPLOAD_DIR, exist_ok=True)

app = FastAPI(title="AI Course Assistant Platform")

app.add_middleware(
    SessionMiddleware,
    secret_key=SECRET_KEY
)

app.mount(
    "/static",
    StaticFiles(directory="static"),
    name="static"
)

templates = Jinja2Templates(directory="templates")


@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        create_demo_users(db)
    finally:
        db.close()


def current_user(request: Request, db: Session):
    user_id = request.session.get("user_id")

    if not user_id:
        return None

    return db.query(User).filter(User.id == user_id).first()


@app.get("/")
def general_chat_page(request: Request, db: Session = Depends(get_db)):
    user = current_user(request, db)

    if not user:
        return RedirectResponse("/login")

    return templates.TemplateResponse(
        "chat.html",
        {
            "request": request,
            "user": user,
            "chat_title": "General Chat",
            "chat_subtitle": "Ask general questions. This mode does not use course documents.",
            "api_url": "/api/chat"
        }
    )


@app.get("/login")
def login_page(request: Request):
    return templates.TemplateResponse(
        "login.html",
        {
            "request": request,
            "error": None,
            "user": None
        }
    )


@app.post("/login")
def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.username == username).first()

    if not user or not verify_password(password, user.password_hash):
        return templates.TemplateResponse(
            "login.html",
            {
                "request": request,
                "error": "Wrong username or password",
                "user": None
            },
            status_code=401
        )

    request.session["user_id"] = user.id

    return RedirectResponse("/", status_code=303)


@app.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/login")


@app.get("/courses")
def courses_page(request: Request, db: Session = Depends(get_db)):
    user = current_user(request, db)

    if not user:
        return RedirectResponse("/login")

    courses = db.query(Course).order_by(Course.created_at.desc()).all()

    return templates.TemplateResponse(
        "courses.html",
        {
            "request": request,
            "user": user,
            "courses": courses
        }
    )


@app.get("/courses/{course_id}/chat")
def course_chat_page(
    course_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    user = current_user(request, db)

    if not user:
        return RedirectResponse("/login")

    course = db.query(Course).filter(Course.id == course_id).first()

    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    return templates.TemplateResponse(
        "chat.html",
        {
            "request": request,
            "user": user,
            "course": course,
            "chat_title": f"{course.course_code} - {course.course_name}",
            "chat_subtitle": "Ask questions based on this course's uploaded documents.",
            "api_url": f"/api/courses/{course.id}/chat"
        }
    )


@app.get("/admin")
def admin_page(request: Request, db: Session = Depends(get_db)):
    user = current_user(request, db)

    if not user or user.role != "admin":
        return RedirectResponse("/login")

    courses = db.query(Course).order_by(Course.created_at.desc()).all()
    documents = db.query(Document).order_by(Document.created_at.desc()).all()
    
    course_count = db.query(Course).count()
    document_count = db.query(Document).count()
    summary_count = db.query(DocumentSummary).count()
    quiz_count = db.query(DocumentQuiz).count()
    return templates.TemplateResponse(
        "admin.html",
        {
            "request": request,
            "user": user,
            "courses": courses,
            "documents": documents,
            "course_count": course_count,
            "document_count": document_count,
            "summary_count": summary_count,
            "quiz_count": quiz_count
        }
    )


@app.post("/admin/courses")
def create_course(
    request: Request,
    course_code: str = Form(...),
    course_name: str = Form(...),
    description: str = Form(""),
    db: Session = Depends(get_db)
):
    user = current_user(request, db)

    if not user or user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")

    existing = db.query(Course).filter(Course.course_code == course_code).first()

    if existing:
        return RedirectResponse("/admin", status_code=303)

    course = Course(
        course_code=course_code.strip(),
        course_name=course_name.strip(),
        description=description.strip()
    )

    db.add(course)
    db.commit()

    return RedirectResponse("/admin", status_code=303)


@app.post("/upload")
def upload_document(
    request: Request,
    course_id: int = Form(...),
    file: UploadFile = File(...),
    title: str = Form(...),
    db: Session = Depends(get_db)
):
    user = current_user(request, db)

    if not user or user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")

    course = db.query(Course).filter(Course.id == course_id).first()

    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    safe_name = file.filename.replace("/", "_").replace("\\", "_")
    file_path = os.path.join(UPLOAD_DIR, safe_name)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    text = extract_text_from_file(file_path)
    chunks = chunk_text(text)

    doc = Document(
        course_id=course.id,
        title=title,
        filename=safe_name,
        uploaded_by=user.id
    )

    db.add(doc)
    db.flush()

    for i, chunk in enumerate(chunks):
        db.add(
            DocumentChunk(
                document_id=doc.id,
                course_id=course.id,
                chunk_text=chunk,
                chunk_index=i
            )
        )

    db.commit()

    return RedirectResponse("/admin", status_code=303)


@app.post("/api/chat")
async def general_chat_api(
    request: Request,
    db: Session = Depends(get_db)
):
    user = current_user(request, db)

    if not user:
        return JSONResponse(
            {"error": "Not logged in"},
            status_code=401
        )

    data = await request.json()
    question = data.get("question", "").strip()

    if not question:
        return JSONResponse(
            {"error": "Question is empty"},
            status_code=400
        )

    answer = ask_general_lmstudio(question)

    history = ChatHistory(
        user_id=user.id,
        course_id=None,
        question=question,
        answer=answer,
        source_context=None
    )

    db.add(history)
    db.commit()

    return {
        "answer": answer,
        "sources": []
    }


@app.post("/api/courses/{course_id}/chat")
async def course_chat_api(
    course_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    user = current_user(request, db)

    if not user:
        return JSONResponse(
            {"error": "Not logged in"},
            status_code=401
        )

    course = db.query(Course).filter(Course.id == course_id).first()

    if not course:
        return JSONResponse(
            {"error": "Course not found"},
            status_code=404
        )

    data = await request.json()
    question = data.get("question", "").strip()

    if not question:
        return JSONResponse(
            {"error": "Question is empty"},
            status_code=400
        )

    chunks = find_relevant_chunks(db, question, course_id=course.id)
    context = "\n\n---\n\n".join(chunks)

    answer = ask_course_lmstudio(question, context)

    history = ChatHistory(
        user_id=user.id,
        course_id=course.id,
        question=question,
        answer=answer,
        source_context=context
    )

    db.add(history)
    db.commit()

    return {
        "answer": answer,
        "sources": chunks
    }


@app.get("/courses/{course_id}")
def course_detail_page(
    course_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    user = current_user(request, db)

    if not user:
        return RedirectResponse("/login")

    course = db.query(Course).filter(Course.id == course_id).first()

    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    documents = (
        db.query(Document)
        .filter(Document.course_id == course.id)
        .order_by(Document.created_at.desc())
        .all()
    )

    return templates.TemplateResponse(
        "course_detail.html",
        {
            "request": request,
            "user": user,
            "course": course,
            "documents": documents
        }
    )


@app.get("/courses/{course_id}/summary")
def course_summary_page(
    course_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    user = current_user(request, db)

    if not user:
        return RedirectResponse("/login")

    course = db.query(Course).filter(Course.id == course_id).first()

    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    return templates.TemplateResponse(
        "summary.html",
        {
            "request": request,
            "user": user,
            "course": course,
            "summary": None,
            "language": "English"
        }
    )


@app.post("/courses/{course_id}/summary")
def generate_course_summary(
    course_id: int,
    request: Request,
    language: str = Form("English"),
    db: Session = Depends(get_db)
):
    user = current_user(request, db)

    if not user:
        return RedirectResponse("/login")

    course = db.query(Course).filter(Course.id == course_id).first()

    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    context = get_course_context(db, course_id=course.id)

    if not context.strip():
        summary = "No course documents have been uploaded yet."
    else:
        summary = summarize_course_lmstudio(context, language=language)

    return templates.TemplateResponse(
        "summary.html",
        {
            "request": request,
            "user": user,
            "course": course,
            "summary": summary,
            "language": language
        }
    )


@app.get("/courses/{course_id}/documents/{document_id}/summary")
def document_summary_page(
    course_id: int,
    document_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    user = current_user(request, db)

    if not user:
        return RedirectResponse("/login")

    course = db.query(Course).filter(Course.id == course_id).first()

    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    document = (
        db.query(Document)
        .filter(Document.id == document_id, Document.course_id == course.id)
        .first()
    )

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    return templates.TemplateResponse(
        "document_summary.html",
        {
            "request": request,
            "user": user,
            "course": course,
            "document": document,
            "summary": None,
            "language": "English",
            "from_cache": False
        }
    )


@app.post("/courses/{course_id}/documents/{document_id}/summary")
def generate_document_summary(
    course_id: int,
    document_id: int,
    request: Request,
    language: str = Form("English"),
    regenerate: str = Form("0"),
    db: Session = Depends(get_db)
):
    user = current_user(request, db)

    if not user:
        return RedirectResponse("/login")

    course = db.query(Course).filter(Course.id == course_id).first()

    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    document = (
        db.query(Document)
        .filter(Document.id == document_id, Document.course_id == course.id)
        .first()
    )

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    language_map = {
        "English": "English",
        "Vietnamese": "Vietnamese",
        "Traditional Chinese": "Traditional Chinese zh-TW",
        "Traditional Chinese zh-TW": "Traditional Chinese zh-TW",
    }

    language = language_map.get(language, "English")

    print("Selected summary language:", language)
    print("Regenerate summary:", regenerate)

    cached_summary = (
        db.query(DocumentSummary)
        .filter(
            DocumentSummary.document_id == document.id,
            DocumentSummary.language == language
        )
        .first()
    )

    if cached_summary and regenerate != "1":
        return templates.TemplateResponse(
            "document_summary.html",
            {
                "request": request,
                "user": user,
                "course": course,
                "document": document,
                "summary": cached_summary.summary_text,
                "language": language,
                "from_cache": True
            }
        )

    context = get_document_context(db, document_id=document.id)

    if not context.strip():
        summary = "No document content is available."
    else:
        summary = summarize_course_lmstudio(
            context=context,
            language=language
        )

    if cached_summary:
        cached_summary.summary_text = summary
    else:
        new_summary = DocumentSummary(
            document_id=document.id,
            language=language,
            summary_text=summary
        )
        db.add(new_summary)

    db.commit()

    return templates.TemplateResponse(
        "document_summary.html",
        {
            "request": request,
            "user": user,
            "course": course,
            "document": document,
            "summary": summary,
            "language": language,
            "from_cache": False
        }
    )


@app.get("/courses/{course_id}/documents/{document_id}/quiz")
def document_quiz_page(
    course_id: int,
    document_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    user = current_user(request, db)

    if not user:
        return RedirectResponse("/login")

    course = db.query(Course).filter(Course.id == course_id).first()

    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    document = (
        db.query(Document)
        .filter(Document.id == document_id, Document.course_id == course.id)
        .first()
    )

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    return templates.TemplateResponse(
        "document_quiz.html",
        {
            "request": request,
            "user": user,
            "course": course,
            "document": document,
            "quiz": None,
            "language": "English",
            "question_count": 5,
            "from_cache": False
        }
    )


@app.post("/courses/{course_id}/documents/{document_id}/quiz")
def generate_document_quiz(
    course_id: int,
    document_id: int,
    request: Request,
    language: str = Form("English"),
    question_count: int = Form(5),
    regenerate: str = Form("0"),
    db: Session = Depends(get_db)
):
    user = current_user(request, db)

    if not user:
        return RedirectResponse("/login")

    course = db.query(Course).filter(Course.id == course_id).first()

    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    document = (
        db.query(Document)
        .filter(Document.id == document_id, Document.course_id == course.id)
        .first()
    )

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    language_map = {
        "English": "English",
        "Vietnamese": "Vietnamese",
        "Traditional Chinese": "Traditional Chinese zh-TW",
        "Traditional Chinese zh-TW": "Traditional Chinese zh-TW",
    }

    language = language_map.get(language, "English")

    if question_count < 1:
        question_count = 1

    if question_count > 10:
        question_count = 10

    print("Selected quiz language:", language)
    print("Quiz question count:", question_count)
    print("Regenerate quiz:", regenerate)

    cached_quiz = (
        db.query(DocumentQuiz)
        .filter(
            DocumentQuiz.document_id == document.id,
            DocumentQuiz.language == language,
            DocumentQuiz.question_count == question_count
        )
        .first()
    )

    if cached_quiz and regenerate != "1":
        return templates.TemplateResponse(
            "document_quiz.html",
            {
                "request": request,
                "user": user,
                "course": course,
                "document": document,
                "quiz": cached_quiz.quiz_text,
                "language": language,
                "question_count": question_count,
                "from_cache": True
            }
        )

    context = get_document_context(db, document_id=document.id)

    if not context.strip():
        quiz = "No document content is available."
    else:
        quiz = generate_quiz_lmstudio(
            context=context,
            language=language,
            question_count=question_count
        )

    if cached_quiz:
        cached_quiz.quiz_text = quiz
    else:
        new_quiz = DocumentQuiz(
            document_id=document.id,
            language=language,
            question_count=question_count,
            quiz_text=quiz
        )
        db.add(new_quiz)

    db.commit()

    return templates.TemplateResponse(
        "document_quiz.html",
        {
            "request": request,
            "user": user,
            "course": course,
            "document": document,
            "quiz": quiz,
            "language": language,
            "question_count": question_count,
            "from_cache": False
        }
    )


@app.get("/history")
def history_page(request: Request, db: Session = Depends(get_db)):
    user = current_user(request, db)

    if not user:
        return RedirectResponse("/login")

    items = (
        db.query(ChatHistory)
        .filter(ChatHistory.user_id == user.id)
        .order_by(ChatHistory.created_at.desc())
        .limit(30)
        .all()
    )

    # Convert UTC time to Taiwan time UTC+8 for display
    for item in items:
        item.display_time = item.created_at + timedelta(hours=8)

    return templates.TemplateResponse(
        "history.html",
        {
            "request": request,
            "user": user,
            "items": items
        }
    )