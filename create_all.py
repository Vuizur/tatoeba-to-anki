from tatoeba_to_anki.create_all_decks import AllDeckCreator

if __name__ == "__main__":
    adc = AllDeckCreator()
    adc.create_decks_for_all_languages()