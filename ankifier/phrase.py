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
        pass 


class Phrase:
    def __init__(self, phrase: str, config: dict, spacy_pipeline: Language, 
                 translator, db: Database):
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
        # If it's a phrase (NOT a derived form of a word etc), add it
        # TODO look up the phrase in the mongo DB here

        # Next, look up all the individual (lemmatized) words and generate cards for these
        tokens = self.pre_process_phrase(self.phrase)
        for (lemma, pos, detailed_pos) in tokens:
            word = Word(lemma, pos, self.config.config)
            cards_for_lemma = word.generate_cards()
            cards.extend(cards_for_lemma)

        # Finally, translate the whole thing with DeepL
        translation = self.translator.translate_text(self.phrase, target_lang="EN")
        overall_translation = Card(self.phrase, translation)

        cards.append(overall_translation)

        return cards