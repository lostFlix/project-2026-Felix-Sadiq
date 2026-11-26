## Protein Lunch Finder

Final project, Data Analysis with Python (Felix & Sadiq)

Main question: where in Zurich do I get the cheapest protein for my lunchbreak at uni? 
We compare Aldi, Lidl, Coop and Migros

## Data
- `data/raw/products_raw.csv` --> all data from Aldi, Lidl, Migros and Coop
- `data/raw/product_pages_nutrition.csv`--> exact nutrition values from single product pages (Migros + Coop)-> at Aldi and Lidl we couldn't find reliable data
- `data/raw/first_dataset_56.csv`--> a fun dataset for a bad joke
- `data/processed/products_clean.csv`--> clean dataset, 1623 products

Prices of the products were collected on 25 November 2026
!!!Lidl and Aldi don't show nutrition values online so for them (for products without a product page) we use reference values per product type from the Swiss food composition database which we added a column `nutrition_source` to show the source of our data...

To build the clean file again:

```
python src/build_products.py
```

## Plan 

- **Q1 protein price:** which shop and product gives protein the cheapest? 
-> `chf_per_100g_protein` (I will add more categories to reduce error potential)
- **Q2 shop ranking:** same product type in all 4 shops, compared by `price_per_kg`
- **Q3 protein share of calories:** `protein_100g * 4 / kcal_100g` this isn't unique, so everyone or every fitness app or AI can answer this question but for me it's a gimmick which fits into this app and it's easy to do
- **Q4 hidden cheap gymbro foods:** ranking of the cheapest and leanest protein products in terms of kcal
- **Q5 plant protein vs. animal protein in terms of price**
- **Q6 organic vs non organic pricing on the "same" product** 
(tbd who will answer which question)

## App

```
streamlit run app/app.py
```
