# Ankifier: generating Anki cards for language learning

**Ankifier** is a tool to generate Anki cards from vocabulary lists.

Given an input file, Ankifier uses Wiktionary and DeepL to generate:
1. Cards for individual words (including words in phrases/sentences)
2. Translations into English for phrases and sentences

Optionally, for each word card it can also give you an output of related words (incl synonyms, antonyms) and examples from Wiktionary. 

For example, given the input `он говорит по-русски`, Ankifier will generate the following cards:
- The Wiktionary entries of `он`, `говорю́`, `по`, `русски`
- The DeepL translation of `он говорит по-русски` 

## Setting up 
### Python environment
Create a new Conda environment from the `environment.yaml`:
```bash
conda create --name ankifier --file environment.yaml
```
(this is exported with `conda env export -n ankifier > environment.yaml` from my development environment). 

Set up MongoDB using the instructions [here](https://www.mongodb.com/docs/manual/administration/install-community/) and make sure your Mongo instance is running.

### Set up linguistic tools 

Ankifier uses SpaCy to tokenize and lemmatize input phrases. Download the [SpaCy models](https://spacy.io/models) for the languages you want to use, e.g.:
```bash
python -m spacy download ru_core_news_sm
```

To retrieve information about individual words (definitions, conjugations/declinations, example usages, etc) Ankifier uses pre-parsed Wiktionary extracts. Download a Wiktionary dump from [Kaikki](https://kaikki.org/dictionary/) for your chosen language. Save it somewhere (e.g. `data/`). Make sure Mongo is running locally, then run the `import_data.sh` script to import it to a Mongo database and collection of your choice, e.g.: 

```bash
bash import_data.sh ankifier ru_wiktionary kaikki.org-dictionary-Russian.json
```

Ankifier uses the DeepL API to translate longer phrases into English. Sign up for a free API key on the [DeepL website](https://www.deepl.com/pro/change-plan#developer): this gives you 500,000 characters per month, which should be more than enough!  


### Settings files
You'll need to define at least two settings files:
1. An overall Ankifier settings file, described in the [example_settings.yaml](./settings/example_settings.yaml). 
2. A settings file for each language you wish to process, which specifies how word-level cards are generated from Wiktionary definitions. 

The language-level settings file should have one entry for each part of speech, with a `front` and `back` defined in `jq` syntax. The `default` entry defines what to do if no part-of-speech can be matched.

```yaml
default:
  front: .forms[] | select(.tags == ["canonical"]).form
  back: .senses[].glosses

verb:
  front: .forms[] | select((.tags == ["first-person", "present", "singular"]) or (.tags == ["present", "second-person", "singular"]) or (.tags == ["plural", "present", "third-person"])).form
  back: .senses[].glosses
```

There is an example file for Russian in [settings/language_configs](./settings/language_configs/russian.yaml). 

## Using Ankifier 

Call Ankifier from the command line with the following arguments:
- `--config-file`: the configuration file for Ankifier. 
- `--input-file`: the vocabulary list to process. Each entry should be on a new line and the entire file should be in one language. 
- `--output-file`: the file to output Anki cards in plain text format. Each card will be on a new line in the format `front|back|part-of-speech`.  
- `--additional-outputs-file`: the file to output additional outputs (examples, related words, synonyms, antonyms). These *are not* Anki cards: it's up to you to browse through this file and decide what to discard and what to pass to Ankifier for a second pass. 
- `--language`: the language for the input file, matching one of the language settings in the config file. 