# Ankifier: generating Anki cards for language learning

## Importing 
To retrieve information about individual words (definitions, conjugations/declinations, example usages, etc) we use pre-parsed Wiktionary extracts. 

Download a Wiktionary dump from [Kaikki](https://kaikki.org/dictionary/) for your chosen language. Save it somewhere (e.g. `data/`). Make sure Mongo is running locally, then run the `import_data.sh` script to import it to a Mongo database and collection of your choice, e.g.: 

```bash
bash import_data.sh ankifier russian kaikki.org-dictionary-Russian.json
```