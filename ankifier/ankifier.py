import click
import deepl
import spacy
import yaml
from pathlib import Path 
from typing import List 
from pymongo import MongoClient

from card import Card
from phrase import Phrase


class Ankifier:
    def __init__(self, config: dict):
        self.config = config
        self.cards_to_add: List[Card] = []
        self.mongodb = self.config.ankifier_config.mongodb_name

    def create_spacy_pipeline(self, language: str) -> spacy.Language:
        model = self.config.language_configs[language]["spacy_model"]
        nlp = spacy.load(model)
        return nlp

    def parse_file(self, input_file: Path, language: str):
        spacy_pipeline = self.create_spacy_pipeline(language)
        translator = deepl.Translator(self.config.ankifier_config.deepl_api_key)
        # Set up for database queries
        db = MongoClient()[self.mongodb]

        with open(input_file, 'r') as f:
            for entry in f:
                p = Phrase(entry, self.config, spacy_pipeline, translator, db)
                cards = p.generate_cards() 
                self.cards_to_add.append(cards)

    def write_out_cards(self):
        # Write out cards_to_add
        pass 


@click.command()
@click.option("--config-file", type=click.File('r'))
@click.option("--input-file", type=click.Path(exists=True))
@click.option("--language", type=str)
def main(config_file: click.File, input_file: click.Path, language: str):
    config = yaml.safe_load(config_file)

    ankifier = Ankifier(config)
    ankifier.parse_file(input_file, language)