"""Testlar uchun alohida vaqtinchalik baza (ishchi bazaga tegmaydi)."""
import os
import tempfile

_tmp = tempfile.mkdtemp(prefix="mxk_test_")
os.environ["MEBELIX_DB_URL"] = os.environ.get("MEBELIX_TEST_DB_URL", f"sqlite:///{_tmp}/test.db")
os.environ.pop("MES_WEBHOOK_URL", None)
os.environ.pop("MEBELIX_AUTH_REQUIRED", None)
os.environ.pop("MEBELIX_JWT_SECRET", None)

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402

KRAVAT = [  # (uid, L, W, qty) — 14 detal, 19 dona
    (1, 748, 1468, 1), (2, 200, 1468, 2), (3, 154, 748, 1), (4, 154, 1052, 1),
    (5, 50, 1052, 2), (6, 480, 800, 1), (7, 154, 400, 2), (8, 100, 1452, 1),
    (9, 470, 800, 1), (10, 900, 800, 1), (11, 500, 1452, 1), (12, 116, 552, 1),
    (13, 100, 350, 2), (14, 100, 503, 2),
]


@pytest.fixture(scope="session")
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture()
def kravat(client):
    """Loyiha: EL kromka + CS (LDSP) + 14 detal; qaytaradi (pid, cs_id, el_id)."""
    p = client.post("/api/projects", json={"name": "Detskiy kravat"}).json()
    pid = p["id"]
    p = client.post(f"/api/projects/{pid}/operations", json={"type": "EL", "code": "KP-1/19", "name": "PVC 1-19"}).json()
    el_id = p["operations"][-1]["id"]
    p = client.post(f"/api/projects/{pid}/operations", json={"type": "CS", "code": "LDSP16", "name": "LDSP BELI"}).json()
    cs_id = p["operations"][-1]["id"]
    parts = [dict(name=f"Panel{u}", length=L, width=W, qty=q) for u, L, W, q in KRAVAT]
    parts[5].update(edge_top={"op_id": el_id}, edge_bottom={"op_id": el_id})
    client.post(f"/api/projects/{pid}/operations/{cs_id}/parts", json=parts)
    return pid, cs_id, el_id
