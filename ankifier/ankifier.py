import click
import yaml
from pathlib import Path 
from typing import List 

from card import Card
from phrase import Phrase


class Ankifier:
    def __init__(self, config: dict):
        self.config = config
        self.cards_to_add: List[Card] = []

    def parse_file(self, input_file: Path):
        with open(input_file, 'r') as f:
            for entry in f:
                p = Phrase(entry, self.config)
                cards = p.generate_cards() 
                self.cards_to_add.append(cards)

    def write_out_cards(self):
        # Write out cards_to_add
        pass 


@click.command()
@click.option("--config-file", type=click.File('r'))
@click.option("--input-file", type=click.Path(exists=True))
def main(config_file: click.File, input_file: click.Path):
    config = yaml.safe_load(config_file)

    ankifier = Ankifier(config)
    ankifier.parse_file(input_file)