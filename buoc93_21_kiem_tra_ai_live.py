from pathlib import Path

path = Path("backend/routers/ai_live.py")

lines = path.read_text(
    encoding="utf-8-sig",
    errors="replace"
).splitlines()

print("=== BUOC 93.21: KIEM TRA AI LIVE ===")

ranges = [
    (1, 115),
    (340, 460),
]

for start, end in ranges:
    print(f"\n=== DONG {start} - {end} ===")

    for number in range(start, min(end, len(lines)) + 1):
        print(f"{number:4}: {lines[number - 1]}")

print("\n=== KET THUC ===")
