from pathlib import Path
import ast

main_path = Path("backend/main.py")
ai_path = Path("backend/routers/ai_live.py")

main = main_path.read_text(encoding="utf-8-sig")
ai = ai_path.read_text(encoding="utf-8-sig")

ast.parse(main)
ast.parse(ai)

checks = {
    "FastAPI co lifespan": "lifespan=tronhanh_lifespan" in main,
    "Lifespan khoi dong AI": "start_auto_ai_refresh()" in main,
    "Lifespan dung AI": "stop_auto_ai_refresh()" in main,
    "AI co vong lap tu dong": "def _auto_ai_loop(" in ai,
    "AI co ham khoi dong": "def start_auto_ai_refresh(" in ai,
    "AI co ham dung": "def stop_auto_ai_refresh(" in ai,
    "AI co phat hien thay doi": "fingerprint_rooms(rooms)" in ai,
}

print("=== BUOC 93.25: KIEM TRA AUTO AI ===")

for name, passed in checks.items():
    print(f"{'OK' if passed else 'THIEU'} - {name}")

print()
if all(checks.values()):
    print("Cau truc Auto AI da duoc ket noi.")
    print("Can kiem thu thuc te khi du lieu thay doi.")
else:
    print("Phat hien thanh phan chua duoc ket noi.")
