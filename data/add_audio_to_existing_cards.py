import sys
from pymongo import MongoClient

sys.path.append("..")

from ankifier.utils import call_ankiconnect, look_up_word, retrieve_fields

DECK_NAME = "Languages::Russian"


def find_notes_without_audio(deck):
    # Find all the notes that are not phrases and do not have audio
    query = f'deck:{deck} Audio: -"Part of speech:phrase"'
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
        audio = retrieve_fields(entry, ".sounds[] | .mp3_url")
        if audio:
            # Pull just the first sound entry
            return audio[0]
    return


def add_audio_to_note(note, coll):
    note_id = note["noteId"]
    base_form = note["fields"]["Base form"]["value"]
    url = get_audio_url_for_base(base_form, coll)
    print("Audio link: ", url)

    if not url:
        # Don't do anything if we don't find a url
        return

    request = {
        "action": "updateNote",
        "version": 6,
        "params": {
            "note": {
                "id": note_id,
                # Need a dummy "fields" method or the call fails
                "fields": {},
                "audio": [
                    {"url": url, "filename": f"{base_form}.mp3", "fields": ["Audio"]}
                ],
            }
        },
    }

    call_ankiconnect(request)


def main():
    notes_to_process = find_notes_without_audio(DECK_NAME)
    print(f"Found {len(notes_to_process)} notes to process")
    mongo_client = MongoClient(serverSelectionTimeoutMS=1000)
    coll = mongo_client["ankifier"]["ru_wiktionary"]

    for note in notes_to_process:
        print("Adding audio to note: ", note["fields"]["Base form"]["value"])
        add_audio_to_note(note, coll)


if __name__ == "__main__":
    main()
