from os.path import isfile
import html
import os

import pycountry

from sqlalchemy import create_engine, Index
import sqlite3
from tatoeba_to_anki.sort_sentences import get_sentence_word_frequency
from ebook_dictionary_creator.e_dictionary_creator.dictionary_creator import (
    DictionaryCreator,
)
import genanki
from tatoebatools import tatoeba
from tatoebatools.models import (
    Base,
    SentenceDetailed,
    SentenceWithAudio,
    UserLanguage,
    Link,
    Tag,
)

from tatoeba_to_anki.generate_anki_deck import generate_dictionary_html
from tabfile_dictionary import TabfileDictionary
from tatoeba_to_anki.prune_sentences import delete_punctuation
from tatoeba_to_anki.download_audio import (
    AudioDownloader,
    DownloadMode,
    Sentence,
    get_available_voices,
)

FORBIDDEN_LOCALES = ["de-CH"]  # Sorry friends from Switzerland


class AnkiDeckCreator:
    def __init__(
        self,
        source_language: str,
        target_language: str,
        tts_voices: str
        | list[str]
        | None = None,  # Will be figured out by the program if None
        outdated_tags: list[str] = ["outdated, old-fashioned"],
        audio_folder="audio",
        dictionary_tabfile_path=None,
        minimum_skill_level=5,
        number_of_common_sentences_where_minimum_skill_level_should_not_be_applied=100,
        download_and_create_english_dictionary=True,
        audio_download_mode=DownloadMode.TATOEBA_AND_TTS,
        in_memory_database=False,  # This currently does not work, do not change it.
        deck_output_path=None,
        deck_name=None,
        deck_description=None,
        deck_author="Vuizur",
        max_sentence_number=9001,
        deck_id=None,
        waiting_time=0.20,
    ):
        if deck_id is None:
            # Hash the source and target language to get a unique deck id
            self.deck_id = hash(source_language + target_language)
        else:
            self.deck_id = deck_id

        self.source_language = source_language
        self.target_language = target_language
        # Convert the source language ("English") to the language code ("eng")
        # using pycountry
        if self.source_language == "Filipino":
            self.source_language_code = "tgl"  # This is what Tatoeba uses
        else:
            self.source_language_code = pycountry.languages.get(
                name=self.source_language
            ).alpha_3
        self.target_language_code = pycountry.languages.get(
            name=self.target_language
        ).alpha_3

        if self.source_language == "Iranian Persian":
            self.source_language_code2 = "fa"  # This doesn't work using pycountry
        elif self.source_language == "Filipino":
            self.source_language_code2 = "fil"  # This is what Edge TTS uses
        else:
            self.source_language_code2 = pycountry.languages.get(
                name=self.source_language
            ).alpha_2

        if not in_memory_database:
            self.database_name = (
                f"{self.source_language_code}_{self.target_language_code}.sqlite"
            )
        else:
            self.database_name = ":memory:"
        self.outdated_tags = outdated_tags
        self.download_mode = audio_download_mode

        if tts_voices is None:
            self.tts_voices = [
                voice
                for voice in get_available_voices(self.source_language_code2)
                if not any(
                    voice.startswith(forbidden_locale)
                    for forbidden_locale in FORBIDDEN_LOCALES
                )
            ]
            print(self.tts_voices)
        else:
            self.tts_voices = tts_voices

        self.audio_folder = audio_folder

        # if audio folder does not exist, create it
        if not os.path.exists(self.audio_folder):
            os.makedirs(self.audio_folder)

        self.minimum_skill_level = minimum_skill_level
        if dictionary_tabfile_path is None and download_and_create_english_dictionary:
            self.dictionary_tabfile_path = (
                f"{self.source_language_code}_{self.target_language_code}.txt"
            )
        else:
            self.dictionary_tabfile_path = dictionary_tabfile_path

        self.download_and_create_english_dictionary = (
            download_and_create_english_dictionary
        )

        if deck_output_path is None:
            self.deck_output_path = (
                f"{self.source_language_code}_{self.target_language_code}.apkg"
            )
        else:
            self.deck_output_path = deck_output_path

        if deck_name is None:
            self.deck_name = f"{self.source_language} - {self.target_language} frequency sentences deck"
        else:
            self.deck_name = deck_name

        if deck_description is None:
            self.deck_description = f"Frequency sentences deck for {self.source_language} - {self.target_language}"
        else:
            self.deck_description = deck_description

        # This is needed to not delete the word for "yes" if it randomly got added by a beginner
        self.number_of_common_sentences_where_minimum_skill_level_should_not_be_applied = (
            number_of_common_sentences_where_minimum_skill_level_should_not_be_applied
        )
        self.deck_author = deck_author
        self.max_sentence_number = max_sentence_number
        self.waiting_time = waiting_time

    def create_database(self):

        # If the database already exists, delete it
        if self.database_name != ":memory:" and os.path.exists(self.database_name):
            os.remove(self.database_name)

        engine = create_engine(f"sqlite:///{self.database_name}")

        langs = [self.source_language_code, self.target_language_code]

        table_names = [
            "sentences_detailed",
            "user_languages",
            "sentences_with_audio",
            "tags",
        ]

        # create the tables in the database
        tables = [Base.metadata.tables[table_name] for table_name in table_names]
        Base.metadata.create_all(bind=engine, tables=tables)

        # insert data into the tables
        for lang in langs:
            for table_name in table_names:
                with tatoeba.get(table_name, [lang], chunksize=100000) as reader:
                    for chunk in reader:
                        chunk.to_sql(
                            table_name, con=engine, index=False, if_exists="append"
                        )

        with tatoeba.get("links", langs, chunksize=100000) as reader:
            for chunk in reader:
                chunk.to_sql("links", con=engine, index=False, if_exists="append")
        # https://stackoverflow.com/questions/55271904/sqlalchemy-with-multiple-databases-and-error-due-to-duplicate-index-creation
        # Is this bugged because of this? Damn ORMs, are you even serious...
        # ix = Index("ix_sentence_detailed_sentence_id", SentenceDetailed.sentence_id)
        # ix.create(engine)
        # Do it manually
        engine.execute(
            "CREATE INDEX ix_sentence_detailed_sentence_id ON sentences_detailed (sentence_id)"
        )
        # ix = Index("ix_sentence_detailed_username", SentenceDetailed.username)
        # ix.create(engine)
        engine.execute(
            "CREATE INDEX ix_sentence_detailed_username ON sentences_detailed (username)"
        )
        # sentencedetailed lang index
        # ix = Index("ix_sentences_detailed_lang", SentenceDetailed.lang)
        # ix.create(engine)
        engine.execute(
            "CREATE INDEX ix_sentences_detailed_lang ON sentences_detailed (lang)"
        )
        # links translation_id index
        # ix = Index("ix_links_translation_id", Link.translation_id)
        # ix.create(engine)
        engine.execute("CREATE INDEX ix_links_translation_id ON links (translation_id)")
        # links sentence_id index
        # ix = Index("ix_links_sentence_id", Link.sentence_id)
        # ix.create(engine)
        engine.execute("CREATE INDEX ix_links_sentence_id ON links (sentence_id)")
        # sentences_with_audio sentence_id index
        # ix = Index("ix_sentences_with_audio_sentence_id", SentenceWithAudio.sentence_id)
        # ix.create(engine)
        engine.execute(
            "CREATE INDEX ix_sentences_with_audio_sentence_id ON sentences_with_audio (sentence_id)"
        )
        # user_languages username index
        # ix = Index("ix_user_languages_username", UserLanguage.username)
        # ix.create(engine)
        engine.execute(
            "CREATE INDEX ix_user_languages_username ON user_languages (username)"
        )
        # user_languages lang index
        # ix = Index("ix_user_languages_lang", UserLanguage.lang)
        # ix.create(engine)
        engine.execute("CREATE INDEX ix_user_languages_lang ON user_languages (lang)")
        # user_languages skill_level index
        # ix = Index("ix_user_languages_skill_level", UserLanguage.skill_level)
        # ix.create(engine)
        engine.execute(
            "CREATE INDEX ix_user_languages_skill_level ON user_languages (skill_level)"
        )

        # tags sentence_id index
        # ix = Index("ix_tags_sentence_id", Tag.sentence_id)
        # ix.create(engine)
        engine.execute("CREATE INDEX ix_tags_sentence_id ON tags (sentence_id)")
        # tags tag_name index
        # ix = Index("ix_tags_tag_name", Tag.tag_name)
        # ix.create(engine)
        engine.execute("CREATE INDEX ix_tags_tag_name ON tags (tag_name)")

        # Drop duplicate sentence_id rows
        self.conn = sqlite3.connect(self.database_name)
        self.cur = self.conn.cursor()
        self.cur.execute(
            "DELETE FROM sentences_detailed WHERE rowid NOT IN (SELECT MIN(rowid) FROM sentences_detailed GROUP BY sentence_id)"
        )
        self.calculate_sentence_frequency()
        # Ok, not safe, but it's good enough for now
        query = f"""CREATE VIEW sentences_with_translations AS
                WITH swt_tmp (source_sentence_id, source_text, translation_sentence_id, translation_text, audio_id, source_username, frequency, source_lang_skill_level, rn)
                AS (
                    SELECT
                    sd1.sentence_id AS source_sentence_id,
                    sd1.text AS source_text,
                    sd2.sentence_id AS translation_sentence_id,
                    sd2.text AS translation_text,
                    sentences_with_audio.audio_id AS audio_id,
                    sd1.username AS source_username, 
                    sd1.frequency,
                    user_languages.skill_level AS source_lang_skill_level,
                    --ROW_NUMBER() OVER (PARTITION BY sd1.sentence_id ORDER BY sd1.sentence_id) AS rn
                    ROW_NUMBER() OVER (ORDER BY sd1.frequency DESC) AS rn
                    FROM sentences_detailed sd1
                    JOIN links l ON sd1.sentence_id = l.sentence_id
                    JOIN sentences_detailed sd2 ON l.translation_id = sd2.sentence_id
                    LEFT JOIN sentences_with_audio ON sd1.sentence_id = sentences_with_audio.sentence_id
				    INNER JOIN user_languages ON user_languages.username = sd1.username
                    WHERE user_languages.lang = "{self.source_language_code}" 
                    AND sd1.lang = "{self.source_language_code}"
                    AND sd2.lang = "{self.target_language_code}"
                    --AND (rn < {self.number_of_common_sentences_where_minimum_skill_level_should_not_be_applied} OR user_languages.skill_level >= {self.minimum_skill_level})
                )
                SELECT * FROM swt_tmp
                WHERE rn <= {self.number_of_common_sentences_where_minimum_skill_level_should_not_be_applied} OR source_lang_skill_level >= {self.minimum_skill_level}
            """
        # print query to file
        with open("query.txt", "w") as f:
            f.write(query)
        self.cur.execute(query)

        self.conn.commit()
        # Sqlalchemy vacuum, but too slow
        # engine.execute("VACUUM")

        self.prune_duplicates()
        self.delete_sentences_over_max_sentence_number()

    def delete_sentences_over_max_sentence_number(
        self,  # , prefer_sentences_where_audio_already_has_been_downloaded=True
    ) -> None:
        # TODO: Fix this
        unique_words: set[str] = set()
        sentences_that_contain_unique_words: set[int] = set()

        # Select all sentences that have native audio so that we have all of them
        result = self.cur.execute(
            f"""
                SELECT
                stwtd.source_sentence_id
                FROM sentences_with_translations stwtd
                WHERE stwtd.audio_id IS NOT NULL
                ORDER BY source_lang_skill_level DESC, frequency DESC
                LIMIT {self.max_sentence_number}
        """
        ).fetchall()
        sentences_that_contain_unique_words.update([entry[0] for entry in result])

        # Look in the audio files folder and get all file names
        already_downloaded_file_ids = [
            f.replace(".mp3", "")
            for f in os.listdir(self.audio_folder)
            if isfile(os.path.join(self.audio_folder, f))
        ]
        # Select all sentences in the source language that have one of the already_downloaded_file_ids associated with them
        result = self.cur.execute(
            f"""
                SELECT
                stwtd.source_sentence_id
                FROM sentences_with_translations stwtd
                WHERE stwtd.audio_id IN ({",".join(already_downloaded_file_ids)})
                ORDER BY source_lang_skill_level DESC, frequency DESC
                LIMIT {self.max_sentence_number}
            """
        ).fetchall()
        # Add the sentences to the set, but the set should not grow larger than max_sentence_number
        max_num_of_sentences_to_add = self.max_sentence_number - len(
            sentences_that_contain_unique_words
        )
        sentences_that_contain_unique_words.update(
            [entry[0] for entry in result][:max_num_of_sentences_to_add]
        )

        for row in self.cur.execute(
            """SELECT source_sentence_id, source_text FROM sentences_with_translations ORDER BY audio_id IS NULL, source_lang_skill_level DESC, frequency DESC"""
        ):
            # Check if the sentence contains at least one unique word
            unique_words_of_the_sentence = (
                set([delete_punctuation(word.lower()) for word in row[1].split(" ")])
                - unique_words
            )
            if len(unique_words_of_the_sentence) > 0:
                unique_words.update(unique_words_of_the_sentence)
                sentences_that_contain_unique_words.add(row[0])
            if len(sentences_that_contain_unique_words) >= self.max_sentence_number:
                break
        if len(sentences_that_contain_unique_words) < self.max_sentence_number:
            # Add random sentences to reach the max_sentence_number
            for row in self.cur.execute(
                """SELECT source_sentence_id FROM sentences_with_translations 
                ORDER BY RANDOM() LIMIT ?""",
                (self.max_sentence_number,),
            ):
                if len(sentences_that_contain_unique_words) >= self.max_sentence_number:
                    break
                sentences_that_contain_unique_words.add(row[0])

        # This bit was? broken
        translation_ids_to_keep = []
        for row in self.cur.execute(
            "SELECT translation_id FROM links WHERE sentence_id IN ({})".format(
                ",".join("?" * len(sentences_that_contain_unique_words))
            ),
            tuple(sentences_that_contain_unique_words),
        ):
            translation_ids_to_keep.append(row[0])

        ids_to_keep = (
            list(sentences_that_contain_unique_words) + translation_ids_to_keep
        )
        self.cur.execute(
            "DELETE FROM sentences_detailed WHERE sentence_id NOT IN ({})".format(
                ",".join("?" * len(ids_to_keep))
            ),
            tuple(ids_to_keep),
        )

        self.conn.commit()

    def prune_duplicates(self):

        self.cur.execute(
            "SELECT sentence_id, text FROM sentences_detailed WHERE lang = ?",
            (self.source_language_code,),
        )
        rows = self.cur.fetchall()
        seen = set()
        for sentence_id, text in rows:
            no_punct = delete_punctuation(text)
            if no_punct in seen:
                self.cur.execute(
                    "DELETE FROM sentences_detailed WHERE sentence_id = ?",
                    (sentence_id,),
                )
            else:
                seen.add(no_punct)

        # Keep only one translation per source sentence
        self.cur.execute(
            """SELECT sentence_id, translation_id FROM links WHERE sentence_id IN 
            (SELECT sentence_id FROM sentences_detailed WHERE lang = ?)""",
            (self.source_language_code,),
        )
        rows = self.cur.fetchall()

        # This deletes duplicate translations
        seen = set()
        for sentence_id, translation_id in rows:
            if sentence_id in seen:
                self.cur.execute(
                    "DELETE FROM links WHERE sentence_id = ? AND translation_id = ?",
                    (sentence_id, translation_id),
                )
                self.cur.execute(
                    "DELETE FROM sentences_detailed WHERE sentence_id = ?",
                    (translation_id,),
                )
            else:
                seen.add(sentence_id)

        self.conn.commit()

    def calculate_sentence_frequency(self):
        # Adds a column to the sentences_detailed table which contains the word frequency of the sentence

        # Calculate the IETF BCP 47 language code
        # source_language_ietf_code = pycountry.languages.get(
        #    name=self.source_language
        # ).alpha_2

        self.cur.execute(
            """ALTER TABLE sentences_detailed ADD COLUMN frequency INTEGER"""
        )

        # Use the get_sentence_word_frequency function to get the word frequency of each sentence
        self.cur.execute(
            """SELECT sentence_id, text FROM sentences_detailed WHERE lang = ?""",
            (self.source_language_code,),
        )

        sentences = self.cur.fetchall()
        for sentence in sentences:
            frequency = get_sentence_word_frequency(
                sentence[1], self.source_language_code2
            )
            self.cur.execute(
                """UPDATE sentences_detailed SET frequency = ? WHERE sentence_id = ?""",
                (frequency, sentence[0]),
            )

        # Add the index to the frequency column
        self.cur.execute(
            """CREATE INDEX ix_sentences_detailed_frequency ON sentences_detailed (frequency)"""
        )
        self.cur.execute("COMMIT")

    def download_tabfile_dictionary(self):
        if self.source_language_code == "ell":
            source_language = (
                "Greek"  # Kaikki does not like the "Modern Greek (1453-)" language name
            )
        elif self.source_language_code == "pes":
            source_language = "Persian"  # Kaikki does not know Iranian Persian
        elif self.source_language_code == "tgl":
            source_language = "Tagalog"
        else:
            source_language = self.source_language
        dictionary_creator = DictionaryCreator(source_language, self.target_language)
        dictionary_creator.download_data_from_kaikki()
        dictionary_creator.create_database()
        dictionary_creator.export_to_tabfile(tabfile_path=self.dictionary_tabfile_path)

    def query_relevant_sentences(self) -> list:
        return self.cur.execute(
            """SELECT source_sentence_id, source_text, translation_text, audio_id
        FROM sentences_with_translations
        ORDER BY frequency DESC
        """
        ).fetchall()

    def generate_anki_deck(self):
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
        deck = genanki.Deck(self.deck_id, self.deck_name, self.deck_description)
        # Create a new Anki model using genanki
        audio_note_model = genanki.Model(
            1329331698,
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
        no_audio_model = genanki.Model(
            1414956686,
            "Simple Model",
            fields=[
                {"name": "Question"},
                {"name": "Answer"},
            ],
            templates=[
                {
                    "name": "Card 1",
                    "qfmt": "{{Question}}",
                    "afmt": '{{FrontSide}}<hr id="answer">{{Answer}}',
                },
            ],
            css=css_s,
        )

        # Generate ietf language code
        # source_language_ietf_code = pycountry.languages.get(
        #    name=self.source_language
        # ).alpha_2

        package = genanki.Package(deck)

        # Get the sentences from the database
        sentences = self.query_relevant_sentences()
        sentences_to_download_audio = [
            Sentence(sentence_id, sentence_text, sentence_tatoeba_audio_id)
            for sentence_id, sentence_text, _, sentence_tatoeba_audio_id in sentences
        ]
        ad = AudioDownloader(
            sentences_to_download_audio,
            self.audio_folder,
            self.tts_voices,
            self.download_mode,
            self.waiting_time,
        )
        ad.download_all_audio()
        if self.download_mode != DownloadMode.NONE:
            audiofile_paths = [
                f"{self.audio_folder}/{source_sentence_id}.mp3"
                for source_sentence_id, _, _, _ in sentences
            ]

            package.media_files = audiofile_paths

        if self.dictionary_tabfile_path is not None:
            tabfile_dictionary = TabfileDictionary(self.dictionary_tabfile_path)

        card_num = 0

        for source_sentence_id, source_sentence, translation, audio_id in sentences:
            if self.dictionary_tabfile_path is not None:
                target_sentence_html = f"{html.escape(translation)}{generate_dictionary_html(source_sentence, tabfile_dictionary, self.source_language_code2)}"
            else:
                target_sentence_html = f"{html.escape(translation)}"
            if (
                os.path.isfile(f"{self.audio_folder}/{source_sentence_id}.mp3")
                and not self.download_mode == DownloadMode.NONE
            ):
                # if False:
                note = genanki.Note(
                    model=audio_note_model,
                    fields=[
                        html.escape(source_sentence),
                        target_sentence_html,
                        f"[sound:{source_sentence_id}.mp3]",
                    ],
                )
            else:
                note = genanki.Note(
                    model=no_audio_model,
                    fields=[
                        html.escape(source_sentence),
                        target_sentence_html,
                    ],
                )
            # Add the note to the Anki deck
            deck.add_note(note)
            card_num += 1
            # Print the progress every 1000 sentences
            if (card_num % 1000) == 0:
                print(f"Added {card_num} cards")

        package.write_to_file(self.deck_output_path)

    def export_anki_deck(self):
        print("Creating database...")
        self.create_database()
        if self.download_and_create_english_dictionary:
            print("Downloading dictionary...")
            self.download_tabfile_dictionary()
        print("Generating Anki deck...")
        self.generate_anki_deck()

    # Close the database connection when the object is garbage collected (Note: this might be buggy)
    # def __del__(self):
    #    self.conn.commit()
    #    self.conn.close()

    def create_ankiweb_info(self, final_number_of_sentences: int):
        title = f"{final_number_of_sentences} {self.source_language} sentences with audio, ordered by difficulty + containing word definitions"
        description = f"""This deck contains {final_number_of_sentences} {self.source_language} sentences with audio ordered by difficulty. 
        
Additionally, it includes the definitions of individual words from Wiktionary directly written on the cards so that you don't have to look them up online.

The deck has been created with my open source program [tatoeba-to-anki](https://github.com/Vuizur/tatoeba-to-anki). So if you find any errors or have feedback, you can also open an issue there.
        """

        # Print the AnkiWeb info to a file
        with open(f"{self.deck_output_path}.ankiweb_info", "w") as f:
            f.write(f"title: {title}\n")
            f.write(f"description: {description}\n")


if __name__ == "__main__":
    voices = ["de-AT-IngridNeural", "de-CH-LeniNeural", "test"]
    print(
        [
            voice
            for voice in voices
            if not any(
                voice.startswith(forbidden_locale)
                for forbidden_locale in FORBIDDEN_LOCALES
            )
        ]
    )
