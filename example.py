from tatoeba_to_anki import AnkiDeckCreator

if __name__ == "__main__":
    adc = AnkiDeckCreator(
        "Polish", "English", max_sentence_number=15, tts_voices="pl-PL-ZofiaNeural", in_memory_database=False
    )
    
    adc.export_anki_deck()
