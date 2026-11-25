import streamlit as st
import pandas as pd
st.title("Protein Lunch Finder")
df = pd.read_csv("data/processed/products_clean.csv")
st.write("Food prices from Aldi, Lidl, Coop and Migros.")
st.dataframe(df)
