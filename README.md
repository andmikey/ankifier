# Ankifier: generating Anki cards for language learning

**Ankifier** is a tool to generate Anki cards from vocabulary lists.

Given an input file, Ankifier uses Wiktionary and DeepL to generate:
1. Cards for individual words.
2. Translations into English for longer phrases and sentences.

The benefits of Ankifier are:
- Automatic pronounciation: Ankifier will pull audio for individual words from Wiktionary (where available) and save it to word cards.
- Incremental cards: if you add a phrase or sentence where you don't know all the words, Ankifier will generate cards for each of the new words, too.  
- Learn declensions and conjugations: Ankifier can pull declensions for nouns, conjugations for verbs, and so on - just configure which fields you want on your card in the language-level config.  
- Automatic deduplication: cards aren't added if they're already in your Anki database. 
- Related words: for each word card, Ankifier will also generate lists of related words (e.g. synonyms, antonyms) and examples. 

## Setting up 
See the [first time setup guide](./first_time_setup.md). 

## Using Ankifier 

Run the streamlit app with `streamlit run ankifier.py`. Make sure MongoDB and Anki are running. 

Upload your setings file in the 'Settings' tab. The "testing mode" switch is used to turn DeepL translation on and off (with it off, all translations that would usually go to DeepL just return "test translation" instead). 

Upload your vocabulary file (one entry per line, or if you want to include a phrase with a translation, the line should contain "phrase | translation") in the 'Import cards' tab. You'll see a text editor that lets you add, delete, and edit entries as desired. Once you're happy, press 'Generate cards'. 

The resulting Anki cards are in the 'Edit cards' tab. You can also use this tab to edit previously-generated card sets. Double-check the cards for correctness and then click "Write cards to Anki" to write your cards directly to Anki. 

In 'Additional outputs' you'll see related outputs (e.g. example sentences) which were generated but not added to the final list, alongside the entry they were generated from. You'll also see a list of the entries which did not generate any cards.

Finally, in the 'Look up' tab you can look up individual words from Wiktionary and experiment with jq filters on them. This is useful if you want to change your jq filter to cover some specific edge cases. From here you can also generate single-word cards and write them directly to Anki.  