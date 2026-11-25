"""Bước 79: test độc lập router auth, KHÔNG kết nối PostgreSQL thật.
Chạy từ thư mục gốc dự án: python -m pytest tests/test_auth_buoc79.py -v
"""
import importlib
import sys
import types

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette.middleware.sessions import SessionMiddleware


@pytest.fixture
def client(monkeypatch):
    # Import auth.py mà không cần kết nối database thật.
    # Các module database giả chỉ tồn tại trong phiên test.
    fake_db_auth = types.ModuleType('database.auth')
    fake_db_auth.dang_ky = lambda *args: (True, 'Đăng ký thành công')
    fake_db_auth.dang_nhap = lambda *args: (False, 'Sai thông tin đăng nhập', None)
    fake_db_conn = types.ModuleType('database.connection')
    fake_db_conn.ket_noi_db = lambda: None
    monkeypatch.setitem(sys.modules, 'database.auth', fake_db_auth)
    monkeypatch.setitem(sys.modules, 'database.connection', fake_db_conn)
    monkeypatch.delitem(sys.modules, 'backend.routers.auth', raising=False)
    auth = importlib.import_module('backend.routers.auth')
    app = FastAPI()
    app.add_middleware(SessionMiddleware, secret_key='test-only-secret-key')
    app.include_router(auth.router)
    with TestClient(app) as test_client:
        yield test_client, auth
    sys.modules.pop('backend.routers.auth', None)


def test_dang_ky_thanh_cong(client, monkeypatch):
    c, auth = client
    called = []
    monkeypatch.setattr(auth, 'dang_ky', lambda *args: (called.append(args) or True, 'OK'))
    r = c.post('/api/auth/register', json={
        'full_name': 'Nguyen Van A', 'username': 'user_a',
        'email': 'a@example.com', 'phone': '0900000000', 'password': '12345678'
    })
    assert r.status_code == 200
    assert r.json()['status'] == 'success'
    assert called[0][1] == 'user_a'


def test_dang_ky_thieu_truong(client):
    c, _ = client
    assert c.post('/api/auth/register', json={'username': 'a'}).status_code == 422


def test_dang_ky_trung_tai_khoan(client, monkeypatch):
    c, auth = client
    monkeypatch.setattr(auth, 'dang_ky', lambda *args: (False, 'Đã tồn tại'))
    r = c.post('/api/auth/register', json={
        'full_name': 'A', 'username': 'a', 'email': 'a@example.com',
        'phone': '123', 'password': '123456'
    })
    assert r.status_code == 400


def test_dang_nhap_sai(client):
    c, _ = client
    r = c.post('/api/auth/login', json={'username_email': 'wrong', 'password': 'wrong'})
    assert r.status_code == 401


def test_dang_nhap_va_dang_xuat(client, monkeypatch):
    c, auth = client
    monkeypatch.setattr(auth, 'dang_nhap', lambda *args: (
        True, 'OK', {'id': 10, 'username': 'demo', 'role': 'nguoi_thue'}
    ))
    r = c.post('/api/auth/login', json={'username_email': 'demo', 'password': '123456'})
    assert r.status_code == 200
    assert r.json()['user']['id'] == 10
    r = c.post('/api/auth/logout')
    assert r.status_code == 200
    assert r.json()['status'] == 'success'


def test_xem_ho_so_khi_chua_dang_nhap(client):
    c, _ = client
    assert c.get('/api/auth/me').status_code == 401


def test_sua_ho_so_khi_chua_dang_nhap(client):
    c, _ = client
    r = c.put('/api/auth/profile', json={
        'full_name': 'A', 'email': 'a@example.com', 'phone': ''
    })
    assert r.status_code == 401


def test_doi_mat_khau_khi_chua_dang_nhap(client):
    c, _ = client
    r = c.put('/api/auth/change-password', json={
        'old_password': 'old', 'new_password': 'newpassword'
    })
    assert r.status_code == 401


def test_thieu_du_lieu_dang_nhap(client):
    c, _ = client
    assert c.post('/api/auth/login', json={'password': 'x'}).status_code == 422
