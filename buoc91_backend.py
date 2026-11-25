from pathlib import Path
import shutil

path = Path("backend/routers/ai_live.py")
backup = Path("backend/routers/ai_live_before_step91.py.bak")

content = path.read_text(encoding="utf-8-sig")
shutil.copy2(path, backup)

old = '''    return {
        "mae": round(float(mean_absolute_error(y, predictions)), 2),
        "rmse": round(
            float(np.sqrt(mean_squared_error(y, predictions))), 2
        ),
        "r2": round(float(r2_score(y, predictions)), 4),
        "evaluation": f"{folds}-fold cross-validation",
    }'''

new = '''    return {
        "mae": round(float(mean_absolute_error(y, predictions)), 2),
        "rmse": round(
            float(np.sqrt(mean_squared_error(y, predictions))), 2
        ),
        "r2": round(float(r2_score(y, predictions)), 4),
        "evaluation": f"{folds}-fold cross-validation",
        "actual_values": [
            round(float(v), 2) for v in y
        ],
        "predicted_values": [
            round(float(v), 2) for v in predictions
        ],
    }'''

if old not in content:
    if '"predicted_values":' not in content:
        raise RuntimeError("Không tìm thấy hàm evaluate_model dự kiến.")
else:
    content = content.replace(old, new, 1)

# Gắn ID phòng với từng dự đoán để biểu đồ xác định đúng phòng.
old2 = '''    results = {
        "knn": evaluate_model(knn, X, y),
        "random_forest": evaluate_model(rf, X, y),
    }'''

new2 = '''    results = {
        "knn": evaluate_model(knn, X, y),
        "random_forest": evaluate_model(rf, X, y),
    }

    room_ids = [int(room["id"]) for room in rooms]

    for metrics in results.values():
        metrics["room_ids"] = room_ids'''

if old2 not in content:
    if 'metrics["room_ids"] = room_ids' not in content:
        raise RuntimeError("Không tìm thấy phần đánh giá mô hình.")
else:
    content = content.replace(old2, new2, 1)

# Đổi phiên bản fingerprint để tự tính lại kết quả.
if '"ai-version-89.7|" + raw' in content:
    content = content.replace(
        '"ai-version-89.7|" + raw',
        '"ai-version-91|" + raw',
        1
    )
else:
    raise RuntimeError("Không tìm thấy phiên bản cache 89.7.")

path.write_text(content, encoding="utf-8")

print("Da bo sung du doan ngoai mau cho tung phong.")
print("Backup:", backup)
