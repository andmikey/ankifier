from deepl import Translator
from typing import List, Tuple
from spacy import Language
from pymongo import Collection
from functools import reduce

from card import Card


# Maps SpaCy POS tags to Wiktionary POS 
# https://universaldependencies.org/u/pos/
POS_MAPPINGS = {
    "ADJ": set("adj"),
    "ADP": set("adv"),
    "ADV": set("prep", "prep_phrase"),
    "CCONJ": set("conj"),
    "DET": set("det"),
    "INTJ": set("intj"),
    "NOUN": set("noun"),
    "NUM": set("num"),
    "PART": set("particle"),
    "PRON": set("pron"),
    "PROPN": set("noun"),
    "PUNCT": set("punct"),
    "SCONJ": set("conj"),
    "SYM": set("symbol"),
    "VERB": set("verb")
}


class Word:
    def __init__(self, word: str, pos: str, config: dict, coll: Collection):
        self.word = word 
        self.pos = pos
        self.wiktionary_pos = POS_MAPPINGS.get(self.pos, None)
        self.config = config
        self.coll = coll

    def retrieve_config(self):
        # Return config for this POS 
        if self.pos in self.config:
            return self.config[self.pos]
        else:
            return self.config["default"]
        
    def get_field_from_dotted(self, entry, field):
        fields = field.split(".")
        for f in fields:
            entry = entry[f]
        return entry

    def retrieve_fields(self, entry, fields):
        if "use" in fields and "where" in fields:
            field = fields["use"].split(".")[:-1]
            filters = fields["use"].split(".")[-1]
            entries_for_field = self.get_field_from_dotted(entry, field)
            entries_to_keep = []
            for e in entries_for_field:
                if set(e[filters]) == fields["use"]:
                    entries_to_keep.append(e)
            val = ", ".join(entries_to_keep)
        else:
            val = str(self.get_field_from_dotted(entry, field))

        return val 

    
    def generate_cards(self) -> List[Card]:
        entries = self.coll.find({ 
                "word": self.word, 
                "senses.form_of": {"$exists": False} # Skip derived forms
                }, 
                {"forms", "senses", "related"} # Only retrieve relevant fields
            )
        
        # May get multiple entries, so choose the one with the POS we're looking for 
        entries_to_process = []
        for entry in entries:
            if self.wiktionary_pos is not None:
                if entry["pos"] == self.wiktionary_pos:
                    entries_to_process.append(entry)
                    break
            else:
                entries_to_process.append(entry)

        cards_to_output = [] 

        for entry in entries_to_process:
            config = self.retrieve_config()
            config_front = config["front"]
            config_back = config["back"]
            
            # Generate card just for this word
            front = self.retrieve_fields(entry, config_front)
            back = self.retrieve_fields(entry, config_back)
            card = Card(front, back)
            cards_to_output.append(card)

            # Optional: choose examples and output to another file
            # Optional: choose related words and output to another file
            # TODO

        # Generate cards for related words
        return cards_to_output


class Phrase:
    def __init__(self, phrase: str, config: dict, spacy_pipeline: Language, 
                 translator: Translator, coll: Collection):
        self.phrase = phrase 
        self.config = config
        self.spacy = spacy_pipeline
        self.translator = translator
        self.coll = coll

    def pre_process_phrase(self, phrase: str) -> List[Tuple[str, str]]:
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

        # First, try looking the phrase itself up 
        word = Word(self.phrase, "", self.config) # TODO what POS tag?
        cards_for_phrase = word.generate_cards()
        cards.extend(cards_for_phrase)

        # Next, look up all the individual (lemmatized) words and generate cards for these
        tokens = self.pre_process_phrase(self.phrase)
        for (lemma, pos, detailed_pos) in tokens:
            word = Word(lemma, pos, self.config, self.coll)
            cards_for_lemma = word.generate_cards()
            cards.extend(cards_for_lemma)

        # Finally, translate the whole thing with DeepL
        translation = self.translator.translate_text(self.phrase, target_lang="EN")
        overall_translation = Card(self.phrase, translation)

        cards.append(overall_translation)

        return cards