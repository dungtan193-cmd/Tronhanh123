from pathlib import Path
from datetime import datetime
import ast

path = Path("backend/routers/ai_live.py")
source = path.read_text(encoding="utf-8-sig")

marker = "# ===== BUOC 93.30: REAL AND DEMO AI ====="

if marker in source:
    print("Buoc 93.30 da duoc tich hop.")
    raise SystemExit(0)

required = [
    "def read_rooms():",
    "def fingerprint_rooms(rooms):",
    "def background_update(rooms, fingerprint):",
    "def ai_status():",
    "def predict_rent(",
    "prediction_cache = {",
]

missing = [x for x in required if x not in source]

if missing:
    raise SystemExit("Khong tim thay: " + ", ".join(missing))

ast.parse(source)

backup = path.with_name(
    "ai_live.backup_93_30_" +
    datetime.now().strftime("%Y%m%d_%H%M%S") +
    ".py"
)

# 1. Doc du lieu theo che do
source = source.replace(
    "def read_rooms():",
    """# ===== BUOC 93.30: REAL AND DEMO AI =====
from fastapi import Query as AIQuery

def read_rooms(mode="real"):

    if mode not in ("real", "demo"):
        raise ValueError("Che do AI khong hop le")
""",
    1
)

source = source.replace(
    """              AND area > 0
            ORDER BY id""",
    """              AND area > 0
              AND (
                  %s = 'demo'
                  OR title NOT LIKE '[DEMO-AI-89-%%'
              )
            ORDER BY id""",
    1
)

source = source.replace(
    'cursor.execute("""',
    'cursor.execute("""',
    1
)

old_query_end = '''            ORDER BY id
        """)'''

new_query_end = '''            ORDER BY id
        """, (mode,))'''

if old_query_end not in source:
    raise SystemExit("Khong tim thay cuoi SQL read_rooms")

source = source.replace(old_query_end, new_query_end, 1)

# 2. Tao bo nho rieng cho moi che do
old_state = '''state = {
    "status": "not_started",
    "fingerprint": None,
    "updated_at": None,
    "result": None,
    "error": None,
}'''

new_state = '''def new_ai_state():
    return {
        "status": "not_started",
        "fingerprint": None,
        "updated_at": None,
        "result": None,
        "error": None,
    }


states = {
    "real": new_ai_state(),
    "demo": new_ai_state(),
}

# Tuong thich voi code cu
state = states["real"]'''

if old_state not in source:
    raise SystemExit("Khong tim thay state AI")

source = source.replace(old_state, new_state, 1)

# 3. Background AI nhan che do
source = source.replace(
    "def background_update(rooms, fingerprint):",
    """def background_update(rooms, fingerprint, mode="real"):
    state = states[mode]""",
    1
)

# 4. API status
source = source.replace(
    'def ai_status():',
    '''def ai_status(mode: str = AIQuery(default="real", pattern="^(real|demo)$")):
    state = states[mode]''',
    1
)

source = source.replace(
    '''        rooms = read_rooms()
    except Exception:''',
    '''        rooms = read_rooms(mode)
    except Exception:''',
    1
)

old_submit = '''                background_update,
                rooms,
                current_fingerprint,
            )'''

new_submit = '''                background_update,
                rooms,
                current_fingerprint,
                mode,
            )'''

if old_submit not in source:
    raise SystemExit("Khong tim thay executor.submit")

source = source.replace(old_submit, new_submit, 1)

# Tra ve thong tin che do
old_status_return = '''    return {
        "status": status,
        "is_current": is_current,'''

new_status_return = '''    return {
        "mode": mode,
        "contains_demo_data": mode == "demo",
        "status": status,
        "is_current": is_current,'''

if old_status_return not in source:
    raise SystemExit("Khong tim thay response status")

source = source.replace(
    old_status_return,
    new_status_return,
    1
)

# 5. Auto AI chay che do real
source = source.replace(
    '''            ai_status()
        except Exception:''',
    '''            ai_status(mode="real")
        except Exception:''',
    1
)

# 6. API predict: them mode ma khong thay doi thuat toan
old_predict = '''    area: float = Query(gt=0, le=500),
):'''

new_predict = '''    area: float = Query(gt=0, le=500),
    mode: str = Query(default="real", pattern="^(real|demo)$"),
):'''

if old_predict not in source:
    raise SystemExit("Khong tim thay tham so predict")

source = source.replace(old_predict, new_predict, 1)

old_predict_rooms = '''    rooms = read_rooms()

    if len(rooms) < MIN_TRAINING_ROOMS:'''

new_predict_rooms = '''    rooms = read_rooms(mode)

    if len(rooms) < MIN_TRAINING_ROOMS:'''

if old_predict_rooms not in source:
    raise SystemExit("Khong tim thay read_rooms cua predict")

source = source.replace(
    old_predict_rooms,
    new_predict_rooms,
    1
)

# Fingerprint co che do de tranh dung nham model cache
old_predict_fp = '''    rooms = read_rooms(mode)

    if len(rooms) < MIN_TRAINING_ROOMS:'''

# Du lieu demo va real co fingerprint khac nhau do danh sach khac nhau.
# Cache predict duoc bao ve boi fingerprint cua du lieu.

# 7. Kiem tra cu phap va sao luu
ast.parse(source)

backup.write_text(
    path.read_text(encoding="utf-8-sig"),
    encoding="utf-8"
)

path.write_text(source, encoding="utf-8")

print("=== BUOC 93.30 HOAN THANH ===")
print("Backup:", backup)
print("Da tach AI real va demo.")
print("Khong thay doi database.")
