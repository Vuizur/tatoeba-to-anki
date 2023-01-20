from tatoeba_to_anki import AnkiDeckCreator
from tatoeba_to_anki.download_audio import DownloadMode

if __name__ == "__main__":

    adc = AnkiDeckCreator(
        "Czech",
        "English",
        max_sentence_number=4,
        tts_voices="pl-PL-ZofiaNeural",
    )
    adc.export_anki_deck()
    adc.create_ankiweb_info(9000)

    #adc.export_anki_deck()
    quit()
    envoice = "en-GB-LibbyNeural"
    adc = AnkiDeckCreator(
        "English",
        "Spanish",
        tts_voices=envoice,
        max_sentence_number=5,
        download_and_create_english_dictionary=False,
    )
    adc.export_anki_deck()

    quit()
    # Latin without TTS
    adc = AnkiDeckCreator(
        "Latin",
        "English",
        max_sentence_number=9000,
        tts_voices=[],
        audio_download_mode=DownloadMode.NONE,
        minimum_skill_level=5,
    )
    adc.export_anki_deck()
