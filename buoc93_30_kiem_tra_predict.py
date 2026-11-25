from pathlib import Path

path = Path("backend/routers/ai_live.py")
lines = path.read_text(
    encoding="utf-8-sig",
    errors="replace"
).splitlines()

print("=== BUOC 93.30: KIEM TRA API DU DOAN ===")

for number in range(433, len(lines) + 1):
    print(f"{number:4}: {lines[number - 1]}")

print("\n=== KET THUC ===")
