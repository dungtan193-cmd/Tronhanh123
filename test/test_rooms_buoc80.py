"""Bước 80: kiểm thử router phòng trọ, không truy cập PostgreSQL thật."""
from unittest.mock import MagicMock
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette.middleware.sessions import SessionMiddleware
import backend.routers.rooms as rooms


@pytest.fixture
def setup(monkeypatch):
    app = FastAPI()
    app.add_middleware(SessionMiddleware, secret_key='test-only-secret')
    app.include_router(rooms.router)
    db = MagicMock()
    cursor = db.cursor.return_value
    monkeypatch.setattr(rooms, 'ket_noi_db', lambda: db)
    return TestClient(app), db, cursor, monkeypatch


def valid_form():
    return dict(title='Phòng đẹp', address='Hà Nội', district='Cầu Giấy', price='2500000', area='25', description='Có cửa sổ')


def valid_json():
    return dict(title='Phòng đẹp', address='Hà Nội', district='Cầu Giấy', price=2500000, area=25, description='Có cửa sổ')


def test_khong_dang_nhap_khong_duoc_dang_tin(setup):
    client, db, _, _ = setup
    assert client.post('/api/rooms', data=valid_form()).status_code == 401
    db.assert_not_called()


def test_khong_dang_nhap_khong_duoc_sua_tin(setup):
    client, db, _, _ = setup
    assert client.put('/api/rooms/1', json=valid_json()).status_code == 401
    db.assert_not_called()


def test_khong_dang_nhap_khong_duoc_xoa_tin(setup):
    client, db, _, _ = setup
    assert client.delete('/api/rooms/1').status_code == 401
    db.assert_not_called()


def test_phan_trang_khong_hop_le(setup):
    client, db, _, _ = setup
    assert client.get('/api/rooms/paged?page=0').status_code == 422
    assert client.get('/api/rooms/paged?limit=101').status_code == 422
    db.assert_not_called()


def test_sap_xep_khong_hop_le(setup):
    client, db, _, _ = setup
    assert client.get('/api/rooms/paged?sort=unknown').status_code == 422
    db.assert_not_called()


def test_loc_gia_khong_hop_le(setup):
    client, db, _, _ = setup
    assert client.get('/api/rooms/paged?price_range=unknown').status_code == 422
    db.assert_not_called()


def test_gia_dien_tich_sai_khi_dang(setup):
    client, db, _, monkeypatch = setup
    monkeypatch.setattr(rooms, 'kiem_tra_tai_khoan_hoat_dong', lambda request: 1)
    for key, value in [('price', '0'), ('area', '0'), ('area', '301')]:
        data = valid_form()
        data[key] = value
        assert client.post('/api/rooms', data=data).status_code == 422
    db.assert_not_called()


def test_toa_do_thieu_mot_chieu(setup):
    client, db, _, monkeypatch = setup
    monkeypatch.setattr(rooms, 'kiem_tra_tai_khoan_hoat_dong', lambda request: 1)
    data = valid_form()
    data['latitude'] = '21.0'
    assert client.post('/api/rooms', data=data).status_code == 400
    db.assert_not_called()


def test_nguoi_thue_dang_tin_cho_duyet(setup):
    client, db, cursor, monkeypatch = setup
    monkeypatch.setattr(rooms, 'kiem_tra_tai_khoan_hoat_dong', lambda request: 1)
    cursor.fetchone.side_effect = [('nguoi_thue', True), (101,)]
    res = client.post('/api/rooms', data=valid_form())
    assert res.status_code == 200, res.text
    assert res.json()['room_status'] == 'cho_duyet'
    db.commit.assert_called_once()
    inserts = [call.args[1] for call in cursor.execute.call_args_list if 'INSERT INTO rooms' in call.args[0]]
    assert len(inserts) == 1 and inserts[0][8] == 'cho_duyet'


def test_admin_dang_tin_tu_duyet(setup):
    client, db, cursor, monkeypatch = setup
    monkeypatch.setattr(rooms, 'kiem_tra_tai_khoan_hoat_dong', lambda request: 1)
    cursor.fetchone.side_effect = [('quan_tri', True), (102,)]
    res = client.post('/api/rooms', data=valid_form())
    assert res.status_code == 200, res.text
    assert res.json()['room_status'] == 'da_duyet'
    db.commit.assert_called_once()


def test_khong_duoc_sua_tin_nguoi_khac(setup):
    client, db, cursor, monkeypatch = setup
    monkeypatch.setattr(rooms, 'kiem_tra_tai_khoan_hoat_dong', lambda request: 1)
    cursor.fetchone.return_value = (2, 'da_duyet')
    res = client.put('/api/rooms/5', json=valid_json())
    assert res.status_code == 403, res.text
    db.commit.assert_not_called()


def test_khong_duoc_xoa_tin_nguoi_khac(setup):
    client, db, cursor, monkeypatch = setup
    monkeypatch.setattr(rooms, 'kiem_tra_tai_khoan_hoat_dong', lambda request: 1)
    cursor.fetchone.return_value = (2,)
    res = client.delete('/api/rooms/5')
    assert res.status_code == 403, res.text
    db.commit.assert_not_called()


def test_sua_tin_cua_minh_phai_duyet_lai(setup):
    client, db, cursor, monkeypatch = setup
    monkeypatch.setattr(rooms, 'kiem_tra_tai_khoan_hoat_dong', lambda request: 1)
    cursor.fetchone.side_effect = [(1, 'da_duyet'), ('nguoi_thue',)]
    res = client.put('/api/rooms/5', json=valid_json())
    assert res.status_code == 200, res.text
    assert res.json()['room_status'] == 'cho_duyet'
    db.commit.assert_called_once()


def test_xoa_tin_cua_minh(setup):
    client, db, cursor, monkeypatch = setup
    monkeypatch.setattr(rooms, 'kiem_tra_tai_khoan_hoat_dong', lambda request: 1)
    cursor.fetchone.return_value = (1,)
    res = client.delete('/api/rooms/5')
    assert res.status_code == 200, res.text
    assert res.json()['room_id'] == 5
    db.commit.assert_called_once()
