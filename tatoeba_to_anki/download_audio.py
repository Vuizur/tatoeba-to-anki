import csv
import os
import time
import requests
from gtts import gTTS


SENTENCES_WITH_AUDIO_PATH = "sentences_with_audio.tsv"


def get_sentences_with_audio(sentences_with_audio_path) -> set[str]:
    sentences_with_audio = set()
    with open(sentences_with_audio_path, "r", encoding="utf-8") as f:
        reader = csv.reader(f, delimiter="\t")
        for row in reader:
            sentences_with_audio.add(row[0])
    return sentences_with_audio


class AudioDownloader:
    def __init__(
        self, language: str, SENTENCES_WITH_AUDIO_PATH: str, audio_dir: str
    ) -> None:
        """
        Initialize the class.
        """
        self.language = language
        self.sentences_with_tatobea_audio = get_sentences_with_audio(
            SENTENCES_WITH_AUDIO_PATH
        )
        self.audio_dir = audio_dir

    def get_audio_path(self, sentence_id: str) -> str:
        """
        Get the audio file path for the given sentence_id.
        """
        return os.path.join(self.audio_dir, sentence_id + ".mp3")

    def download_audio(
        self, sentence_id: str, sentence: str, wait_interval: float
    ) -> None:
        """
        Download the audio file for the given sentence.
        """

        # Check if an audio file with the given sentence_id exists.
        audio_file_path = os.path.join(self.audio_dir, str(sentence_id) + ".mp3")
        if os.path.exists(audio_file_path):
            print("File already exists: " + audio_file_path)
            return
        # if sentence_id in self.sentences_with_tatobea_audio:
        #    print("Downloading audio for sentence_id: " + sentence_id)
        #    # Download the audio file using the given sentence_id using requests
        #    url = "https://tatoeba.org/eng/sentences/audio/" + sentence_id + ".mp3"
        #    response = requests.get(url, stream=True)
        #    with open(audio_file_path, 'wb') as f:
        #        for chunk in response.iter_content(chunk_size=1024):
        #            if chunk:
        #                f.write(chunk)
        #                f.flush()
        #        f.close()
        #        print("Downloaded audio file: " + audio_file_path)
        else:
            # Download the audio file for the given sentence using gTTS
            print("Downloading audio for sentence: " + sentence)
            tts = gTTS(text=sentence, lang=self.language)
            tts.save(audio_file_path)
            print("Downloaded audio file: " + audio_file_path)
            time.sleep(wait_interval)
