import html
import os
import genanki
import pandas as pd
import wordfreq

from tatoeba_to_anki.tabfiledictionary import SimpleTabfileDictionary


def generate_wiktionary_link_html(
    sentence: str,
    wiktionary_base_url,
    wiktionary_source_language: str,
    ietf_language_code: str,
) -> str:
    # Tokenize the sentence using wordfreq
    tokens = wordfreq.tokenize(sentence, ietf_language_code)
    html = "<p>"
    for token in tokens:
        html += f"<a href='{wiktionary_base_url}{token}#{wiktionary_source_language}'>{token}</a> "
    html += "</p>"
    return html

def generate_dictionary_html(
    sentence: str,
    dictionary: SimpleTabfileDictionary,
    ietf_language_code: str,
) -> str:
    tokens = wordfreq.tokenize(sentence, ietf_language_code)
    html = "<p>"
    for token in tokens:
        results = dictionary.get_entries(token)
        if results is not None:
            html += "<details><summary>" + token + "</summary>"
            for result in results:
                html += f"<b>{list(result.headword_and_inflections)[0]}</b>"
                html += f"<br>{result.definition}<br><br>"
            html += "</details>"
    html += "</p>"
    return html

def generate_anki_deck(
    sorted_sentences: pd.DataFrame,
    config: dict,  # deck_name: str, deck_description: str, deck_filename: str, model_id: int, deck_id: int
    audio_files_folder="audio_files",
):

    css_s = """
    .card {
        font-family: arial;
        font-size: 20px;
        text-align: center;
        color: black;
        background-color: white;
        padding: 20px;
        }
        """
    # Create a new Anki deck using genanki
    deck = genanki.Deck(
        config["deck_id"], config["deck_name"], config["deck_description"]
    )
    # Create a new Anki model using genanki
    audio_note_model = genanki.Model(
        config["model_id"],
        "Simple Model with Media",
        fields=[
            {"name": "Question"},
            {"name": "Answer"},
            {"name": "MyMedia"},
        ],
        templates=[
            {
                "name": "Card 1",
                "qfmt": "{{Question}}<br>{{MyMedia}}",
                "afmt": '{{FrontSide}}<hr id="answer">{{Answer}}',
            },
        ],
        css=css_s,
    )
    no_audio_model = genanki.Model(
        1414956686,
        "Simple Model",
        fields=[
            {"name": "Question"},
            {"name": "Answer"},
        ],
        templates=[
            {
                "name": "Card 1",
                "qfmt": "{{Question}}",
                "afmt": '{{FrontSide}}<hr id="answer">{{Answer}}',
            },
        ],
        css=css_s,
    )

    package = genanki.Package(deck)

    # Get a list of all files in the audio_files folder with the full relative path if the audio files folder exists
    if os.path.exists(audio_files_folder):
        audio_files = [
            os.path.join(audio_files_folder, f)
            for f in os.listdir(audio_files_folder)
            if os.path.isfile(os.path.join(audio_files_folder, f))
            and f.split(".")[0].isdigit()
            # also check if the sentence id in the filename matches the sentence id in the sorted_sentences
            and int(f.split(".")[0]) in sorted_sentences["sentence_id"].values
        ]
    # audio_files = os.listdir(audio_files_folder)
    # audio_files = [
    #    f for f in os.listdir(config["audio_files_path"]) if os.path.isfile(f)
    # ]
        package.media_files = audio_files
    # package.media_files = (
    #    sorted_sentences["sentence_id"]
    #    .map(lambda x: "audio_files/" + str(x) + ".mp3")
    #    .to_list()
    # )
    if config["single_word_lookup_mode"] == "Dictionary":
        dictionary = SimpleTabfileDictionary(config["dictionary_path"])


    # Iterate through the sorted sentences and add them to the Anki deck
    for index, row in sorted_sentences.iterrows():
        target_sentence = row["target_sentence"]
        if config["single_word_lookup_mode"] == "Wiktionary":
            target_sentence_html = f"{html.escape(target_sentence)}{generate_wiktionary_link_html(row['sentence_source'], config['wiktionary_base_url'], config['wiktionary_source_language'], config['source_language'])}"
        elif config["single_word_lookup_mode"] == "Dictionary":
            target_sentence_html = f"{html.escape(target_sentence)}{generate_dictionary_html(row['sentence_source'], dictionary, config['source_language'])}"
        else:
            target_sentence_html = html.escape(target_sentence)
        # Create a new Anki note using genanki depending on whether an audio file for it exists
        if os.path.isfile(os.path.join("audio_files/", f"{row['sentence_id']}.mp3")):

            note = genanki.Note(
                model=audio_note_model,
                fields=[
                    html.escape(row["sentence_source"]),
                    target_sentence_html,
                    f"[sound:{row['sentence_id']}.mp3]",
                ],
            )
        else:
            note = genanki.Note(
                model=no_audio_model,
                fields=[
                    html.escape(row["sentence_source"]),
                    target_sentence_html,
                ],
            )
        # Add the note to the Anki deck
        deck.add_note(note)

    package.write_to_file(config["deck_output_path"])


if __name__ == "__main__":
    dictionary = SimpleTabfileDictionary("Tschechisch-Deutsch.txt")
    print(generate_dictionary_html("svoboda je pro mě velmi důležitá", dictionary, "cs"))
