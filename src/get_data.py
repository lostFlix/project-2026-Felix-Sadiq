# get_data.py
# What this does: downloads today's supermarket prices from Skrimpers
# and saves them as a csv in data/raw.
# Run it from the project folder:  python src/get_data.py
#
# Source: Skrimpers (skrimpers.com), open data, licence CC BY 4.0
# -> we are allowed to use it, but we have to name them (app + report)

import pandas as pd
from pathlib import Path

# project folder = one level above this file (src -> project)
ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"

URL = "https://skrimpers.com/data/open/staples-today.csv"

# pandas can read a csv directly from a link, no manual download needed
df = pd.read_csv(URL)

# the data has a date column -> we put the date in the file name,
# so every download gets its own file and we never overwrite old prices
day = df["date"][0]
out_path = RAW / f"staples_{day}.csv"

df.to_csv(out_path, index=False)

print(f"saved {len(df)} rows to {out_path}")
