# Analysis plan - Protein Lunch Finder

Felix & Sadiq, Data Analysis with Python (UZH, HS26). Last update: 25.11.2026

**Main question:** Where in Zurich do I get the cheapest protein for my lunch?
Shops: Aldi, Lidl, Coop, Migros. Currency: CHF. One row = one product.

We work in this order (like agreed with the lecturer on 24.11.):

1. Get the data -> raw CSV (done)
2. Clean it -> one processed CSV (done)
3. Write down the questions and how we answer each one (this file)
4. One analysis per question -> table + chart
5. Put the results on the website (Streamlit pages)

---

## 1. Data (done)

| Step | File | What happens |
|---|---|---|
| Scrape | `data/raw/products_raw.csv` | 41 search terms x 4 shop websites, 3365 search results, never changed after download |
| Nutrition | `data/raw/product_pages_nutrition.csv` | nutrition per 100 g from single Migros/Coop product pages (757 pages) |
| Nutrition | `data/raw/openfoodfacts_nutrition.csv` | 9 Lidl/Aldi products matched by hand to Open Food Facts |
| Clean | `src/build_products.py` | raw -> clean, can be run again and gives the same file |
| Result | `data/processed/products_clean.csv` | 1623 products, 28 columns |

How collected: browser on the normal shop websites, one page after the other, no blocking. Prices from 25.11.2026.

**Known limits (we say this in every result):**
- Lidl and Aldi don't show nutrition online. For them we mostly use reference values per product type (Swiss food database BLV). Column `nutrition_source` shows where each value comes from.
- So: **price questions** are fair for all 4 shops, **protein questions** compare shops fairly only for Migros vs Coop.
- Product types come from keywords in the product name, so a few rows can be wrong.
- Eggs: price per pack, weight assumed 60 g per egg (`egg_weight_assumed`).

## 2. Filters used in all questions

```python
protein_cats = ["milch", "tierisch", "pflanzlich", "high_protein"]
df = df[df["category"].isin(protein_cats)]   # only protein foods (1029 rows)
df = df[df["joke"] == False]                  # dog food row only on the page, not in the analysis
df = df[df["promo"] == False]                 # normal prices only (67 promo rows out)
df = df.dropna(subset=["protein_100g", "price_chf"])  # -> 962 rows left
```

Calculated columns (already in the clean file):

| Column | Formula |
|---|---|
| `price_per_kg` | `price_chf / package_g * 1000` |
| `protein_pack_g` | `protein_100g * package_g / 100` |
| `chf_per_100g_protein` | `price_chf / protein_pack_g * 100` |
| `protein_kcal_share` | `protein_100g * 4 / kcal_100g` (share of calories that come from protein) |
| `under_5/10/20` | `price_chf < 5 / 10 / 20` |

We use the **median** for group comparisons, because a few very expensive products would pull the mean up.

---

## 3. Questions

Owner: proposal, still to confirm with Sadiq.

### Q1 - Protein per franc *(Felix)*
**Question:** Which product and which shop gives me 100 g protein for the least money?
- Column: `chf_per_100g_protein` (lower = better)
- Method: `sort_values("chf_per_100g_protein")`, top 10 overall + best product per `product_type` (`groupby` + `idxmin` or `drop_duplicates`)
- Output: ranking table (with package size and shop) + bar chart top 10
- Note: dry lentils/beans win (price per dry weight, need cooking) -> show them, but also a ranking "ready to eat" without dry legumes
- Page: Ranking

### Q2 - Shop comparison *(Sadiq)*
**Question:** For the same product type, which shop is cheapest?
- Column: `price_per_kg` (real for all 4 shops)
- Filter: only product types sold in at least 3 shops (20 of 22 types)
- Method: `groupby(["product_type", "store"])["price_per_kg"].median()` -> table type x shop (`unstack` / `pivot_table`), count how often each shop is cheapest
- Output: heatmap or grouped bar chart, "cheapest shop" count
- Page: Shop comparison

### Q3 - Protein per calorie *(Felix)*
**Question:** Which products give the most protein for the fewest calories? (diet question)
- Column: `protein_kcal_share`
- Filter: `kcal_100g > 0`
- Method: `sort_values(ascending=False)`, top 10, median per `product_type`
- Output: ranking table + bar chart
- Page: Ranking

### Q4 - Cheap AND lean *(Felix)*
**Question:** Which products are good in Q1 and Q3 at the same time?
- Columns: `chf_per_100g_protein` (x) and `protein_kcal_share` (y)
- Method: scatter plot, colour = `category`; "winners" = in the cheapest 25 % (`quantile(0.25)`) **and** in the leanest 25 % (`quantile(0.75)` of `protein_kcal_share`), two boolean conditions with `&`. (Tested: median cut gives 222 winners, quartile cut 90.)
- Output: scatter plot + table of winners
- Page: Ranking

