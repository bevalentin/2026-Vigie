from passlib.context import CryptContext
from typing import Optional
from app.models.domain import Owner, UserRole
from app.database import get_session
from sqlmodel import select

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def authenticate_user(email: str, password: str) -> Optional[Owner]:
    with next(get_session()) as session:
        statement = select(Owner).where(Owner.email == email)
        owner = session.exec(statement).first()
        if not owner:
            return None
        if not owner.password_hash:
            return None
        if verify_password(password, owner.password_hash):
            return owner
    return None
