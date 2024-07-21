import pandas as pd
import yaml

import streamlit as st

st.set_page_config(page_title="Ankifier")

settings, import_cards, edit_cards, look_up_cards, related_cards = st.tabs(
    ["Settings", "Import cards", "Edit cards", "Look up", "Related cards"]
)

with settings:
    uploaded = st.file_uploader(
        "Upload settings file", type="yaml", accept_multiple_files=False
    )

    if uploaded:
        config = yaml.safe_load(uploaded)
        st.session_state["config"] = config

        languages = config["language_configs"].keys()
        st.session_state["language"] = st.selectbox("Choose language", languages)

with import_cards:
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
                st.session_state["additional_outputs"] = (
                    ankifier.get_additional_outputs_df()
                )

            st.success(
                "Generated translations! Go to Editor or Related pages for more."
            )

with edit_cards:
    pass

with look_up_cards:
    pass

with related_cards:
    pass
