import itertools
import logging
from typing import List, Tuple

import jq
from spacy import Language

import streamlit as st


class Card:
    def __init__(self, front: str, back: str, pos: str, root: str):
        self.front = front
        self.back = back
        self.pos = pos
        self.root = root

    def __str__(self):
        return f"{self.front}|{self.back}|{self.pos}|{self.root}"

    def __repr__(self):
        return self.__str__

    def __eq__(self, card):
        return (self.front == card.front) and (self.pos == card.pos)

    def as_tuple(self):
        return (self.front, self.back, self.pos, self.root)


class Word:
    def __init__(self, word: str, pos: str, config: dict, coll):
        self.word = word
        self.pos = pos
        self.config = config
        self.coll = coll
        self.examples = []
        self.related = []

    def retrieve_config(self, pos):
        # Return config for this POS
        return self.config.get(pos, self.config["default"])

    def generate_cards(self) -> List[Card]:
        entries = look_up_word(self.coll, self.word)

        cards_to_output = []

        for entry in entries:
            if entry is None:
                continue

            pos = entry["pos"]

            config = self.retrieve_config(pos)
            config_front = config["front"]
            config_back = config["back"]

            # Generate card just for this word
            root = retrieve_fields(entry, ".word")
            front_contents = retrieve_fields(entry, config_front)
            back_contents = retrieve_fields(entry, config_back)
            if front_contents is not None and back_contents is not None:
                front = ", ".join([x for x in front_contents if x])
                back = "<br>".join([x for x in back_contents if x])
                card = Card(front, back, pos, root)
                cards_to_output.append(card)

            # Optional: choose examples and output to another file
            examples = retrieve_fields(
                entry, "(.senses[].examples[]?) | (.text, .english) | select(. != null)"
            )
            if examples is not None:
                self.examples.extend(examples)

            # Optional: choose related words and output to another file
            related = retrieve_fields(entry, "(.related[]?.word)")
            if related is not None:
                self.related.extend(related)
            also_related = retrieve_fields(
                entry,
                "(.senses[] | .synonyms, .antonyms) | select(. != null)[] | .word",
            )
            if also_related is not None:
                self.related.extend(also_related)

        # Generate cards for related words
        return cards_to_output


class Phrase:
    def __init__(
        self, phrase: str, config: dict, spacy_pipeline: Language, translator, coll
    ):
        self.phrase = phrase
        self.config = config
        self.spacy = spacy_pipeline
        self.translator = translator
        self.coll = coll
        self.examples = []
        self.related = []

    def pre_process_phrase(self, phrase: str) -> List[Tuple[str, str]]:
        # Use SpaCy to extract lemmas
        processed = self.spacy(phrase)

        tokens = []
        for token in processed:
            lemma = token.lemma_
            pos = token.pos_
            detailed_pos = token.tag_
            tokens.append((lemma, pos, detailed_pos))

        return tokens

    def generate_cards(self) -> List[Card]:
        cards: List[Card] = []

        # Look up all the individual (lemmatized) words and generate cards for these
        tokens = self.pre_process_phrase(self.phrase)
        for lemma, pos, detailed_pos in tokens:
            if pos == "PROPN":
                lemma = lemma.capitalize()
            word = Word(lemma, pos, self.config, self.coll)
            cards_for_lemma = word.generate_cards()
            cards.extend(cards_for_lemma)
            self.examples.extend(word.examples)
            self.related.extend(word.related)

        # Translate the whole phrase
        if len(tokens) > 1:
            translation = self.translator.translate_text(self.phrase, target_lang="EN")
            overall_translation = Card(self.phrase, translation, "phrase", self.phrase)
            cards.append(overall_translation)

        logging.info(
            f"Generated {len(cards)} cards for {self.phrase}, "
            + f"{len(self.examples) + len(self.related)} additional cards"
        )
        return [c.as_tuple() for c in cards]

    def get_additional_outputs(self):
        return self.related + self.examples


def parse_df_to_cards(df, bar):
    # Takes DataFrame where each row is a word/phrase and outputs:
    # 1. Translated cards
    # 2. Additional cards which someone may want to add
    cards_to_add = []
    additional_outputs = []
    generated_nothing = []

    total_entries = df.shape[0]

    for idx, row in df.iterrows():
        progress = min(1, (idx + 1) / total_entries)
        bar.progress(progress)

        entry = row["Word"].strip()
        p = Phrase(
            entry,
            st.session_state["language_config"],
            st.session_state["nlp"],
            st.session_state["translator"],
            st.session_state["mongo_coll"],
        )

        cards = p.generate_cards()
        cards_to_add.extend(cards)
        # Examples, synonyms, antonyms, related words, etc
        additional = p.get_additional_outputs()
        additional_outputs.extend([(entry, out) for out in additional])

        if not cards and not additional:
            generated_nothing.extend([entry])

    return cards_to_add, additional_outputs, generated_nothing


def look_up_word(coll, word):
    return coll.find(
        {
            "word": word,
            "senses.form_of": {"$exists": False},  # Skip derived forms
        },
        {
            "_id": 0
        },  # JSON parser can't handle contents of _id field, so don't select it
    )


def retrieve_fields(entry, fields):
    try:
        res = jq.compile(fields).input_value(entry).all()
    except ValueError:
        return []

    if not res:
        return []

    if type(res[0]) is list:
        res = list(itertools.chain(*res))

    return [e for e in res if e]


class TestTranslator:
    def translate_text(*args, **kwargs):
        return "Test translation"
