import deepl
import pandas as pd
import spacy
import utils
import yaml
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError

import streamlit as st

st.set_page_config(page_title="Ankifier")

test_mode = st.toggle("Testing mode", value=True)

settings, import_cards, edit_cards, related_cards, look_up_cards = st.tabs(
    ["Settings", "Import cards", "Edit cards", "Additional outputs", "Look up"]
)

with settings:
    uploaded = st.file_uploader(
        "Upload settings file", type="yaml", accept_multiple_files=False
    )

    if uploaded:
        config = yaml.safe_load(uploaded)
        st.session_state["config"] = config

        languages = config["language_configs"].keys()
        language = st.selectbox("Choose language", languages)
        st.session_state["language"] = language

        # Set up global configs
        # Retrieve language-level config
        with open(config["language_configs"][language]["word_settings"]) as f:
            language_config = yaml.safe_load(f)
        st.session_state["language_config"] = language_config

        # SpaCy
        spacy_model = config["language_configs"][language]["spacy_model"]
        st.session_state["nlp"] = spacy.load(spacy_model)

        # Mongo
        mongo_client = MongoClient(serverSelectionTimeoutMS=1000)
        try:
            _ = mongo_client.is_mongos
        except ServerSelectionTimeoutError:
            st.warning("Can't connect to Mongo client. Is it running?")

        st.session_state["mongo_coll"] = mongo_client[
            config["ankifier_config"]["mongodb_name"]
        ][config["language_configs"][language]["wiktionary_collection"]]

        # Translator
        if test_mode:
            st.session_state["translator"] = utils.TestTranslator()
        else:
            st.session_state["translator"] = deepl.Translator(
                config["ankifier_config"]["deepl_api_key"]
            )


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
            with st.spinner("Translating"):
                cards, additional = utils.parse_df_to_cards(edited_df)
                st.session_state["generated_cards"] = pd.DataFrame(
                    cards, columns=["Front", "Back", "Part-of-speech"]
                )
                st.session_state["additional_outputs"] = pd.DataFrame(
                    additional, columns=["Source", "Entry"]
                )

            st.success(
                'Generated translations! Go to "Edit cards" to see generated cards '
                + 'or "Additional outputs" to see related words.'
            )

with edit_cards:
    if "generated_cards" in st.session_state:
        cards = st.session_state["generated_cards"]
        st.write(f"Generated {cards.shape[0]} cards")
        edited_df = st.data_editor(
            cards, hide_index=True, num_rows="dynamic", use_container_width=True
        )

with look_up_cards:
    search = st.text_input("Enter word to look up")

    if search:
        output = utils.look_up_word(st.session_state["mongo_coll"], search)
        for entry in output:
            st.json(entry)

with related_cards:
    if "additional_outputs" in st.session_state:
        cards = st.session_state["additional_outputs"]
        st.write(f"Generated {cards.shape[0]} additional cards")
        edited_df = st.data_editor(
            cards, hide_index=True, num_rows="dynamic", use_container_width=True
        )
