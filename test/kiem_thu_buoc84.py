"""Bước 84: kiểm thử tích hợp an toàn (không sửa dữ liệu).
Chạy tại D:\\baicuoiki: python test\\kiem_thu_buoc84.py
Có thể khai báo TRONHANH_USER và TRONHANH_PASSWORD để thử phiên đăng nhập.
Tùy chọn TRONHANH_API, TRONHANH_FRONTEND (mặc định localhost:8000, localhost:5173).
"""
import getpass
import http.cookiejar
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

API = os.getenv('TRONHANH_API', 'http://localhost:8000').rstrip('/')
FRONTEND = os.getenv('TRONHANH_FRONTEND', 'http://localhost:5173').rstrip('/')
USER = os.getenv('TRONHANH_USER', '').strip()
PASSWORD = os.getenv('TRONHANH_PASSWORD', '')
results = []
jar = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))

def call(method, path, payload=None, base=API):
    raw = json.dumps(payload).encode('utf-8') if payload is not None else None
    req = urllib.request.Request(base + path, data=raw, method=method)
    if raw is not None:
        req.add_header('Content-Type', 'application/json')
    try:
        with opener.open(req, timeout=12) as res:
            body = res.read(2_000_000)
            status = res.status
            content_type = res.headers.get('Content-Type', '')
    except urllib.error.HTTPError as e:
        status = e.code
        body = e.read(2_000_000)
        content_type = e.headers.get('Content-Type', '')
    if 'json' in content_type:
        try:
            return status, json.loads(body)
        except (ValueError, UnicodeDecodeError):
            return status, {'_invalid_json': True}
    return status, {'_html': body.decode('utf-8', 'replace')[:1000]}

def result(kind, name, message):
    results.append((kind, name, str(message)))

def check(name, method, path, predicate, base=API):
    try:
        status, data = call(method, path, base=base)
        ok, msg = predicate(status, data)
        result('PASS' if ok else 'FAIL', name, msg)
        return status, data
    except Exception as e:
        result('FAIL', name, f'{type(e).__name__}: {e}')
        return None, {}

def data_list(status, body):
    d = body.get('data') if isinstance(body, dict) else None
    return status == 200 and isinstance(d, list), f'HTTP {status}; {len(d)} mục' if isinstance(d, list) else f'HTTP {status}; thiếu data dạng danh sách'

def auth_required(status, body):
    return status in (401, 403), f'HTTP {status} (mong đợi 401/403 khi chưa đăng nhập)'

print('TRONHANH123 - KIỂM THỬ BƯỚC 84 (KHÔNG THAY ĐỔI DỮ LIỆU)')
print('Backend:', API, '| Frontend:', FRONTEND)
check('Backend hoạt động', 'GET', '/api/health', lambda s, b: (s == 200 and b.get('status') == 'success', f'HTTP {s}'))
check('Frontend Vite phục vụ trang', 'GET', '/', lambda s, b: (s == 200 and '<html' in b.get('_html', '').lower(), f'HTTP {s}; cần chạy npm run dev'), base=FRONTEND)
_, rooms = check('Danh sách phòng công khai', 'GET', '/api/rooms', data_list)
room_list = rooms.get('data', []) if isinstance(rooms, dict) else []
if room_list and isinstance(room_list[0], dict) and isinstance(room_list[0].get('id'), int):
    room_id = room_list[0]['id']
    check('Chi tiết phòng và ảnh', 'GET', f'/api/rooms/{room_id}', lambda s, b: (
        s == 200 and isinstance(b.get('data'), dict) and isinstance(b['data'].get('images'), list),
        f'HTTP {s}; phòng #{room_id}; images là danh sách: {isinstance((b.get("data") or {}).get("images"), list)}'))
    check('Phòng liên quan', 'GET', f'/api/rooms/{room_id}/related', data_list)
else:
    result('SKIP', 'Chi tiết phòng và phòng liên quan', 'Chưa có phòng công khai hợp lệ để thử')
check('Phân trang và tìm kiếm', 'GET', '/api/rooms/paged?page=1&limit=6&keyword=&district=&price_range=all&area_range=all&room_type=all&sort=new',
      lambda s, b: (s == 200 and isinstance(b.get('data'), list) and isinstance(b.get('total'), int), f'HTTP {s}; tổng={b.get("total")}'))
check('Thống kê phòng', 'GET', '/api/rooms/stats', lambda s, b: (s == 200 and isinstance(b.get('data'), dict) and 'total_rooms' in b['data'], f'HTTP {s}'))
check('KNN dự đoán giá', 'GET', '/api/rooms/predict-price?area=25&district=', lambda s, b: (
    s == 200 and isinstance(b.get('data'), dict) and isinstance(b['data'].get('predicted_price'), (int, float)),
    f'HTTP {s}; giá={((b.get("data") or {}).get("predicted_price"))}'))
check('Chặn truy cập tin của tôi khi chưa đăng nhập', 'GET', '/api/rooms/my', auth_required)
check('Chặn truy cập yêu thích khi chưa đăng nhập', 'GET', '/api/favorites', auth_required)
check('Chặn truy cập admin khi chưa đăng nhập', 'GET', '/api/admin/rooms/pending', auth_required)

if USER and not PASSWORD:
    PASSWORD = getpass.getpass('Mật khẩu tài khoản kiểm thử (không hiển thị): ')
if USER and PASSWORD:
    try:
        status, body = call('POST', '/api/auth/login', {'username_email': USER, 'password': PASSWORD})
        user = body.get('user') or body.get('thong_tin') or body.get('data') or {}
        if status == 200:
            result('PASS', 'Đăng nhập', f'HTTP {status}; cookie phiên: {len(jar)}')
            check('Phiên đăng nhập /auth/me', 'GET', '/api/auth/me', lambda s, b: (
                s == 200 and bool((b.get('user') or b.get('thong_tin') or b.get('data') or b).get('id')),
                f'HTTP {s}; có ID người dùng'))
            check('Danh sách tin của tôi', 'GET', '/api/rooms/my', data_list)
            check('Danh sách yêu thích', 'GET', '/api/favorites', data_list)
            if isinstance(user, dict) and user.get('role') == 'quan_tri':
                check('Admin xem tin chờ duyệt', 'GET', '/api/admin/rooms/pending', data_list)
                check('Admin xem tài khoản', 'GET', '/api/admin/users', data_list)
            else:
                check('Tài khoản thường bị chặn khỏi admin', 'GET', '/api/admin/rooms/pending', auth_required)
            # Không gọi logout vì có thể thay đổi trạng thái phiên; cookie chỉ tồn tại trong bộ nhớ chương trình.
        else:
            result('FAIL', 'Đăng nhập', f'HTTP {status}; {str(body.get("detail", ""))[:120]}')
    except Exception as e:
        result('FAIL', 'Đăng nhập', f'{type(e).__name__}: {e}')
else:
    result('SKIP', 'Các API sau đăng nhập', 'Chưa khai báo TRONHANH_USER / TRONHANH_PASSWORD')

print('\nKẾT QUẢ')
for kind, name, msg in results:
    print(f'[{kind}] {name}: {msg}')
counts = {k: sum(r[0] == k for r in results) for k in ('PASS', 'FAIL', 'SKIP')}
print(f'\nTỔNG: {counts["PASS"]} PASS, {counts["FAIL"]} FAIL, {counts["SKIP"]} SKIP')
print('Lưu ý: kiểm thử API không thay thế thao tác thủ công trên trình duyệt; chương trình không tạo/sửa/xóa dữ liệu.')
sys.exit(1 if counts['FAIL'] else 0)
