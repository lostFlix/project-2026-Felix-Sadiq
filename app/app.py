import streamlit as st
import pandas as pd
st.title("Zurich Food Price Finder")
df = pd.read_csv("data/processed/prices_clean.csv")
st.write("Food prices from Aldi, Lidl, Coop and Migros.")
st.dataframe(df)
