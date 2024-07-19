import streamlit as st
import pandas as pd


st.write("# Edit generated cards")

if "translations" in st.session_state:
    cards = st.session_state["translations"]

    edited_df = st.data_editor(
        cards, hide_index=True, num_rows="dynamic", use_container_width=True
    )
