"""JWT auth + RBAC. Deny by default; roles enforced server-side on every route."""

import datetime as dt

import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app import models
from app.config import settings
from app.database import get_db

bearer = HTTPBearer()


def hash_password(pw: str) -> str:
    return bcrypt.hashpw(pw.encode(), bcrypt.gensalt()).decode()


def verify_password(pw: str, hashed: str) -> bool:
    return bcrypt.checkpw(pw.encode(), hashed.encode())


def create_token(username: str) -> str:
    exp = dt.datetime.utcnow() + dt.timedelta(minutes=settings.jwt_expire_min)
    return jwt.encode({"sub": username, "exp": exp}, settings.jwt_secret,
                      algorithm=settings.jwt_algorithm)


def get_current_user(token=Depends(bearer), db: Session = Depends(get_db)) -> models.User:
    cred_exc = HTTPException(status.HTTP_401_UNAUTHORIZED, "invalid credentials")
    try:
        payload = jwt.decode(token.credentials, settings.jwt_secret,
                             algorithms=[settings.jwt_algorithm])
        username = payload.get("sub")
    except JWTError:
        raise cred_exc
    user = db.query(models.User).filter_by(username=username).first()
    if not user:
        raise cred_exc
    return user


def require_admin(user: models.User = Depends(get_current_user)) -> models.User:
    if user.role != "admin":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "admin only")
    return user


def ward_scope(user: models.User, ward_id: str | None) -> str | None:
    """Citizens are confined to their own ward; admins pass through."""
    if user.role == "admin":
        return ward_id
    return user.ward_id
