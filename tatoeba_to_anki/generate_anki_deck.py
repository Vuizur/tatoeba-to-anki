import genanki
import pandas as pd


def generate_anki_deck(
    sorted_tsv_file_path, deck_name, deck_description, deck_filename
):
    MODEL_ID = 1524605756
    DECK_ID = 1327334698
    # Load the sorted_sentences.tsv file with the sorted list of sentences into pandas
    with open(sorted_tsv_file_path, "r", encoding="utf-8") as f:
        # Read tsv to pandas
        sorted_sentences = pd.read_csv(f, sep="\t", encoding="utf-8")

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
    deck = genanki.Deck(DECK_ID, deck_name, deck_description)
    # Create a new Anki model using genanki
    model = genanki.Model(
        MODEL_ID,
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

    package = genanki.Package(deck)

    package.media_files = (
        sorted_sentences["sentence_id"]
        .map(lambda x: "audio_files/" + str(x) + ".mp3")
        .to_list()
    )

    # Iterate through the sorted sentences and add them to the Anki deck
    for index, row in sorted_sentences.iterrows():
        # Create a new Anki note using genanki
        note = genanki.Note(
            model=model,
            fields=[
                row["sentence_source"],
                row["target_sentence"],
                f"[sound:{row['sentence_id']}.mp3]",
            ],
        )
        # Add the note to the Anki deck
        deck.add_note(note)

    package.write_to_file(deck_filename)

if __name__ == "__main__":
    generate_anki_deck(
        sorted_tsv_file_path="sorted_sentences.tsv",
        deck_name="Tschechisch-Deutsch",
        deck_description="Tschechisch-Deutsches Anki-Deck",
        deck_filename="tschechisch_deutsch_deck.apkg",
    )
