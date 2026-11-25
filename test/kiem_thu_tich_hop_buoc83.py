"""Bước 83 - Kiểm thử API tích hợp Tronhanh123 (chỉ đọc dữ liệu).
Chạy: python kiem_thu_tich_hop_buoc83.py
Tùy chọn: TRONHANH_API=http://localhost:8000
          TRONHANH_USER=... TRONHANH_PASSWORD=... (để thử API có đăng nhập)
"""
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
import http.cookiejar

BASE = os.getenv('TRONHANH_API', 'http://localhost:8000').rstrip('/')
USER = os.getenv('TRONHANH_USER', '')
PASSWORD = os.getenv('TRONHANH_PASSWORD', '')
jar = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
results = []

def request(method, path, payload=None):
    data = json.dumps(payload).encode('utf-8') if payload is not None else None
    req = urllib.request.Request(BASE + path, data=data, method=method)
    if data is not None:
        req.add_header('Content-Type', 'application/json')
    try:
        with opener.open(req, timeout=10) as resp:
            raw = resp.read()
            return resp.status, json.loads(raw) if raw else {}
    except urllib.error.HTTPError as err:
        raw = err.read()
        try:
            obj = json.loads(raw)
        except (ValueError, UnicodeDecodeError):
            obj = {'detail': raw[:200].decode('utf-8', 'replace')}
        return err.code, obj

def check(name, path, validate, expected=(200,)):
    try:
        status, body = request('GET', path)
        if status not in expected:
            results.append(('FAIL', name, f'HTTP {status}: {str(body.get("detail", ""))[:110]}'))
            return body
        if status != 200:
            results.append(('SKIP', name, f'HTTP {status}: {str(body.get("detail", ""))[:110]}'))
            return body
        good, detail = validate(body)
        results.append(('PASS' if good else 'FAIL', name, detail))
        return body
    except (OSError, ValueError, TimeoutError) as err:
        results.append(('FAIL', name, str(err)[:140]))
        return {}

def is_list(b):
    return isinstance(b.get('data'), list), f'{len(b.get("data", []))} phòng' if isinstance(b.get('data'), list) else 'Thiếu data dạng danh sách'

def is_paged(b):
    good = isinstance(b.get('data'), list) and all(isinstance(b.get(k), int) for k in ('page', 'total', 'total_pages'))
    return good, f'trang={b.get("page")}, tổng={b.get("total")}, số trang={b.get("total_pages")}'

def is_stats(b):
    d = b.get('data') or {}
    good = isinstance(d, dict) and all(k in d for k in ('total_rooms', 'average_price', 'by_price', 'by_district'))
    return good, f'số phòng đã duyệt={d.get("total_rooms", "?")}'

def is_prediction(b):
    d = b.get('data') or {}
    good = isinstance(d, dict) and all(k in d for k in ('predicted_price', 'suggested_min_price', 'suggested_max_price', 'warnings'))
    return good, f'giá dự đoán={d.get("predicted_price", "?")} VNĐ'

print('KIỂM THỬ TÍCH HỢP TRONHANH123 - BƯỚC 83')
print('API:', BASE)
check('Máy chủ /api/health', '/api/health', lambda b: (b.get('status') == 'success', f'status={b.get("status")}'))
check('Danh sách phòng', '/api/rooms', is_list)
check('Phân trang mặc định', '/api/rooms/paged?page=1&limit=6&keyword=&district=&price_range=all&area_range=all&room_type=all&sort=new', is_paged)
check('Phân trang lọc giá', '/api/rooms/paged?page=1&limit=6&price_range=under3&area_range=all&room_type=all&sort=low', is_paged)
check('Thống kê phòng', '/api/rooms/stats', is_stats)
check('KNN dự đoán giá', '/api/rooms/predict-price?area=25&district=', is_prediction, expected=(200, 422))
check('KNN kiểm tra diện tích sai', '/api/rooms/predict-price?area=0', lambda b: (False, 'API phải từ chối diện tích sai'), expected=(422,))
# Đối với diện tích sai, 422 là kết quả mong đợi chứ không phải thiếu dữ liệu.
if results[-1][0] == 'SKIP' and 'HTTP 422' in results[-1][2]:
    results[-1] = ('PASS', 'KNN kiểm tra diện tích sai', 'Máy chủ trả HTTP 422 đúng như mong đợi')

if USER and PASSWORD:
    try:
        status, body = request('POST', '/api/auth/login', {'username_email': USER, 'password': PASSWORD})
        if status == 200:
            results.append(('PASS', 'Đăng nhập phiên', 'HTTP 200; cookie được quản lý trong bộ nhớ'))
            check('Thông tin tài khoản', '/api/auth/me', lambda b: (bool((b.get('user') or b.get('thong_tin') or b).get('id')), 'Có ID tài khoản'))
            check('Tin đăng của tôi', '/api/rooms/my', is_list)
            check('Phòng yêu thích', '/api/favorites', is_list)
            try:
                request('POST', '/api/auth/logout')
            except (OSError, ValueError):
                pass
        else:
            results.append(('FAIL', 'Đăng nhập phiên', f'HTTP {status}: {str(body.get("detail", ""))[:100]}'))
    except (OSError, ValueError, TimeoutError) as err:
        results.append(('FAIL', 'Đăng nhập phiên', str(err)[:140]))
else:
    results.append(('SKIP', 'API yêu cầu đăng nhập', 'Không khai báo TRONHANH_USER / TRONHANH_PASSWORD'))

print('\nKẾT QUẢ')
for state, name, detail in results:
    print(f'[{state:4}] {name}: {detail}')
passed = sum(x[0] == 'PASS' for x in results)
failed = sum(x[0] == 'FAIL' for x in results)
skipped = sum(x[0] == 'SKIP' for x in results)
print(f'\nTỔNG: {passed} PASS, {failed} FAIL, {skipped} SKIP')
print('Ghi chú: SKIP ở KNN có thể do chưa đủ 3 tin đã duyệt hợp lệ.')
sys.exit(1 if failed else 0)
