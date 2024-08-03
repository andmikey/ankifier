import itertools
import json
import logging
import urllib
from typing import List, Tuple

import jq
import streamlit as st
from spacy import Language


class Card:
    def __init__(self, front: str, back: str, pos: str, base: str):
        self.front = front
        self.back = back
        self.pos = pos
        self.base = base

    def __str__(self):
        return f"{self.front}|{self.back}|{self.pos}|{self.base}"

    def __repr__(self):
        return self.__str__

    def __eq__(self, card):
        return (self.front == card.front) and (self.pos == card.pos)

    def as_tuple(self):
        return (self.front, self.back, self.pos, self.base)


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
            base = retrieve_fields(entry, ".word")
            front_contents = retrieve_fields(entry, config_front)
            back_contents = retrieve_fields(entry, config_back)
            if front_contents is not None and back_contents is not None:
                front = ", ".join([x for x in front_contents if x])
                back = "<br>".join([x for x in back_contents if x])
                base = strip_stress_marks("".join([x for x in base]))
                card = Card(front, back, pos, base)
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
        self,
        phrase: str,
        translation: str,
        config: dict,
        spacy_pipeline: Language,
        translator,
        coll,
        anki_deck: str,
    ):
        self.phrase = phrase
        # For Russian, should be removed for other languages
        self.cleaned_phrase = strip_stress_marks(phrase)
        self.translation = translation
        self.config = config
        self.spacy = spacy_pipeline
        self.translator = translator
        self.coll = coll
        self.anki_deck = anki_deck
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
        tokens = self.pre_process_phrase(self.cleaned_phrase)
        for lemma, pos, detailed_pos in tokens:
            if pos == "PROPN":
                lemma = lemma.capitalize()

            # Only generate for words not already in Anki
            if not self.exists_in_anki(lemma):
                word = Word(lemma, pos, self.config, self.coll)
                cards_for_lemma = word.generate_cards()
                cards.extend(cards_for_lemma)
                self.examples.extend(word.examples)
                self.related.extend(word.related)

        # Translate the whole phrase
        if len(tokens) > 1:
            # Only generate for phrases not already in Anki
            if not self.exists_in_anki(self.cleaned_phrase):
                if self.translation != "":
                    # Already have a translation provided
                    translation = self.translation
                else:
                    # Run through the translator
                    translation = self.translator.translate_text(
                        self.cleaned_phrase, target_lang="EN-GB"
                    )
                overall_translation = Card(
                    self.phrase, translation, "phrase", strip_stress_marks(self.phrase)
                )
                cards.append(overall_translation)

        logging.info(
            f"Generated {len(cards)} cards for {self.phrase}, "
            + f"{len(self.examples) + len(self.related)} additional cards"
        )
        return [c.as_tuple() for c in cards]

    def get_additional_outputs(self) -> List[str]:
        return self.related + self.examples

    def exists_in_anki(self, entry: str) -> bool:
        search_query = f'deck:{self.anki_deck} "Base form:{entry}"'
        request = {
            "action": "findCards",
            "params": {"query": search_query},
            "version": 6,
        }

        request_json = json.dumps(request).encode("utf-8")
        response = json.load(
            urllib.request.urlopen(
                urllib.request.Request("http://127.0.0.1:8765", request_json)
            )
        )
        # Error handling borrowed from https://git.foosoft.net/alex/anki-connect#python
        if len(response) != 2:
            raise Exception('Response has an unexpected number of fields')
        if 'error' not in response:
            raise Exception('Response is missing required error field')
        if 'result' not in response:
            raise Exception('Response is missing required result field')
        if response['error'] is not None:
            raise Exception(response['error'])
        
        count_matches = len(response["result"])
        return (count_matches > 0)
    

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
        translation = str(row["Translation"]).strip()
        p = Phrase(
            entry,
            translation,
            st.session_state["language_config"],
            st.session_state["nlp"],
            st.session_state["translator"],
            st.session_state["mongo_coll"],
            st.session_state["language_anki_deck"]
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


def strip_stress_marks(text: str) -> str:
    # https://www.ojisanseiuchi.com/2022/01/23/stripping-russian-syllabic-stress-marks-in-python/
    b = text.encode("utf-8")
    # correct error where latin accented ó is used
    b = b.replace(b"\xc3\xb3", b"\xd0\xbe")
    # correct error where latin accented á is used
    b = b.replace(b"\xc3\xa1", b"\xd0\xb0")
    # correct error where latin accented é is used
    b = b.replace(b"\xc3\xa0", b"\xd0\xb5")
    # correct error where latin accented ý is used
    b = b.replace(b"\xc3\xbd", b"\xd1\x83")
    # remove combining diacritical mark
    b = b.replace(b"\xcc\x81", b"").decode()
    return b


class TestTranslator:
    def translate_text(*args, **kwargs):
        return "Test translation"
