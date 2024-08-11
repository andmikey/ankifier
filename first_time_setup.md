# Ankifier: first time setup

## Python environment
Create a new Conda environment from the `environment.yaml`:
```bash
conda create --name ankifier --file environment.yaml
```
(this is exported with `conda env export -n ankifier > environment.yaml` from my development environment). 

Ankifier uses SpaCy to tokenize and lemmatize input phrases. Download the [SpaCy models](https://spacy.io/models) for the languages you want to use, e.g.:
```bash
python -m spacy download ru_core_news_sm
```

## Wiktionary database

Set up MongoDB using the instructions [here](https://www.mongodb.com/docs/manual/administration/install-community/) and make sure your Mongo instance is running (`sudo service mongod start`).

To retrieve information about individual words (definitions, conjugations/declinations, example usages, etc) Ankifier uses pre-parsed Wiktionary extracts. Download a Wiktionary dump from [Kaikki](https://kaikki.org/dictionary/) for your chosen language. Save it somewhere (e.g. `data/`). Make sure Mongo is running locally, then run the `import_data.sh` script to import it to a Mongo database and collection of your choice, e.g.: 

```bash
bash import_data.sh ankifier ru_wiktionary kaikki.org-dictionary-Russian.json
```

## DeepL API key

Ankifier uses the DeepL API to translate longer phrases into English. Sign up for a free API key on the [DeepL website](https://www.deepl.com/pro/change-plan#developer): this gives you 500,000 characters per month, which should be more than enough!  

## Anki and AnkiConnect 
Install AnkiConnect using the instructions [here](https://git.foosoft.net/alex/anki-connect). This stops you adding cards which already exist in Anki. Make sure Anki is running while you use Ankifier. 

Make sure you have a suitable card type for saving your cards. This should contain the following fields:
- Front: the word or phrase in the target language. 
- Back: the word or phraes in English. 
- Base form: the front reduced to a base form (with e.g. stress marks removed, the verb in the infinitive form). Used for deduplication.
- Part of speech: the part-of-speech according to Wiktionary, or "phrase" if it's a phrase or sentence. 
- Audio: the audio for the word in the target language. 


## Settings files
You'll need to define at least two settings files:
1. An overall Ankifier settings file, described in the [example_settings.yaml](./settings/example_settings.yaml). 
2. A settings file for each language you wish to process, which specifies how word-level cards are generated from Wiktionary definitions. 

The language-level settings file should have one entry for each part of speech, with a `front` and `back` defined in `jq` syntax. The `default` entry defines what to do if no part-of-speech can be matched.

There is an example file for Russian in [settings/language_configs](./settings/language_configs/russian.yaml). 