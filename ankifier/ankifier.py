import deepl
import pandas as pd
import spacy
import streamlit as st
import utils
import yaml
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError

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
        st.session_state["language_anki_deck"] = config["language_configs"][language][
            "anki_deck"
        ]
        st.session_state["language_anki_card_type"] = config["language_configs"][
            language
        ]["card_type"]

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
        data_df = pd.read_csv(
            data, sep="|", header=None, names=["Word", "Translation"], dtype=str
        )

        # Force coercion to str
        data_df["Translation"] = data_df["Translation"].fillna("")

        st.write(f"Found {data_df.shape[0]} entries")

        edited_df = st.data_editor(
            data_df, hide_index=True, num_rows="dynamic", use_container_width=True
        )

        clicked = st.button("Generate cards")

        if clicked:
            with st.spinner("Translating"):
                bar = st.progress(0)
                cards, additional, generated_nothing = utils.parse_df_to_cards(
                    edited_df.drop_duplicates(ignore_index=True), bar
                )
                bar.empty()

                st.session_state["generated_cards"] = pd.DataFrame(
                    cards,
                    columns=[
                        "Front",
                        "Back",
                        "Part-of-speech",
                        "Base form",
                        "Audio link",
                    ],
                ).drop_duplicates(ignore_index=True)

                st.session_state["additional_outputs"] = pd.DataFrame(
                    additional, columns=["Source", "Entry"]
                ).drop_duplicates(subset=["Entry"], ignore_index=True)

                st.session_state["generated_nothing"] = pd.DataFrame(
                    generated_nothing, columns=["Source"]
                ).drop_duplicates(ignore_index=True)

            st.success(
                f"Generated: \n{st.session_state['generated_cards'].shape[0]} cards, "
                + f"{st.session_state['additional_outputs'].shape[0]} related entries.\n"
                + f"{st.session_state['generated_nothing'].shape[0]} entries did not generate any cards."
            )

with edit_cards:
    choice = st.radio("Choose an option:", ["Use import", "Upload existing file"])
    if choice == "Use import":
        if "generated_cards" in st.session_state:
            cards = st.session_state["generated_cards"]
            st.write(f"Generated {cards.shape[0]} cards")
            edited_df = st.data_editor(
                cards,
                hide_index=True,
                num_rows="dynamic",
                use_container_width=True,
            )
    else:
        data = st.file_uploader("Upload a file to edit:", type=["csv", "txt"])

        if data:
            data_df = pd.read_csv(data, sep=",")
            data_df.columns = [
                "Front",
                "Back",
                "Part-of-speech",
                "Base form",
                "Audio link",
            ]
            edited_df = st.data_editor(
                data_df, hide_index=True, num_rows="dynamic", use_container_width=True
            )

    clicked = st.button("Write cards to Anki")
    if clicked:
        with st.spinner("Writing to Anki"):
            errors = utils.write_df_to_anki(
                edited_df,
                st.session_state["language_anki_deck"],
                st.session_state["language_anki_card_type"],
            )
        count_errors = len(errors)
        count_written = edited_df.shape[0] - count_errors
        st.success(f"Wrote {count_written} cards to Anki")

with look_up_cards:
    search = st.text_input("Enter word to look up", key="lookup")

    if search:
        with st.spinner("Searching"):
            output = utils.look_up_word(
                st.session_state["mongo_coll"], utils.strip_stress_marks(search)
            )

        # Track how many entries we've seen to generate unique keys for the text_input field
        i = 0

        for entry in output:
            pos = entry["pos"]
            fields = st.session_state["language_config"].get(
                entry["pos"], st.session_state["language_config"]["default"]
            )
            st.write("Word has part of speech:")
            st.write(pos)
            st.write("Your jq filter is: ")
            st.write(fields)
            st.write("With your jq filter:")
            front_contents = utils.retrieve_fields(entry, fields["front"])
            back_contents = utils.retrieve_fields(entry, fields["back"])
            audio = utils.get_audio(entry)
            pos = utils.retrieve_fields(entry, ".pos")[0]
            base = utils.retrieve_fields(entry, ".word")

            card = utils.create_card_from_contents(
                front_contents, back_contents, base, pos, audio
            )

            st.write("Front: ")
            st.write(front_contents)
            st.write("Back: ")
            st.write(back_contents)
            st.write("Audio field: ")
            st.write(audio)
            st.write("Part of speech: ")
            st.write(pos)

            # Write single card to Anki
            clicked = st.button("Write card to Anki")
            if clicked:
                with st.spinner("Adding to Anki"):
                    card_contents = {
                        "Front": card.front,
                        "Back": card.back,
                        "Base form": card.base,
                        "Part-of-speech": card.pos,
                        "Audio link": card.audio,
                    }
                    response = utils.write_card(
                        st.session_state["language_anki_deck"],
                        st.session_state["language_anki_card_type"],
                        card_contents,
                    )
                if response["error"]:
                    st.error(f"Error with {base}, {response['error']}")
                else:
                    st.success("Wrote card to Anki")

            custom = st.text_input(
                "Add a custom jq filter: ", key=f"custom_jq_{pos}_{i}"
            )
            if custom:
                st.write("With your custom jq filter:")
                st.write(utils.retrieve_fields(entry, custom))

            st.write("Output JSON:")
            st.json(entry, expanded=False)
            st.divider()
            i += 1

with related_cards:
    if "additional_outputs" in st.session_state:
        cards = st.session_state["additional_outputs"]
        st.write(f"Generated {cards.shape[0]} additional cards")
        edited_df = st.data_editor(
            cards,
            hide_index=True,
            num_rows="dynamic",
            use_container_width=True,
        )

    if "generated_nothing" in st.session_state:
        generated_nothing = st.session_state["generated_nothing"]
        st.write(f"{generated_nothing.shape[0]} entries did not generate any cards")
        edited_df = st.data_editor(
            generated_nothing,
            hide_index=True,
            num_rows="dynamic",
            use_container_width=True,
        )
