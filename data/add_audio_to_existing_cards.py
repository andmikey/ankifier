import sys
from pymongo import MongoClient

sys.path.append("..")

from ankifier.utils import call_ankiconnect, look_up_word, retrieve_fields

DECK_NAME = "Languages::Russian"


def find_notes_without_audio(deck):
    # Find all the notes that are not phrases and do not have audio
    # query = f'deck:{deck} Audio: -"Part of speech:phrase'
    query = f'deck:{deck} Audio: футбол'
    request = {
        "action": "findNotes",
        "params": {"query": query},
        "version": 6,
    }
    response = call_ankiconnect(request)
    note_ids = response["result"]

    # Get the actual *contents* of those notes
    request = {
        "action": "notesInfo",
        "params": {"notes": note_ids},
        "version": 6,
    }
    response = call_ankiconnect(request)
    notes = response["result"]

    return notes


def get_audio_url_for_base(base_form, coll):
    entries = look_up_word(coll, base_form)
    for entry in entries:
        audio = retrieve_fields(entry, '.sounds[] | select(.text == "Audio") | .mp3_url')
        if audio:
            # Pull just the first sound entry
            return audio[0]
    return 


def add_audio_to_note(note, coll):
    note_id = note["noteId"]
    base_form = note["fields"]["Base form"]
    url = get_audio_url_for_base(base_form, coll)

    if not url:
        # Don't do anything if we don't find a url
        return 
    
    request = {
        "action": "updateNoteFields",
        "version": 6,
        "params": {
            "note": {
                "id": note_id,
                "audio": [
                    {"url": url, "filename": f"{base_form}.mp3", "fields": ["Audio"]}
                ],
            }
        },
    }

    call_ankiconnect(request)


def main():
    notes_to_process = find_notes_without_audio(DECK_NAME)
    mongo_client = MongoClient(serverSelectionTimeoutMS=1000)
    coll = mongo_client["ankifier"]["ru_wiktionary"]

    for note in notes_to_process:
        add_audio_to_note(note, coll)


if __name__ == "__main__":
    main()