### Q5 - Animal vs plant protein *(Sadiq)*
**Question:** Is plant protein (tofu, lentils, meat substitutes) cheaper than meat, fish and dairy?
- Column: `chf_per_100g_protein`, grouped by `category` (and `vegan`)
- Method: `groupby("category")["chf_per_100g_protein"].median()`, also per `product_type`
- Output: box plot or bar chart per category
- Page: Comparisons

### Q6 - Organic premium *(Sadiq)*
**Question:** How much more do you pay for organic (Bio) protein?
- New column: `bio = df["product"].str.contains("bio", case=False)` (133 Bio products after the filters; Coop Naturaplan products also have "Bio" in the name). Check by hand that no non-organic product matches.
- Method: compare **inside the same product type** (otherwise we compare tofu with salmon): median `price_per_kg` Bio vs non-Bio per `product_type`, premium in % = `(bio / non_bio - 1) * 100`. Only types with at least 3 Bio and 3 non-Bio products (14 types).
- Output: bar chart premium in % per product type
- Note: tofu shows a negative premium, probably because almost all tofu is Bio and the few non-Bio ones are flavoured/smoked -> check by hand before we say anything
- Page: Comparisons

### Q7 - Best pack for my budget *(optional, open)*
**Question:** Most protein in one pack that costs under 5 / 10 / 20 CHF?
- Columns: `under_5/10/20`, `protein_pack_g`
- Method: filter by budget, `sort_values("protein_pack_g")`
- Output: 3 small tables or a slider on the website

---

## 4. Website: who builds what

We use Streamlit, one file per page in `app/pages/`. Each of us only edits his own files, so we never overwrite each other.

| File | What | Owner |
|---|---|---|
| `app/app.py` | frame, navigation between pages | Felix |
| `src/load_data.py` | reads the clean CSV and applies the filters from section 2, used by every page | Felix |
| `app/pages/home.py` | idea, data, limits | both |
| `app/pages/ranking.py` | Q1, Q3, Q4 (+ dog food joke row) | Felix |
| `app/pages/shops.py` | Q2 | Sadiq |
| `app/pages/comparisons.py` | Q5, Q6 | Sadiq |

All pages load the data with the same function, so both of us work with exactly the same 962 rows.

## 5. Design

Every page looks the same, so the website feels like one thing:

1. Title + the question in one sentence
2. Filters in the sidebar (shop, category) with `st.sidebar`
3. Result table (`st.dataframe`)
4. One chart
5. Takeaway: 1-2 sentences, what the result means
6. Small note on the data (source, limits)

Same colour for each shop on all charts. No extra design work, the content counts.

## 6. How we build it (we are beginners)

- Notebook first: every question starts in its own notebook (`notebooks/q1_protein_price.ipynb` etc.). We run it cell by cell and look at the output after every step.
- Only when the notebook works, we copy the lines into the page.
- Small versions, one commit each: v1 table -> v2 filter -> v3 chart -> v4 takeaway text.
- Commands from the course where possible (filtering, `groupby`, `sort_values`, `merge`, plots).
- Claude helps with code, but we go through every line and write the comments ourselves. Each of us must be able to explain the filters, cleaning and commands of his part (agreed with the lecturer on 24.11.).
- Git: `git pull` before starting, `git push` after every finished step.

## 7. How we check that it works and makes sense

Runs without errors:
- before every push: `streamlit run app/app.py` and click through every page
- after deploy: open the Streamlit Cloud link and check every page again
- fresh clone + `python src/build_products.py` gives the same clean file

Data makes sense:
- row count after the filters is 962
- no price <= 0, `protein_100g` between 0 and 100
- `protein_100g * 4` is not bigger than `kcal_100g` (else the nutrition values are wrong)
- look at the top 10 and bottom 10 of every ranking by hand: would a normal person agree?
- 3 random products per page: compare price with the shop website

Results make sense:
- we write the takeaway sentence for every chart. If we can't explain a result, it doesn't go on the page.
- strange results (like Bio tofu being cheaper) are checked by hand first
- Felix tests Sadiq's pages and Sadiq tests Felix' pages before 3.12.

## 8. Timeline

| Date | What |
|---|---|
| 25.11. | data cleaned, analysis plan written |
| 26.11. | git checkpoint: plan committed, owners confirmed |
| until 1.12. | analysis Q1-Q6 (one notebook per question), Felix: app frame + `load_data.py` |
| until 3.12. | pages in Streamlit, deploy, cross-testing |
| 4.12. | presentation |
| 10.12. | report |

## 9. Use of AI

Data collection (browser agent) and parts of the cleaning code were done with Claude, which the lecturer allowed. Questions, filters and decisions are ours, and we checked and can explain the code.
