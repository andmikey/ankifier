from deepl import Translator
from typing import List, Tuple
from spacy import Language
from pymongo import Database

from card import Card


class Word:
    def __init__(self, word: str, pos: str, config: dict):
        self.word = word 
        self.pos = pos
        self.config = config
    
    def generate_cards(self) -> List[Card]:
        # Don't generate if derived form
        # Derived form = contains senses.form_of (see https://kaikki.org/dictionary/All%20languages%20combined/meaning/%D0%B3/%D0%B3%D0%BE/%D0%B3%D0%BE%D0%B2%D0%BE%D1%80%D1%8F%D1%89%D0%B8%D0%B9.html)
        pass 


class Phrase:
    def __init__(self, phrase: str, config: dict, spacy_pipeline: Language, 
                 translator: Translator, db: Database):
        self.phrase = phrase 
        self.config = config
        self.spacy = spacy_pipeline
        self.translator = translator
        self.db = db

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
            word = Word(lemma, pos, self.config)
            cards_for_lemma = word.generate_cards()
            cards.extend(cards_for_lemma)

        # Finally, translate the whole thing with DeepL
        translation = self.translator.translate_text(self.phrase, target_lang="EN")
        overall_translation = Card(self.phrase, translation)

        cards.append(overall_translation)

        return cards