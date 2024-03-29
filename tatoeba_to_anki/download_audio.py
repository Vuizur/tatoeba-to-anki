from dataclasses import dataclass
from enum import Enum
import os
import random
import time
import requests
import edge_tts
from edge_tts.list_voices import VoicesManager
import asyncio


async def download_edge(text: str, voice: str, output_path: str) -> None:
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_path)


async def get_correct_voices(language: str, gender: str) -> list[str]:
    voices = await VoicesManager.create()
    return voices.find(Language=language, Gender=gender)


def get_available_voices(
    language_code: str, gender: str = "Female"
) -> list[
    str
]:  # We choose random female voices -> Only one gender because otherwise people would get confused that gender-specific
    """The language code has to be 2 letters long."""  # sentences randomly get voiced by the wrong gender

    available_voices = asyncio.get_event_loop().run_until_complete(
        get_correct_voices(language=language_code, gender=gender)
    )
    return [voice["Name"] for voice in available_voices]


async def all_langs() -> list[str]:
    voices = await VoicesManager.create()
    return voices.find()


def get_all_languages() -> list[str]:
    """Get all voices."""
    voices: dict = asyncio.get_event_loop().run_until_complete(
        all_langs()  # type: ignore
    )
    # Find all unique language keys
    languages = set()
    for voice in voices:
        languages.add(voice["Language"])
    return list(languages)


@dataclass
class Sentence:
    sentence_id: int
    sentence_text: str
    sentence_tatoeba_audio_id: int


DownloadMode = Enum("DownloadMode", "TATOEBA_AND_TTS TATOEBA NONE")


class AudioDownloader:
    def __init__(
        self,
        sentences_to_download: list[Sentence],
        audio_dir: str,
        tts_voices: str | list[str],
        download_mode: DownloadMode,
        wait_interval: float = 1.0,
    ) -> None:
        """
        Initialize the class.
        """
        self.audio_dir = audio_dir
        self.tts_voices = tts_voices
        self.sentences_to_download = sentences_to_download
        self.download_mode = download_mode
        self.wait_interval = wait_interval

    def waitonce(self):
        # Multiply the wait interval by a random number between 0.5 and 1.5
        waiting_time = self.wait_interval * (0.5 + (0.5 * random.random()))

        time.sleep(waiting_time)

    def download_edge_audio_new(self, sentence: str, filename: str):
        if isinstance(self.tts_voices, list):
            voice = random.choice(self.tts_voices)
        else:
            voice = self.tts_voices

        asyncio.get_event_loop().run_until_complete(
            download_edge(sentence, voice, filename)
        )

        # with open(f"{filename}.txt", "w", encoding="utf-8") as f:
        #    f.write(sentence)

    #
    # command = f'edge-tts --file "{filename}.txt" --write-media "{filename}" --voice {voice}'
    ## Delete the text file
    # subprocess.check_output(command, shell=True)#
    # os.remove(f"{filename}.txt")

    def get_audio_path(self, sentence_id: str) -> str:
        """
        Get the audio file path for the given sentence_id.
        """
        return os.path.join(self.audio_dir, sentence_id + ".mp3")

    def download_audio(
        self, sentence_id: int, sentence: str, sentence_tatoeba_audio_id: int
    ) -> None:
        """
        Download the audio file for the given sentence.
        """

        if self.download_mode == DownloadMode.NONE:
            print("No audio download")
            return

        # Check if an audio file with the given sentence_id exists.
        audio_file_path = os.path.join(self.audio_dir, f"{sentence_id}.mp3")
        if os.path.exists(audio_file_path):
            print("File already exists: " + audio_file_path)
            return

        self.waitonce()
        if sentence_tatoeba_audio_id != None:
            print(f"Downloading audio for sentence_id from Tatoeba: {sentence_id}")
            # Download the audio file using the given sentence_id using requests
            url = f"https://tatoeba.org/audio/download/{sentence_tatoeba_audio_id}"
            response = requests.get(url, stream=True)
            with open(audio_file_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=1024):
                    if chunk:
                        f.write(chunk)
                        f.flush()
                f.close()
                print(f"Downloaded audio file: {audio_file_path}")

        else:
            if self.download_mode == DownloadMode.TATOEBA_AND_TTS:
                # Download the audio file for the given sentence using edge-tts
                print(f"Downloading audio for sentence: {sentence}")
                # tts = gTTS(text=sentence, lang=self.language)
                # tts.save(audio_file_path)
                self.download_edge_audio_new(sentence, audio_file_path)
                print("Downloaded audio file: " + audio_file_path)
                self.waitonce()

    def download_all_audio(self):
        if self.download_mode == DownloadMode.NONE:
            print("No audio download")
            return
        # Create the audio directory if it doesn't exist
        if not os.path.exists(self.audio_dir):
            os.makedirs(self.audio_dir)
        for sentence in self.sentences_to_download:
            self.download_audio(
                sentence.sentence_id,
                sentence.sentence_text,
                sentence.sentence_tatoeba_audio_id,
            )


if __name__ == "__main__":

    # print(get_available_voices("es", "Female"))
    print(get_all_languages())

    quit()

    # u89
    voice1 = "cs-CZ-VlastaNeural"
    voice = "cs-CZ-AntoninNeural"

    ad = AudioDownloader([], "test_aud", voice1, DownloadMode.TATOEBA_AND_TTS)
    ad.download_edge_audio_new("Ta by měla vznikat za nového zadání.", "test3.mp3")
