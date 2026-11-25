import subprocess
from pathlib import Path
from datetime import datetime

print("=== BUOC 93.33: XOA 30 PHONG DEMO AI ===")

backup_dir = Path("backups")
backup_dir.mkdir(exist_ok=True)

backup_file = backup_dir / (
    "tronhanh123_before_delete_demo_"
    + datetime.now().strftime("%Y%m%d_%H%M%S")
    + ".sql"
)

# Sao luu database
with backup_file.open("wb") as f:
    result = subprocess.run(
        [
            "docker", "exec", "postgres_db",
            "pg_dump",
            "-U", "postgres",
            "-d", "tronhanh123",
        ],
        stdout=f,
        stderr=subprocess.PIPE,
    )

if result.returncode != 0:
    backup_file.unlink(missing_ok=True)
    raise SystemExit(
        "Sao luu that bai: "
        + result.stderr.decode(errors="replace")
    )

print("Da sao luu:", backup_file)

sql = """
BEGIN;

DO $$
DECLARE
    demo_count integer;
BEGIN
    SELECT COUNT(*)
    INTO demo_count
    FROM public.rooms
    WHERE title LIKE '[DEMO-AI-89-%';

    IF demo_count <> 30 THEN
        RAISE EXCEPTION
        'Du kien 30 phong demo, nhung tim thay %',
        demo_count;
    END IF;
END
$$;

DELETE FROM public.favorite_rooms
WHERE room_id IN (
    SELECT id
    FROM public.rooms
    WHERE title LIKE '[DEMO-AI-89-%'
);

DELETE FROM public.rooms
WHERE title LIKE '[DEMO-AI-89-%';

COMMIT;

SELECT
    COUNT(*) AS total_rooms,
    COUNT(*) FILTER (
        WHERE status = 'da_duyet'
    ) AS approved_rooms,
    COUNT(*) FILTER (
        WHERE title LIKE '[DEMO-AI-89-%'
    ) AS remaining_demo
FROM public.rooms;
"""

result = subprocess.run(
    [
        "docker", "exec", "-i", "postgres_db",
        "psql",
        "-v", "ON_ERROR_STOP=1",
        "-U", "postgres",
        "-d", "tronhanh123",
    ],
    input=sql,
    text=True,
    capture_output=True,
)

print(result.stdout)

if result.returncode != 0:
    print(result.stderr)
    raise SystemExit("Xoa demo that bai. Kiem tra thong bao tren.")

print("=== HOAN THANH BUOC 93.33 ===")
