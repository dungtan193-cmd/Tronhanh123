import requests
import time

URL = "http://localhost:8000/api/ai/live/status"

print("=== BUOC 93.19: KIEM TRA AI ===")

for i in range(1, 5):
    try:
        response = requests.get(
            URL,
            params={"_check": i},
            timeout=30,
            headers={"Cache-Control": "no-cache"}
        )

        response.raise_for_status()
        data = response.json()

        print(f"\nLan kiem tra {i}")
        print("Status:", data.get("status"))
        print("Is current:", data.get("is_current"))
        print("Updated at:", data.get("updated_at"))
        print("Error:", data.get("error"))
        print("Result available:", data.get("result") is not None)

        if data.get("status") == "ready" and data.get("is_current"):
            print("\nAI da co ket qua moi nhat.")
            break

    except Exception as exc:
        print("Loi:", exc)

    if i < 4:
        time.sleep(10)

print("\n=== KET THUC ===")
