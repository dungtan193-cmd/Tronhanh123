import subprocess

sql = """
SELECT
    COUNT(*) FILTER (
        WHERE status = 'da_duyet'
    ) AS approved_total,

    COUNT(*) FILTER (
        WHERE status = 'da_duyet'
          AND title LIKE '[DEMO-AI-89-%'
    ) AS demo_total,

    COUNT(*) FILTER (
        WHERE status = 'da_duyet'
          AND title NOT LIKE '[DEMO-AI-89-%'
    ) AS real_total,

    COUNT(*) FILTER (
        WHERE status = 'da_duyet'
          AND title NOT LIKE '[DEMO-AI-89-%'
          AND price > 0
          AND area > 0
          AND latitude BETWEEN -90 AND 90
          AND longitude BETWEEN -180 AND 180
    ) AS real_gis_total

FROM public.rooms;
"""

print("=== BUOC 93.28: KIEM TRA DU LIEU AI ===")

result = subprocess.run(
    [
        "docker", "exec", "postgres_db",
        "psql", "-U", "postgres",
        "-d", "tronhanh123",
        "-c", sql
    ],
    text=True,
    capture_output=True
)

print(result.stdout)

if result.returncode != 0:
    print(result.stderr)

print("=== KET THUC ===")
