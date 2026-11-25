"""Bước 81: test admin và favorites không kết nối PostgreSQL thật.
Chạy: python -m pytest test/test_admin_favorites_buoc81.py -v
"""
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette.middleware.sessions import SessionMiddleware

from backend.routers import admin, favorites


class FakeCursor:
    def __init__(self, results):
        self.results = iter(results)
        self.current = None
        self.queries = []
    def execute(self, sql, params=None):
        self.queries.append((sql, params))
        self.current = next(self.results, None)
    def fetchone(self):
        return self.current
    def fetchall(self):
        return self.current or []
    def close(self):
        pass


class FakeConnection:
    def __init__(self, results):
        self.cur = FakeCursor(results)
        self.commits = 0
        self.rollbacks = 0
    def cursor(self):
        return self.cur
    def commit(self):
        self.commits += 1
    def rollback(self):
        self.rollbacks += 1
    def close(self):
        pass


@pytest.fixture
def client():
    app = FastAPI()
    app.add_middleware(SessionMiddleware, secret_key='test-only-key')
    app.include_router(admin.router)
    app.include_router(favorites.router)
    with TestClient(app) as c:
        yield c


def fake_db(monkeypatch, module, results):
    conn = FakeConnection(results)
    monkeypatch.setattr(module, 'ket_noi_db', lambda: conn)
    return conn


def as_admin(monkeypatch):
    monkeypatch.setattr(admin, 'kiem_tra_admin', lambda request: 1)


def as_user(monkeypatch):
    monkeypatch.setattr(favorites, 'lay_user_id', lambda request: 2)


@pytest.mark.parametrize('url', [
    '/api/admin/rooms/pending', '/api/admin/users',
    '/api/favorites',
])
def test_chua_dang_nhap_bi_chan(client, url):
    assert client.get(url).status_code == 401


@pytest.mark.parametrize('url', [
    '/api/admin/rooms/7/approve', '/api/admin/rooms/7/reject',
    '/api/admin/users/7/lock', '/api/admin/users/7/unlock',
])
def test_chua_dang_nhap_khong_duoc_thao_tac_admin(client, url):
    assert client.put(url).status_code == 401


def test_nguoi_thue_khong_duoc_xem_admin(client, monkeypatch):
    # Không thay hàm kiểm tra quyền: giả lập phiên đăng nhập người thuê.
    from fastapi import Request
    # Test trực tiếp hàm kiểm tra quyền bằng request có session giả.
    scope = {'type': 'http', 'method': 'GET', 'path': '/', 'headers': [],
             'session': {'user_id': 2}}
    conn = fake_db(monkeypatch, admin, [('nguoi_thue', True)])
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as err:
        admin.kiem_tra_admin(Request(scope))
    assert err.value.status_code == 403
    assert conn.cur.queries


def test_admin_xem_tin_cho_duyet(client, monkeypatch):
    as_admin(monkeypatch)
    fake_db(monkeypatch, admin, [[]])
    r = client.get('/api/admin/rooms/pending')
    assert r.status_code == 200
    assert r.json()['data'] == []


def test_admin_duyet_tin(client, monkeypatch):
    as_admin(monkeypatch)
    conn = fake_db(monkeypatch, admin, [(7,)])
    r = client.put('/api/admin/rooms/7/approve')
    assert r.status_code == 200
    assert r.json()['room_id'] == 7
    assert conn.commits == 1
    assert "'da_duyet'" in conn.cur.queries[0][0]


def test_admin_tu_choi_tin(client, monkeypatch):
    as_admin(monkeypatch)
    conn = fake_db(monkeypatch, admin, [(7,)])
    r = client.put('/api/admin/rooms/7/reject')
    assert r.status_code == 200
    assert conn.commits == 1
    assert "'tu_choi'" in conn.cur.queries[0][0]


def test_khong_duyet_duoc_tin_khong_cho(client, monkeypatch):
    as_admin(monkeypatch)
    conn = fake_db(monkeypatch, admin, [None])
    assert client.put('/api/admin/rooms/7/approve').status_code == 404
    assert conn.rollbacks == 1


def test_admin_khong_duoc_tu_khoa(client, monkeypatch):
    as_admin(monkeypatch)
    assert client.put('/api/admin/users/1/lock').status_code == 400


def test_admin_khoa_tai_khoan(client, monkeypatch):
    as_admin(monkeypatch)
    conn = fake_db(monkeypatch, admin, [(2, 'nguoidung')])
    r = client.put('/api/admin/users/2/lock')
    assert r.status_code == 200
    assert r.json()['is_active'] is False
    assert conn.commits == 1


def test_admin_mo_khoa_tai_khoan(client, monkeypatch):
    as_admin(monkeypatch)
    conn = fake_db(monkeypatch, admin, [(2, 'nguoidung')])
    r = client.put('/api/admin/users/2/unlock')
    assert r.status_code == 200
    assert r.json()['is_active'] is True
    assert conn.commits == 1


def test_khong_luu_phong_chua_duyet(client, monkeypatch):
    as_user(monkeypatch)
    conn = fake_db(monkeypatch, favorites, [None])
    assert client.post('/api/favorites/7').status_code == 404
    assert conn.rollbacks == 1


def test_luu_phong_thanh_cong(client, monkeypatch):
    as_user(monkeypatch)
    conn = fake_db(monkeypatch, favorites, [(7,), (3,)])
    r = client.post('/api/favorites/7')
    assert r.status_code == 200
    assert r.json()['is_favorite'] is True
    assert conn.commits == 1


def test_luu_trung_phong(client, monkeypatch):
    as_user(monkeypatch)
    fake_db(monkeypatch, favorites, [(7,), None])
    r = client.post('/api/favorites/7')
    assert r.status_code == 200
    assert 'đã có' in r.json()['message']


def test_bo_luu_phong(client, monkeypatch):
    as_user(monkeypatch)
    conn = fake_db(monkeypatch, favorites, [(3,)])
    r = client.delete('/api/favorites/7')
    assert r.status_code == 200
    assert r.json()['is_favorite'] is False
    assert conn.commits == 1


def test_bo_luu_phong_chua_luu(client, monkeypatch):
    as_user(monkeypatch)
    fake_db(monkeypatch, favorites, [None])
    r = client.delete('/api/favorites/7')
    assert r.status_code == 200
    assert 'chưa có' in r.json()['message']


def test_danh_sach_yeu_thich_rong(client, monkeypatch):
    as_user(monkeypatch)
    fake_db(monkeypatch, favorites, [[]])
    r = client.get('/api/favorites')
    assert r.status_code == 200
    assert r.json()['total'] == 0
