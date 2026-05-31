from passlib.context import CryptContext
from sqlalchemy.orm import Session
from app.models import User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(password: str, password_hash: str) -> bool:
    return pwd_context.verify(password, password_hash)

def create_demo_users(db: Session):
    users = [
        ("admin", "admin123", "admin"),
        ("student", "student123", "student"),
    ]

    for username, password, role in users:
        existing = db.query(User).filter(User.username == username).first()

        if not existing:
            db.add(
                User(
                    username=username,
                    password_hash=hash_password(password),
                    role=role
                )
            )

    db.commit()