import json
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
import requests

from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    r2_score,
)
from sklearn.model_selection import KFold, cross_val_predict
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

API = "http://localhost:8000/api/ai/gis/research/features"
OUTPUT = Path("reports/ai_gis")
OUTPUT.mkdir(parents=True, exist_ok=True)

MIN_ROOMS = 30

GIS_COLUMNS = [
    "nearest_university_m",
    "bus_stops_1km",
    "schools_1km",
    "hospitals_1km",
    "parks_1km",
]

BASE_COLUMNS = ["district", "area"]
ALL_COLUMNS = BASE_COLUMNS + GIS_COLUMNS


def get_data():
    response = requests.get(
        API,
        params={"limit": 10000},
        timeout=120,
    )
    response.raise_for_status()
    return response.json()


def prepare_dataframe(payload):
    df = pd.DataFrame(payload.get("rooms", []))

    if df.empty:
        return df

    required = [
        "room_id",
        "district",
        "area",
        "price",
        *GIS_COLUMNS,
    ]

    missing = [
        column for column in required
        if column not in df.columns
    ]

    if missing:
        raise ValueError(
            "API thieu cot: " + ", ".join(missing)
        )

    numeric_columns = [
        "area",
        "price",
        *GIS_COLUMNS,
    ]

    for column in numeric_columns:
        df[column] = pd.to_numeric(
            df[column],
            errors="coerce",
        )

    df["district"] = (
        df["district"]
        .fillna("")
        .astype(str)
        .str.strip()
        .str.casefold()
    )

    df = df.drop_duplicates(
        subset=["room_id"],
        keep="first",
    )

    df = df[
        (df["price"] > 0)
        & (df["area"] > 0)
        & (df["district"] != "")
    ].copy()

    # Không tự tạo giá trị GIS khi thiếu.
    df = df.dropna(
        subset=ALL_COLUMNS + ["price"]
    )

    for column in GIS_COLUMNS:
        df = df[df[column] >= 0]

    return df.reset_index(drop=True)


def make_model(columns):
    numeric_columns = [
        column for column in columns
        if column != "district"
    ]

    preprocessor = ColumnTransformer(
        transformers=[
            (
                "district",
                OneHotEncoder(
                    handle_unknown="ignore"
                ),
                ["district"],
            ),
            (
                "numeric",
                SimpleImputer(
                    strategy="median"
                ),
                numeric_columns,
            ),
        ]
    )

    model = RandomForestRegressor(
        n_estimators=100,
        min_samples_leaf=2,
        random_state=42,
        n_jobs=1,
    )

    return Pipeline([
        ("preprocessor", preprocessor),
        ("model", model),
    ])


def evaluate(df, columns, cv):
    X = df[columns]
    y = df["price"].to_numpy()

    model = make_model(columns)

    predictions = cross_val_predict(
        model,
        X,
        y,
        cv=cv,
        n_jobs=1,
    )

    return {
        "mae": round(
            float(mean_absolute_error(y, predictions)), 2
        ),
        "rmse": round(
            float(np.sqrt(
                mean_squared_error(y, predictions)
            )), 2
        ),
        "r2": round(
            float(r2_score(y, predictions)), 4
        ),
        "predictions": predictions,
    }


def main():
    print("\n=== BUOC 93.7: AI + GIS ===")

    payload = get_data()
    df = prepare_dataframe(payload)

    print("So phong nghien cuu:", len(df))
    print("Nguong thu nghiem:", MIN_ROOMS)

    report = {
        "created_at": datetime.now().isoformat(),
        "source": API,
        "total_rooms": int(len(df)),
        "minimum_training_rooms": MIN_ROOMS,
        "status": "insufficient_data",
    }

    if df.empty:
        print("\nCHUA CO DU LIEU PHONG THUC TE.")
        print("Khong huan luyen mo hinh.")
        print("Khong tao du lieu gia lap.")

    else:
        clean_path = OUTPUT / "research_gis_clean.csv"

        df.to_csv(
            clean_path,
            index=False,
            encoding="utf-8-sig",
        )

        print("Da xuat CSV:", clean_path)

        print("\n=== KIEM TRA DU LIEU ===")
        print(
            df[
                ["area", "price", *GIS_COLUMNS]
            ].describe().to_string()
        )

        if len(df) < MIN_ROOMS:
            print("\nCHUA DU 30 PHONG THUC TE.")
            print("Tam thoi chua huan luyen AI + GIS.")

        else:
            print("\n=== CROSS VALIDATION ===")

            cv = KFold(
                n_splits=5,
                shuffle=True,
                random_state=42,
            )

            baseline = evaluate(
                df,
                BASE_COLUMNS,
                cv,
            )

            gis_model = evaluate(
                df,
                ALL_COLUMNS,
                cv,
            )

            print("\nRandom Forest co ban:")
            print(
                "MAE:", baseline["mae"],
                "RMSE:", baseline["rmse"],
                "R2:", baseline["r2"],
            )

            print("\nRandom Forest + GIS:")
            print(
                "MAE:", gis_model["mae"],
                "RMSE:", gis_model["rmse"],
                "R2:", gis_model["r2"],
            )

            y = df["price"].to_numpy()

            prediction_df = pd.DataFrame({
                "room_id": df["room_id"],
                "actual_price": y,
                "baseline_prediction": (
                    baseline["predictions"]
                ),
                "gis_prediction": (
                    gis_model["predictions"]
                ),
            })

            prediction_path = (
                OUTPUT / "comparison_predictions.csv"
            )

            prediction_df.to_csv(
                prediction_path,
                index=False,
                encoding="utf-8-sig",
            )

            report["status"] = "evaluated"
            report["baseline"] = {
                key: baseline[key]
                for key in ("mae", "rmse", "r2")
            }
            report["gis_model"] = {
                key: gis_model[key]
                for key in ("mae", "rmse", "r2")
            }

            report["gis_improved_mae"] = (
                gis_model["mae"] < baseline["mae"]
            )

            print("\nDa xuat:", prediction_path)

    report_path = OUTPUT / "evaluation_report.json"

    report_path.write_text(
        json.dumps(
            report,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    print("\nBao cao:", report_path)
    print("Trang thai:", report["status"])


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print("\nLOI:", exc)
        sys.exit(1)
