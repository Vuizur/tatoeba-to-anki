import sys
import pandas as pd
from tatoeba_to_anki.download_audio import AudioDownloader, get_sentences_with_audio
import tomli
from tatoeba_to_anki.generate_anki_deck import generate_anki_deck
from tatoeba_to_anki.prune_sentences import prune_sentences
from tatoeba_to_anki.sort_sentences import order_sentences

# You probably shouldn't change this
AUDIO_DIR = "audio_files"


def load_sentences_from_tsv(tsv_file_path: str) -> pd.DataFrame:
    """
    Loads the sentences from the TSV file.
    """
    with open(tsv_file_path, "r", encoding="utf-8") as f:
        # Read tsv to pandas
        df = pd.read_csv(tsv_file_path, sep="\t", encoding="utf-8")

        df.columns = [
            "sentence_id",
            "sentence_source",
            "target_sentence_id",
            "target_sentence",
        ]
    return df


if __name__ == "__main__":

    # If a parameter is passed, use it as the config file
    if len(sys.argv) > 1:
        config_file = sys.argv[1]
    else:
        config_file = "config.toml"

    with open(config_file, "rb") as f:
        config = tomli.load(f)
    print("Config loaded")
    df = load_sentences_from_tsv(config["sentence_pairs_path"])
    print("Sentences loaded")
    # Order the sentences
    sorted_sentences = order_sentences(df, config["source_language"])
    
    # Print the sentences to a file
    sorted_sentences.to_csv("sorted_sentences_new.tsv", sep="\t", encoding="utf-8")
    
    print("Sentences sorted")
    sentences_with_audio_path = config["sentences_with_audio_path"]

    sorted_sentences = prune_sentences(
        sorted_sentences,
        config["max_sentence_number"],
        get_sentences_with_audio(sentences_with_audio_path),
    )

    audio_downloader = AudioDownloader(
        config["source_language"],
        config["sentences_with_audio_path"],
        audio_dir=AUDIO_DIR,
    )
    # Iterate through the dataframe and download the audio files
    if config["download_mode"] != "None":
        for i in range(len(sorted_sentences)):
            audio_downloader.download_audio(
                sorted_sentences["sentence_id"][i],
                sorted_sentences["sentence_source"][i],
                config["wait_interval"],
                config["download_mode"]
            )
    print("Audio files downloaded")
    # Generate the Anki deck
    generate_anki_deck(sorted_sentences, config)
    print("Anki deck generated")
