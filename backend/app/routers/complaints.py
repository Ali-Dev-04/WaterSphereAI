"""Complaints: citizens file/track own; admins update status + see all.

Guest reports (no account) come through POST /api/complaints/public — the only
unauthenticated write endpoint; it is rate-limited per IP and validates every
field server-side. Photos are stored with server-generated names in
settings.upload_dir and served to admins only via GET /api/complaints/{cid}/photo.
"""

import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app import models, schemas
from app.auth import get_current_user, require_admin
from app.config import settings
from app.database import get_db
from app.routers.auth import limiter

router = APIRouter(tags=["complaints"])

# Photo policy (clarified with the user 2026-10-25): mandatory, JPEG/PNG/WEBP ≤ 5 MB.
MAX_PHOTO_BYTES = 5 * 1024 * 1024
# Magic-byte allowlist: content sniffing, Content-Type headers are client-controlled.
MAGICS = (
    (b"\x89PNG\r\n\x1a\n", ".png"),
    (b"\xff\xd8\xff", ".jpg"),
)


def _sniff_ext(img: bytes) -> str:
    if len(img) >= 12 and img[:4] == b"RIFF" and img[8:12] == b"WEBP":
        return ".webp"
    for magic, ext in MAGICS:
        if img.startswith(magic):
            return ext
    raise HTTPException(415, "photo must be JPEG, PNG or WEBP")


def _save_photo(f: UploadFile) -> str | None:
    """Validate + persist a guest photo; returns the stored filename."""
    data = f.file.read(MAX_PHOTO_BYTES + 1)  # cap the in-memory read
    if len(data) > MAX_PHOTO_BYTES:
        raise HTTPException(413, f"photo exceeds {MAX_PHOTO_BYTES // (1024 * 1024)} MB")
    ext = _sniff_ext(data)
    out = Path(settings.upload_dir)
    out.mkdir(parents=True, exist_ok=True)
    name = uuid.uuid4().hex + ext
    (out / name).write_bytes(data)
    return name


def _clean(text: str, lo: int, hi: int, label: str) -> str:
    text = text.strip()
    if not (lo <= len(text) <= hi):
        raise HTTPException(422, f"{label} must be {lo}–{hi} characters")
    return text


def _out(c: models.Complaint) -> schemas.ComplaintOut:
    return schemas.ComplaintOut(
        id=c.id, user_id=c.user_id, ward_id=c.ward_id, type=c.type,
        status=c.status, created_at=c.created_at,
        reporter_name=c.reporter_name, address=c.address,
        description=c.description, has_photo=bool(c.photo_path))


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
    return _out(c)


@router.post("/api/complaints/public", response_model=schemas.ComplaintOut,
             status_code=201)
@limiter.limit("5/minute")  # per-IP anti-abuse; effectively also caps spam bursts
async def create_guest(request: Request,
                       ward_id: str = Form(...),
                       type: str = Form(...),
                       reporter_name: str = Form(...),
                       address: str = Form(...),
                       description: str = Form(...),
                       photo: UploadFile = File(...),
                       db: Session = Depends(get_db)):
    """Guest (no-account) incident report. Public by explicit design.
    Rate-limited per IP (5/min)."""
    name = _clean(reporter_name, 2, 120, "full name")
    addr = _clean(address, 5, 500, "incident address")
    desc = _clean(description, 10, 2000, "incident description")
    if not db.query(models.Ward).filter_by(ward_id=ward_id).first():
        raise HTTPException(404, f"unknown ward {ward_id}")
    photo_path = _save_photo(photo)
    c = models.Complaint(user_id=None, ward_id=ward_id, type=type,
                         reporter_name=name, address=addr, description=desc,
                         photo_path=photo_path)
    db.add(c)
    db.commit()
    db.refresh(c)
    return _out(c)


@router.get("/api/complaints", response_model=list[schemas.ComplaintOut])
def listing(user=Depends(get_current_user), db: Session = Depends(get_db)):
    q = db.query(models.Complaint).order_by(models.Complaint.id.desc())
    if user.role != "admin":
        q = q.filter_by(user_id=user.id)
    return [_out(c) for c in q.limit(500).all()]


@router.get("/api/complaints/{cid}/photo")
def photo(cid: int, admin=Depends(require_admin), db: Session = Depends(get_db)):
    """Incident photo — admins only; filename is server-generated, path is
    anchored to the upload dir (no traversal surface)."""
    _ = admin
    c = db.query(models.Complaint).filter_by(id=cid).first()
    if not c or not c.photo_path:
        raise HTTPException(404, "photo not found")
    up_dir = Path(settings.upload_dir).resolve()
    p = (up_dir / c.photo_path).resolve()
    if not p.is_relative_to(up_dir) or not p.is_file():
        raise HTTPException(404, "photo not found")
    mime = "image/jpeg" if p.suffix == ".jpg" else \
           "image/png" if p.suffix == ".png" else "image/webp"
    return FileResponse(p, media_type=mime)


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
    return _out(c)
