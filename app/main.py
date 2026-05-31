import os
import shutil

from fastapi import FastAPI, Request, Depends, Form, UploadFile, File, HTTPException
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from starlette.middleware.sessions import SessionMiddleware

from app.config import SECRET_KEY, UPLOAD_DIR
from app.database import Base, engine, get_db, SessionLocal
from app.models import User, Document, DocumentChunk, ChatHistory
from app.auth import verify_password, create_demo_users
from app.document_utils import extract_text_from_file, chunk_text, find_relevant_chunks
from app.ollama_client import ask_ollama


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
def home(request: Request, db: Session = Depends(get_db)):
    user = current_user(request, db)

    if not user:
        return RedirectResponse("/login")

    return templates.TemplateResponse(
        "chat.html",
        {
            "request": request,
            "user": user
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


@app.get("/admin")
def admin_page(request: Request, db: Session = Depends(get_db)):
    user = current_user(request, db)

    if not user or user.role != "admin":
        return RedirectResponse("/login")

    documents = db.query(Document).order_by(Document.created_at.desc()).all()

    return templates.TemplateResponse(
        "admin.html",
        {
            "request": request,
            "user": user,
            "documents": documents
        }
    )


@app.post("/upload")
def upload_document(
    request: Request,
    file: UploadFile = File(...),
    title: str = Form(...),
    db: Session = Depends(get_db)
):
    user = current_user(request, db)

    if not user or user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")

    safe_name = file.filename.replace("/", "_").replace("\\", "_")
    file_path = os.path.join(UPLOAD_DIR, safe_name)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    text = extract_text_from_file(file_path)
    chunks = chunk_text(text)

    doc = Document(
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
                chunk_text=chunk,
                chunk_index=i
            )
        )

    db.commit()

    return RedirectResponse("/admin", status_code=303)


@app.post("/api/chat")
async def chat_api(
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

    chunks = find_relevant_chunks(db, question)
    context = "\n\n---\n\n".join(chunks)

    answer = ask_ollama(question, context)

    history = ChatHistory(
        user_id=user.id,
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

    return templates.TemplateResponse(
        "history.html",
        {
            "request": request,
            "user": user,
            "items": items
        }
    )