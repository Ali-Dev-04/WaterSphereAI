"""Complaints: citizens file/track own; admins update status + see all."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import models, schemas
from app.auth import get_current_user, require_admin
from app.database import get_db

router = APIRouter(tags=["complaints"])


@router.post("/api/complaints", response_model=schemas.ComplaintOut, status_code=201)
def create(body: schemas.ComplaintIn, user=Depends(get_current_user),
           db: Session = Depends(get_db)):
    if user.role != "admin" and user.ward_id != body.ward_id:
        raise HTTPException(403, "citizens may only file for their own ward")
    if not db.query(models.Ward).filter_by(ward_id=body.ward_id).first():
        raise HTTPException(404, f"unknown ward {body.ward_id}")
    c = models.Complaint(user_id=user.id, ward_id=body.ward_id, type=body.type)
    db.add(c)
    db.commit()
    db.refresh(c)
    return schemas.ComplaintOut(id=c.id, user_id=c.user_id, ward_id=c.ward_id,
                                type=c.type, status=c.status, created_at=c.created_at)


@router.get("/api/complaints", response_model=list[schemas.ComplaintOut])
def listing(user=Depends(get_current_user), db: Session = Depends(get_db)):
    q = db.query(models.Complaint).order_by(models.Complaint.id.desc())
    if user.role != "admin":
        q = q.filter_by(user_id=user.id)
    return [schemas.ComplaintOut(id=c.id, user_id=c.user_id, ward_id=c.ward_id,
                                 type=c.type, status=c.status, created_at=c.created_at)
            for c in q.limit(500).all()]


@router.patch("/api/complaints/{cid}", response_model=schemas.ComplaintOut)
def set_status(cid: int, body: schemas.StatusIn,
               admin=Depends(require_admin), db: Session = Depends(get_db)):
    _ = admin
    c = db.query(models.Complaint).filter_by(id=cid).first()
    if not c:
        raise HTTPException(404, "complaint not found")
    c.status = body.status
    db.commit()
    db.refresh(c)
    return schemas.ComplaintOut(id=c.id, user_id=c.user_id, ward_id=c.ward_id,
                                type=c.type, status=c.status, created_at=c.created_at)
