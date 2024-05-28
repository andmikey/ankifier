import click
import deepl
import spacy
import logging
import yaml
from pathlib import Path 
from typing import List 
from pymongo import MongoClient

from card import Card
from phrase import Phrase


class MockTranslator:
    def __init__(self):
        pass 

    def translate_text(self, text, **kwargs):
        return "translated"


class Ankifier:
    def __init__(self, config: dict):
        self.config = config
        self.cards_to_add: List[Card] = []
        self.mongodb = self.config["ankifier_config"]["mongodb_name"]

    def create_spacy_pipeline(self, language: str) -> spacy.Language:
        model = self.config["language_configs"][language]["spacy_model"]
        nlp = spacy.load(model)
        return nlp

    def parse_file(self, input_file: Path, language: str):
        logging.info(f"Processing input file: {input_file}")
        spacy_pipeline = self.create_spacy_pipeline(language)
        translator = MockTranslator() # deepl.Translator(self.config.ankifier_config.deepl_api_key)

        # Set up for database queries
        coll = MongoClient()[self.mongodb][self.config["language_configs"][language]["wiktionary_collection"]]

        # Open the language-level config 
        with open(self.config["language_configs"][language]["word_settings"]) as f:
            language_config = yaml.safe_load(f)

        with open(input_file, 'r') as f:
            for entry in f:
                p = Phrase(entry.strip(), language_config, spacy_pipeline, translator, coll)
                cards = p.generate_cards() 
                logging.info(f"Generated {len(cards)} cards for {entry}")
                self.cards_to_add.extend(cards)

    def write_out_cards(self):
        # Write out cards_to_add
        with open("out.csv", "w+") as f:
            for c in self.cards_to_add:
                f.write(f"{c}\n")


@click.command()
@click.option("--config-file", type=click.Path(exists=True))
@click.option("--input-file", type=click.Path(exists=True))
@click.option("--language", type=str)
def main(config_file: click.File, input_file: click.Path, language: str):
    logging.basicConfig(level=logging.DEBUG)

    with open(config_file) as f:
        config = yaml.safe_load(f)

    ankifier = Ankifier(config)
    ankifier.parse_file(input_file, language)
    ankifier.write_out_cards()

if __name__ == "__main__":
    main()