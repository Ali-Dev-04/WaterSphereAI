"""Guest complaint endpoint: submission, validation, photo rules, RBAC.

Runs against in-memory SQLite with FastAPI dependency overrides — no live DB or
model loading. TestClient is used WITHOUT its context manager so the app
lifespan (heavy model startup) never runs. The per-IP limiter is disabled for
the suite and exercised explicitly in its own test to avoid cross-test bleed.
"""

import io
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import models
from app.auth import get_current_user
from app.config import settings
from app.database import get_db
from app.main import app
from app.routers.complaints import MAX_PHOTO_BYTES

PNG = b"\x89PNG\r\n\x1a\n" + b"fake-image-data" * 4
JPEG = b"\xff\xd8\xff\xe0" + b"junk" * 3
NOT_IMAGE = b"GIF89a plain text" * 2


@pytest.fixture()
def db():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False},
                           poolclass=StaticPool)  # one conn shared across threads
    models.Base.metadata.create_all(engine)
    s = sessionmaker(bind=engine, autoflush=False, autocommit=False)()
    app.dependency_overrides[get_db] = lambda: s
    yield s
    app.dependency_overrides.clear()


@pytest.fixture()
def client(db, tmp_path, monkeypatch):
    # settings were already instantiated at import — patch the attribute directly
    monkeypatch.setattr(settings, "upload_dir", str(tmp_path / "uploads"))
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(
        id=1, username="admin", role="admin", ward_id="A")
    app.state.limiter.enabled = False  # rate-limiting tested explicitly below
    return TestClient(app)


def seed_ward():
    s = app.dependency_overrides[get_db]()
    s.merge(models.Ward(ward_id="A", ward_name="Ward A", area_km2=6.46))
    s.commit()


def _post(c, ward="A", name="Test Reporter", photo=PNG):
    files = {"photo": ("p.png", io.BytesIO(photo), "image/png")} if photo else None
    return c.post("/api/complaints/public",
                  data={"ward_id": ward, "type": "leakage",
                        "reporter_name": name,
                        "address": "12 Marine Drive, near the pump house",
                        "description": "Major pipeline leak for three days, water is wasted."},
                  files=files)


def test_guest_submission_stored_with_ward_and_ref(client):
    seed_ward()
    r = _post(client)
    assert r.status_code == 201, r.text
    out = r.json()
    assert out["user_id"] is None
    assert out["ward_id"] == "A"
    assert out["reporter_name"] == "Test Reporter"
    assert out["has_photo"] is True
    assert out["type"] == "leakage"
    lst = client.get("/api/complaints").json()
    assert any(c["id"] == out["id"] and c["address"].startswith("12 Marine") for c in lst)


def test_photo_is_mandatory(client):
    seed_ward()
    assert _post(client, photo=None).status_code == 422


def test_unknown_ward_rejected(client):
    seed_ward()
    assert _post(client, ward="ZZ").status_code == 404


def test_field_length_validation(client):
    seed_ward()
    assert _post(client, name="A").status_code == 422  # name < 2 chars


def test_bad_magic_bytes_rejected(client):
    seed_ward()
    assert _post(client, photo=NOT_IMAGE).status_code == 415


def test_webp_accepted_and_stored(client, tmp_path):
    seed_ward()
    webp = b"RIFF" + b"\x00\x00\x00\x00" + b"WEBP" + b"vp8 " + b"x" * 20
    r = _post(client, photo=webp)
    assert r.status_code == 201, r.text
    files = list((tmp_path / "uploads").iterdir())
    assert len(files) == 1 and files[0].suffix == ".webp"


def test_jpeg_accepted_and_stored(client, tmp_path):
    seed_ward()
    r = _post(client, photo=JPEG)
    assert r.status_code == 201, r.text
    files = list((tmp_path / "uploads").iterdir())
    assert len(files) == 1 and files[0].suffix == ".jpg"


def test_oversized_photo_rejected(client):
    seed_ward()
    big = PNG + b"0" * MAX_PHOTO_BYTES
    assert _post(client, photo=big).status_code == 413


def test_photo_access_is_admin_only(client):
    seed_ward()
    cid = _post(client).json()["id"]
    app.dependency_overrides.pop(get_current_user, None)  # unauthenticated caller
    assert client.get(f"/api/complaints/{cid}/photo").status_code == 401
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(
        id=1, username="admin", role="admin", ward_id="A")
    got = client.get(f"/api/complaints/{cid}/photo")
    assert got.status_code == 200 and got.content[:8] == PNG[:8]


def test_citizen_cannot_see_guest_photo(client):
    seed_ward()
    cid = _post(client).json()["id"]
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(
        id=7, username="cit", role="citizen", ward_id="A")
    assert client.get(f"/api/complaints/{cid}/photo").status_code == 403


def test_existing_authenticated_flow_unaffected(client):
    seed_ward()
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(
        id=7, username="cit", role="citizen", ward_id="A")
    r = client.post("/api/complaints", json={"ward_id": "A", "type": "billing"})
    assert r.status_code == 201 and r.json()["reporter_name"] is None
    assert client.post("/api/complaints",
                       json={"ward_id": "B", "type": "billing"}).status_code == 403
    citizen_list = client.get("/api/complaints").json()
    assert all(c["user_id"] == 7 for c in citizen_list)  # guest rows not leaked
    # a guest report now exists alongside the citizen one
    guest = _post(client)
    assert guest.status_code == 201
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(
        id=1, username="admin", role="admin", ward_id="A")  # admin scope
    admin_list = client.get("/api/complaints").json()
    assert any(c["user_id"] is None for c in admin_list)  # guest visible to admin
    assert sum(c["user_id"] == 7 for c in admin_list) == 1  # citizen's still there


def test_rate_limited_after_burst(client):
    seed_ward()
    app.state.limiter.enabled = True
    app.state.limiter.reset()  # clean key storage for this test only
    codes = [_post(client).status_code for _ in range(6)]
    assert 429 in codes and all(c in (201, 429) for c in codes)
    app.state.limiter.reset()
    app.state.limiter.enabled = False
