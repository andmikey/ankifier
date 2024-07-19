import streamlit as st
import pandas as pd
import sys

sys.path.append("../")

from ankifier.ankifier import Ankifier


st.write("# Import vocabulary")

data = st.file_uploader("Upload a vocab file:", type=["csv", "txt"])

if data:
    data_df = pd.read_csv(data, sep="|")
    data_df.columns = ["Word"]
    edited_df = st.data_editor(
        data_df, hide_index=True, num_rows="dynamic", use_container_width=True
    )

    clicked = st.button("Generate cards")

    if clicked:
        ankifier = Ankifier(
            st.session_state["config"],
            st.session_state["language_config_file"],
            st.session_state["language"],
            test_mode=True,
        )

        with st.spinner("Translating"):
            ankifier.parse_contents(edited_df)

            st.session_state["translations"] = ankifier.get_cards_df()
            st.session_state["additional_outputs"] = ankifier.get_additional_outputs_df()

        st.success("Generated translations! Go to Editor or Related pages for more.")