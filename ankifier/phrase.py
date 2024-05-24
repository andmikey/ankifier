from typing import List

from card import Card


class Word:
    def __init__(self, word: str, config: dict):
        self.word = word 
        self.config = config
    
    def generate_cards(self) -> List[Card]:
        pass 


class Phrase:
    def __init__(self, phrase: str, config: dict):
        self.phrase = phrase 
        self.config = config
    
    def generate_cards(self) -> List[Card]:
        cards: List[Card] = []

        # First, try looking the phrase itself up 
        # If it's a phrase (NOT a derived form of a word etc), add it

        # Next, look up all the individual (lemmatized) words and generate cards for these

        # Finally, translate the whole thing with DeepL

        return cards