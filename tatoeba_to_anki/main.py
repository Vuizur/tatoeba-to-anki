import random
import pandas as pd
from tatoeba_to_anki.download_audio import AudioDownloader
import tomli
from tatoeba_to_anki.generate_anki_deck import generate_anki_deck
from tatoeba_to_anki.sort_sentences import order_sentences


# TSV_FILE_PATH = "Satzpaare Tschechisch-Deutsch - 2022-05-30.tsv"
# SOURCE_LANGUAGE = "cs"

# You probably shouldn't change this
AUDIO_DIR = "audio_files"

def czech_strings_are_very_similar(string1: str, string2: str) -> bool:

    # Return True if only the punctuation (.,:;!) is different
    if string1.replace(".", "").replace(",", "").replace(":", "").replace(
        ";", ""
    ).replace("!", "") == string2.replace(".", "").replace(",", "").replace(
        ":", ""
    ).replace(
        ";", ""
    ).replace(
        "!", ""
    ):
        return True
    # Return False if number of words is different
    if len(string1.split()) != len(string2.split()):
        return False

    # TODO: Return True if all words are the same or only differ in the last characters if the last characters are "l" or "ly"

    return False


def load_sentences_from_tsv(tsv_file_path: str) -> pd.DataFrame:
    """
    Loads the sentences from the TSV file.
    """
    with open(tsv_file_path, "r", encoding="utf-8") as f:
        # Read tsv to pandas
        df = pd.read_csv(tsv_file_path, sep="\t", encoding="utf-8")
        # Set pandas dataframe columns to "sentence_id", "sentence_source", "target_sentence_id", "target_sentence"
        df.columns = [
            "sentence_id",
            "sentence_source",
            "target_sentence_id",
            "target_sentence",
        ]
    return df


if __name__ == "__main__":

    with open("config.toml", "rb") as f:
        config = tomli.load(f)
    print("Config loaded")
    df = load_sentences_from_tsv(config["sentence_pairs_path"])
    print("Sentences loaded")
    # Order the sentences
    sorted_sentences = order_sentences(df, config["source_language"])
    print("Sentences sorted")

    # Load the sorted_sentences.tsv file with the sorted list of sentences into pandas
    # with open("sorted_sentences.tsv", "r", encoding="utf-8") as f:
    #    tsv_data = csv.reader(f, delimiter="\t")
    #    # Read tsv to pandas
    #    sorted_sentences = pd.read_csv(f, sep="\t", encoding="utf-8")

    audio_downloader = AudioDownloader(
        config["source_language"],
        config["sentences_with_audio_path"],
        audio_dir=AUDIO_DIR,
    )
    # Iterate through the dataframe and download the audio files
    for i in range(len(sorted_sentences)):
        audio_downloader.download_audio(
            sorted_sentences["sentence_id"][i],
            sorted_sentences["sentence_source"][i],
            random.randint(1, 2),
        )
    print("Audio files downloaded")
    # Generate the Anki deck
    generate_anki_deck(
        sorted_sentences,
        config
    )
    print("Anki deck generated")
