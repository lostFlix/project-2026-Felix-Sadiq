# Protein Lunch Finder

Final project, Data Analysis with Python (UZH, HS26) - Felix & Sadiq

Main question: where in Zurich do I get the cheapest protein for my lunch?
We compare Aldi, Lidl, Coop and Migros.

## Data

- `data/raw/products_raw.csv` - all search results from the 4 shop websites (41 search terms, 3365 rows, not changed)
- `data/raw/product_pages_nutrition.csv` - exact nutrition values from single product pages (Migros + Coop)
- `data/raw/first_dataset_56.csv` - our first small dataset, now only used for one joke row (dog food)
- `data/processed/products_clean.csv` - clean dataset, 1663 products

Prices were collected on 25.11.2026. Lidl and Aldi don't show nutrition values online,
so for them (and for most other products) we use reference values per product type
from the Swiss food composition database (BLV). Column `nutrition_source` shows where a value comes from.

To build the clean file again:

```
python src/build_products.py
```

## Plan (Felix' part)

- **Q1 protein price:** which shop and product gives protein the cheapest? -> `chf_per_100g_protein`
- **Q2 shop ranking:** same product type in all 4 shops, compared by `price_per_kg`
- **Q3 price cuts:** most protein per pack if the pack costs under 5 / 10 / 20 CHF
- **Q4 protein share of calories:** `protein_100g * 4 / kcal_100g`

Sadiq's questions: tbd

## App

```
streamlit run app/app.py
```
