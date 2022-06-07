import html
import genanki
import pandas as pd
import wordfreq


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


class DefinitionGenerator:

    # def convert_dictionary_to_tabfile(self) -> None:
    #    """Converts the dictionary to a tab-separated file"""
    #    glos = Glossary()
    #    glos.convert(
    #        self.dictionary_path,
    #        self.input_format,
    #        outputFilename=self.intermediate_tabfile_path,
    #        outputFormat="tsv",
    #    )

    def __init__(self, dictionary_path) -> None:
        self.dictionary_path = dictionary_path

    # def get_


def generate_anki_deck(
    sorted_sentences: pd.DataFrame,
    config: dict,  # deck_name: str, deck_description: str, deck_filename: str, model_id: int, deck_id: int
):
    # MODEL_ID = 1524605756
    # DECK_ID = 1327334698
    ## Load the sorted_sentences.tsv file with the sorted list of sentences into pandas
    # with open(sorted_tsv_file_path, "r", encoding="utf-8") as f:
    #    # Read tsv to pandas
    #    sorted_sentences = pd.read_csv(f, sep="\t", encoding="utf-8")

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
    model = genanki.Model(
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

    package = genanki.Package(deck)

    package.media_files = (
        sorted_sentences["sentence_id"]
        .map(lambda x: "audio_files/" + str(x) + ".mp3")
        .to_list()
    )

    # Iterate through the sorted sentences and add them to the Anki deck
    for index, row in sorted_sentences.iterrows():
        target_sentence = row["target_sentence"]
        if config["single_word_lookup_mode"]:
            target_sentence_html = f"{html.escape(target_sentence)}{generate_wiktionary_link_html(row['sentence_source'], config['wiktionary_base_url'], config['wiktionary_source_language'], config['source_language'])}"
        else:
            target_sentence_html = html.escape(target_sentence)
        # Create a new Anki note using genanki
        note = genanki.Note(
            model=model,
            fields=[
                html.escape(row["sentence_source"]),
                target_sentence_html,
                f"[sound:{row['sentence_id']}.mp3]",
            ],
        )
        # Add the note to the Anki deck
        deck.add_note(note)

    package.write_to_file(config["deck_output_path"])


# if __name__ == "__main__":
#    generate_anki_deck(
#        sorted_tsv_file_path="sorted_sentences.tsv",
#        deck_name="Tschechisch-Deutsch",
#        deck_description="Tschechisch-Deutsches Anki-Deck",
#        deck_filename="tschechisch_deutsch_deck.apkg",
#    )
