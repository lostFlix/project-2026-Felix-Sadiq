# clean_data.py
# What this does: takes the newest raw price file, throws out what we
# don't need, makes prices comparable (CHF per kg / per litre / per piece)
# and saves a clean file the app can use.
# Run it from the project folder:  python src/clean_data.py

import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"


# ---------- 1) load the newest raw file ----------
# glob finds all files that match the pattern, sorted() puts them in
# date order, [-1] = the last one = the newest
all_files = sorted(RAW.glob("staples_*.csv"))
newest = all_files[-1]
print("using:", newest.name)

df = pd.read_csv(newest)
print("raw shape:", df.shape)


# ---------- 2) keep only normal supermarkets ----------
# prodega, topcc, aligro are wholesalers (big packs, not for students)
# ottos and denner are out too, we only compare the big 4
STORES = ["aldi", "lidl", "coop", "migros"]
df = df[df["store"].isin(STORES)]


# ---------- 3) throw out stuff that is not food ----------
# toilet paper, kitchen roll and alcohol have nothing to do with lunch
NOT_FOOD = [
    "toilet-paper", "paper-towels",
    "b-absolut", "b-alpenbitter", "b-aperol", "b-baileys", "b-moet",
    "b-freixenet", "b-jager", "b-corona", "b-feldschl",
]
# ~ means "not", so: keep every row whose id is NOT in the list
df = df[~df["commodity_id"].isin(NOT_FOOD)]


# ---------- 4) drop prices we can't trust or can't compare ----------
# estimate == 1 means Skrimpers guessed the price -> we don't want guesses
df = df[df["estimate"] == 0]

# without a unit price (ppu) we can't compare -> drop those rows
df = df.dropna(subset=["ppu"])


# ---------- 5) make prices comparable ----------
# the data gives price per 100g or per 100ml -> we want per kg / per litre
# (that's easier to read). eggs are per piece, they stay like that.
df = df.copy()  # copy so pandas doesn't complain when we add columns
df["price_per_unit"] = df["ppu"]
df["unit"] = "piece"

per_100g = df["ppu_unit"] == "100g"
per_100ml = df["ppu_unit"] == "100ml"

df.loc[per_100g, "price_per_unit"] = df.loc[per_100g, "ppu"] * 10
df.loc[per_100g, "unit"] = "kg"
df.loc[per_100ml, "price_per_unit"] = df.loc[per_100ml, "ppu"] * 10
df.loc[per_100ml, "unit"] = "l"

df["price_per_unit"] = df["price_per_unit"].round(2)


# ---------- 6) nicer names + only the columns we need ----------
df = df.rename(columns={"commodity_id": "food_id", "commodity_en": "food"})
df = df[["date", "food_id", "food", "tier", "store", "product", "brand",
         "pack", "price_chf", "price_per_unit", "unit", "promo"]]


# ---------- 7) quick checks + save ----------
print("clean shape:", df.shape)
print(df["store"].value_counts())
print("missing values per column:")
print(df.isna().sum())

out_path = PROCESSED / "prices_clean.csv"
df.to_csv(out_path, index=False)
print("saved to", out_path)
