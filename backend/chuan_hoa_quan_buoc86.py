from pathlib import Path
import pandas as pd
import unicodedata

DATA = Path("D:/baicuoiki/data")
INPUT = DATA / "rooms_clean.csv"
OUTPUT = DATA / "rooms_clean_normalized.csv"

df = pd.read_csv(INPUT, encoding="utf-8-sig")

def fix_text(value):
    if pd.isna(value):
        return "Khong xac dinh"

    text = str(value).strip()

    # Sua chuoi UTF-8 bi doc nham thanh CP437/CP850
    for encoding in ["cp850", "cp437", "latin1"]:
        try:
            repaired = text.encode(encoding).decode("utf-8")
            if repaired != text:
                text = repaired
                break
        except (UnicodeError, ValueError):
            pass

    return unicodedata.normalize("NFC", text)

def normalize_district(value):
    name = fix_text(value)
    key = name.casefold()

    if key == "bắc từ liêm":
        return "Bắc Từ Liêm"
    if key == "thanh xuân":
        return "Thanh Xuân"

    return name

df["district"] = df["district"].apply(normalize_district)

df.to_csv(OUTPUT, index=False, encoding="utf-8-sig")

print("HOAN THANH")
print("So phong:", len(df))
print("So quan:", df["district"].nunique())

print("\nThong ke:")
print(
    df.groupby("district")["price"]
    .agg(["count", "mean", "median"])
    .to_string()
)

print("\nDa luu:", OUTPUT)
