import os
from tatoeba_to_anki.all_langs_helpers import (
    get_all_langs_that_have_voice_and_word_frequency,
)
from tatoeba_to_anki.ankideckcreator import AnkiDeckCreator
import pycountry


class AllDeckCreator:
    def __init__(
        self, max_sentence_number: int = 9001, progress_file: str = "progress.txt"
    ):
        self.max_sentence_number = max_sentence_number
        self.progress_file = progress_file
        self.langs_already_done = self.get_langs_already_done()

    def get_langs_already_done(self) -> list[str]:
        """Get all languages that have already been done."""
        if not os.path.exists(self.progress_file):
            return []

        with open(self.progress_file, "r", encoding="utf-8") as f:
            return f.read().splitlines()

    def create_decks_for_all_languages(self) -> None:
        """Create decks for all languages."""
        langs = get_all_langs_that_have_voice_and_word_frequency()
        # Sort the languages alphabetically
        langs.sort()
        for lang in langs:
            print(lang)
            if lang in self.langs_already_done or lang == "en":
                continue
            elif lang == "ms" or lang == "lv":
                continue  # TODO There are some issues with language codes, must investivate
            elif lang == "sv":
                continue # Here the dictionary is not working yet
            elif lang == "fa":  # Persian
                lang_name = pycountry.languages.get(
                    alpha_3="pes"
                ).name  # This is Iranian Persian. The only thing supported by Tatoeba
            elif lang == "fil":
                lang_name = pycountry.languages.get(alpha_3="fil").name
            else:
                lang_name = pycountry.languages.get(alpha_2=lang).name
            adc = AnkiDeckCreator(
                lang_name,
                "English",
                max_sentence_number=9001,
            )
            adc.export_anki_deck()
            with open(self.progress_file, "a", encoding="utf-8") as f:
                f.write(f"{lang}\n")
