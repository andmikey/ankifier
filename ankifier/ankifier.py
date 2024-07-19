import click
import deepl
import spacy
import logging
import pandas as pd
import yaml

from pathlib import Path
from typing import List
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError

from card import Card
from phrase import Phrase


class Ankifier:
    def __init__(self, config: dict, language_config_file: Path, language: str):
        self.config = config
        self.cards_to_add: List[Card] = []
        self.additional_outputs: List[str] = []
        self.mongodb = self.config["ankifier_config"]["mongodb_name"]
        self.language_config_file = language_config_file
        self.language = language

    def create_spacy_pipeline(self, language: str) -> spacy.Language:
        model = self.config["language_configs"][language]["spacy_model"]
        nlp = spacy.load(model)
        return nlp

    def parse_file(self, input_file: Path):
        contents = pd.read_csv(input_file)
        self.parse_contents(contents)

    def parse_contents(self, input: pd.DataFrame):
        spacy_pipeline = self.create_spacy_pipeline(self.language)
        translator = deepl.Translator(self.config["ankifier_config"]["deepl_api_key"])

        # Set up connection to Mongo for database queries
        client = MongoClient(serverSelectionTimeoutMS=1000)
        try:
            client.is_mongos
        except ServerSelectionTimeoutError:
            logging.info("Can't connect to Mongo client. Is it running?")
            exit()

        coll = client[self.mongodb][
            self.config["language_configs"][self.language]["wiktionary_collection"]
        ]

        # Open the language-level config
        with open(self.language_config_file) as f:
            language_config = yaml.safe_load(f)

        for entry in input:
            p = Phrase(entry.strip(), language_config, spacy_pipeline, translator, coll)
            cards = p.generate_cards()
            self.cards_to_add.extend(cards)
            # Examples, synonyms, antonyms, related words, etc
            # Print a separator so it's clear which entries came from which phrase
            self.additional_outputs.extend(
                [f"Generated from {entry.strip()}:"]
                + p.get_additional_outputs()
                + ["\n\n"]
            )

    def write(self, file, arr):
        with open(file, "w+") as f:
            for item in arr:
                f.write(f"{item}\n")

    def write_out_cards(self, output_file):
        self.write(output_file, self.cards_to_add)

    def write_out_additionals(self, output_file):
        self.write(output_file, self.additional_outputs)


@click.command()
@click.option("--config-file", type=click.Path(exists=True))
@click.option("--language-config-file", type=click.Path(exists=True))
@click.option("--input-file", type=click.Path(exists=True))
@click.option("--output-file", type=click.Path())
@click.option("--additional-outputs-file", type=click.Path())
@click.option("--language", type=str)
def main(
    config_file: click.Path,
    language_config_file: click.Path,
    input_file: click.Path,
    output_file: click.Path,
    additional_outputs_file: click.Path,
    language: str,
):
    logging.basicConfig(level=logging.DEBUG)

    with open(config_file) as f:
        config = yaml.safe_load(f)

    ankifier = Ankifier(config, language_config_file, language)
    ankifier.parse_file(input_file)
    ankifier.write_out_cards(output_file)
    ankifier.write_out_additionals(additional_outputs_file)


if __name__ == "__main__":
    main()
