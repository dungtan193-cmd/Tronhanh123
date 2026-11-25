from pathlib import Path
import shutil

path = Path("backend/routers/ai_live.py")
backup = Path("backend/routers/ai_live_before_89_7.py.bak")

content = path.read_text(encoding="utf-8-sig")
shutil.copy2(path, backup)

# Thêm hàm chuẩn hóa tên quận
anchor = "def prepare_features(rooms):"

normalize_function = '''
def normalize_district(value):
    """
    Chuẩn hóa tên quận để tránh tạo đặc trưng trùng lặp.
    Không thay đổi dữ liệu gốc trong PostgreSQL.
    """
    import unicodedata

    text = unicodedata.normalize("NFC", str(value or ""))
    text = " ".join(text.strip().split())

    mapping = {
        "cầu giấy": "Cầu Giấy",
        "đống đa": "Đống Đa",
        "thanh xuân": "Thanh Xuân",
        "hai bà trưng": "Hai Bà Trưng",
        "nam từ liêm": "Nam Từ Liêm",
        "bắc từ liêm": "Bắc Từ Liêm",
        "hoàng mai": "Hoàng Mai",
        "long biên": "Long Biên",
        "hà đông": "Hà Đông",
        "ba đình": "Ba Đình",
        "tây hồ": "Tây Hồ",
        "hoàn kiếm": "Hoàn Kiếm",
        "thanh trì": "Thanh Trì",
        "gia lâm": "Gia Lâm",
        "đông anh": "Đông Anh",
    }

    key = text.casefold()

    for prefix in ("quận ", "huyện ", "q. ", "q.", "h. ", "h."):
        if key.startswith(prefix):
            key = key[len(prefix):].strip()
            break

    return mapping.get(key, text or "Chưa xác định")


'''

if "def normalize_district(value):" not in content:
    if anchor not in content:
        raise RuntimeError("Không tìm thấy hàm prepare_features")

    content = content.replace(
        anchor,
        normalize_function + anchor,
        1
    )

# Chỉ thay đổi cách tạo đặc trưng AI
old = '''    df = pd.DataFrame(rooms)

    # Không dùng ID để dự đoán giá.
    X = pd.get_dummies('''

new = '''    df = pd.DataFrame(rooms)

    # Chuẩn hóa tên quận trước khi mã hóa One-Hot.
    df["district"] = df["district"].apply(normalize_district)

    # Không dùng ID để dự đoán giá.
    X = pd.get_dummies('''

if old in content:
    content = content.replace(old, new, 1)
elif 'df["district"] = df["district"].apply(normalize_district)' not in content:
    raise RuntimeError("Không tìm thấy vị trí chuẩn hóa dữ liệu")

# Tăng phiên bản để cache AI nhận biết thay đổi logic xử lý.
old = '''    return hashlib.sha256(raw.encode("utf-8")).hexdigest()'''

new = '''    return hashlib.sha256(
        ("ai-version-89.7|" + raw).encode("utf-8")
    ).hexdigest()'''

if old in content:
    content = content.replace(old, new, 1)
elif '"ai-version-89.7|" + raw' not in content:
    raise RuntimeError("Không tìm thấy hàm fingerprint")

path.write_text(content, encoding="utf-8")

print("DA CHUAN HOA TEN QUAN CHO AI")
print("Backup:", backup)
