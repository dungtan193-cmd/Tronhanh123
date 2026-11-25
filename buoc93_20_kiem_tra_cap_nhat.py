from pathlib import Path

root = Path("backend")

keywords = [
    "is_current",
    "updated_at",
    "backgroundtasks",
    "threading",
    "training",
    "da_duyet",
]

print("=== BUOC 93.20: KIEM TRA CO CHE CAP NHAT ===")

for path in sorted(root.rglob("*.py")):
    if "__pycache__" in path.parts:
        continue

    try:
        lines = path.read_text(
            encoding="utf-8-sig",
            errors="replace"
        ).splitlines()
    except OSError:
        continue

    matches = []

    for number, line in enumerate(lines, 1):
        if any(word in line.lower() for word in keywords):
            matches.append((number, line.strip()))

    if matches:
        print(f"\nFILE: {path}")

        for number, line in matches[:12]:
            print(f"  {number}: {line[:150]}")

print("\n=== HOAN THANH ===")
