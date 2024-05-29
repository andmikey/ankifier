# Ankifier: generating Anki cards for language learning

## Setting up environment

Create a new Conda environment from the `environment.yaml`:
```bash
conda create --name ankifier --file enironment.yaml
```
(this is exported with `conda env export -n ankifier > environment.yaml` from my development environment). 

Set up MongoDB using the instructions [here](https://www.mongodb.com/docs/manual/administration/install-community/) and make sure your Mongo instance is running.

Download the [SpaCy models](https://spacy.io/models) corresponding to the languages you specify in your config, e.g.:
```bash
python -m spacy download ru_core_news_sm
```

## Configuring Ankifier settings

You'll need to define at least two settings files:
1. An overall Ankifier settings file, described in the [example_settings.yaml](./settings/example_settings.yaml). 
2. A settings file for each language you wish to process, which specifies how word-level cards are generated from Wiktionary definitions.  


## Importing Wiktionary data 
To retrieve information about individual words (definitions, conjugations/declinations, example usages, etc) we use pre-parsed Wiktionary extracts. 

Download a Wiktionary dump from [Kaikki](https://kaikki.org/dictionary/) for your chosen language. Save it somewhere (e.g. `data/`). Make sure Mongo is running locally, then run the `import_data.sh` script to import it to a Mongo database and collection of your choice, e.g.: 

```bash
bash import_data.sh ankifier ru_wiktionary kaikki.org-dictionary-Russian.json
```

## Processing input files
The input to this program is a CSV, where each row in the CSV contains either:
1. A word or short phrase. 
2. A longer phrase or sentence. 

To process each entry:
- If it's a word:
    - Lemmatize it.
    - Look it up in the Wiktionary entries and create a new card for the word. 
    - (Optional) Create cards for any examples in the Wiktionary entry.
    - (Optional) Create cards for any related words.
- If it's a phrase:
    - (Optional) Look the phrase up in Wiktionary and generate a card for it.
    - For any words in the phrase we've not seen before, generate cards for them as above. 
    - Generate a card based on the DeepL translation of the phrase.