"""Auth routes: register / login / me."""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.orm import Session

from app import models, schemas
from app.auth import create_token, get_current_user, hash_password, verify_password
from app.database import get_db

router = APIRouter(prefix="/api/auth", tags=["auth"])
limiter = Limiter(key_func=get_remote_address)


@router.post("/register", response_model=schemas.UserOut, status_code=201)
def register(body: schemas.RegisterIn, db: Session = Depends(get_db)):
    if body.role == "admin":
        # Admin accounts are provisioned (seed/env), never self-registered.
        raise HTTPException(status.HTTP_403_FORBIDDEN, "admin accounts are provisioned")
    if db.query(models.User).filter_by(username=body.username).first():
        raise HTTPException(status.HTTP_409_CONFLICT, "username taken")
    if body.role == "citizen" and not body.ward_id:
        raise HTTPException(422, "citizens must provide ward_id")
    if body.ward_id and not db.query(models.Ward).filter_by(ward_id=body.ward_id).first():
        raise HTTPException(404, f"unknown ward {body.ward_id}")
    user = models.User(username=body.username, password_hash=hash_password(body.password),
                       role="citizen", ward_id=body.ward_id)
    db.add(user)
    db.commit()
    db.refresh(user)
    return schemas.UserOut(id=user.id, username=user.username, role=user.role,
                           ward_id=user.ward_id)


@router.post("/login", response_model=schemas.TokenOut)
@limiter.limit("10/minute")
def login(request: Request, body: schemas.LoginIn, db: Session = Depends(get_db)):
    user = db.query(models.User).filter_by(username=body.username).first()
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "invalid credentials")
    return schemas.TokenOut(access_token=create_token(user.username))


@router.get("/me", response_model=schemas.UserOut)
def me(user: models.User = Depends(get_current_user)):
    return schemas.UserOut(id=user.id, username=user.username, role=user.role,
                           ward_id=user.ward_id)
