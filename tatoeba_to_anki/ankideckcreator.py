import html
import os
import pycountry

from sqlalchemy import create_engine, Index
import sqlite3
from sort_sentences import get_sentence_word_frequency
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

from tatoeba_to_anki.generate_anki_deck import generate_dictionary_html, generate_wiktionary_link_html


class AnkiDeckCreator:
    def __init__(
        self,
        source_language: str,
        target_language: str,
        deck_id=1329331698,
        model_id = 1524505956,
        outdated_tags: list[str] = ["outdated, old-fashioned"],
        audio_folder="audio",
        dictionary_tabfile_path=None,
        only_take_sentences_from_natives=True,
        download_and_create_english_dictionary=True,
        deck_output_path=None,
        deck_name=None,
        deck_description=None,
        deck_author="Vuizur",
    ):
        self.source_language = source_language
        self.target_language = target_language
        # Convert the source language ("English") to the language code ("eng") using pycountry
        self.source_language_code = pycountry.languages.get(
            name=self.source_language
        ).alpha_3
        self.target_language_code = pycountry.languages.get(
            name=self.target_language
        ).alpha_3

        self.deck_id = deck_id
        self.model_id = model_id
        self.database_name = (
            f"{self.source_language_code}_{self.target_language_code}.sqlite"
        )
        self.outdated_tags = outdated_tags

        self.audio_folder = audio_folder
        self.only_take_sentences_from_natives = only_take_sentences_from_natives

        if dictionary_tabfile_path == None and download_and_create_english_dictionary:
            self.dictionary_tabfile_path = (
                f"{self.source_language_code}_{self.target_language_code}.txt"
            )

        if deck_output_path == None:
            self.deck_output_path = (
                f"{self.source_language_code}_{self.target_language_code}.apkg"
            )
        else:
            self.deck_output_path = deck_output_path

        if deck_name == None:
            self.deck_name = f"{self.source_language_code} - {self.target_language_code} frequency sentences deck"
        else:
            self.deck_name = deck_name

        if deck_description == None:
            self.deck_description = f"Frequency sentences deck for {self.source_language_code} - {self.target_language_code}"
        else:
            self.deck_description = deck_description

        self.deck_author = deck_author

    def create_database(self):

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

        ix = Index("ix_sentence_detailed_sentence_id", SentenceDetailed.sentence_id)
        ix.create(engine)
        ix = Index("ix_sentence_detailed_username", SentenceDetailed.username)
        ix.create(engine)
        # sentencedetailed lang index
        ix = Index("ix_sentences_detailed_lang", SentenceDetailed.lang)
        ix.create(engine)
        # links translation_id index
        ix = Index("ix_links_translation_id", Link.translation_id)
        ix.create(engine)
        # links sentence_id index
        ix = Index("ix_links_sentence_id", Link.sentence_id)
        ix.create(engine)
        # sentences_with_audio sentence_id index
        ix = Index("ix_sentences_with_audio_sentence_id", SentenceWithAudio.sentence_id)
        ix.create(engine)
        # user_languages username index
        ix = Index("ix_user_languages_username", UserLanguage.username)
        ix.create(engine)
        # user_languages lang index
        ix = Index("ix_user_languages_lang", UserLanguage.lang)
        ix.create(engine)
        # user_languages skill_level index
        ix = Index("ix_user_languages_skill_level", UserLanguage.skill_level)
        ix.create(engine)

        # tags sentence_id index
        ix = Index("ix_tags_sentence_id", Tag.sentence_id)
        ix.create(engine)
        # tags tag_name index
        ix = Index("ix_tags_tag_name", Tag.tag_name)
        ix.create(engine)

        # Drop duplicate sentence_id rows
        conn = sqlite3.connect(self.database_name)
        c = conn.cursor()
        c.execute(
            "DELETE FROM sentences_detailed WHERE rowid NOT IN (SELECT MIN(rowid) FROM sentences_detailed GROUP BY sentence_id)"
        )
        conn.commit()
        conn.close()
        # Sqlalchemy vacuum, but too slow
        # engine.execute("VACUUM")
        self.calculate_sentence_frequency()

    def query_relevant_sentences(self) -> list:
        conn = sqlite3.connect(self.database_name)
        c = conn.cursor()

        outdated_char_str = ",".join([f'"{char}"' for char in self.outdated_tags])
        # TODO: Kind of insecure, so this shouldn't be put behind a server like this.
        # Also this does quite not work right now and should be done differently.

        result = c.execute(
            f"""SELECT sd1."text", sd2."text", sentences_with_audio.audio_id, tags.tag_name FROM sentences_detailed sd1
            INNER JOIN links ON sd1.sentence_id = links.sentence_id 
            INNER JOIN sentences_detailed sd2 ON sd2.sentence_id = links.translation_id
            LEFT JOIN sentences_with_audio ON sd1.sentence_id = sentences_with_audio.sentence_id
            LEFT JOIN tags ON sd1.sentence_id = tags.sentence_id
            INNER JOIN user_languages ON user_languages.username = sd1.username
            WHERE user_languages.lang = ?
            AND sd1.lang = ?
            AND sd2.lang = ?
            {"AND user_languages.skill_level = 5" if self.only_take_sentences_from_natives else ""}
            AND (tags.tag_name IS NULL OR tags.tag_name NOT IN ({outdated_char_str}))
            """,
            (
                self.source_language_code,
                self.source_language_code,
                self.target_language_code,
            ),
        ).fetchall()
        # Print the result to the file "test.txt"
        with open("test.txt", "w", encoding="utf-8") as f:
            for row in result:
                f.write(str(row) + "\n")

        conn.close()

        return result

    def calculate_sentence_frequency(self):
        # Adds a column to the sentences_detailed table which contains the word frequency of the sentence
        conn = sqlite3.connect(self.database_name)

        # Calculate the IETF BCP 47 language code
        source_language_ietf_code = pycountry.languages.get(
            name=self.source_language
        ).alpha_2

        c = conn.cursor()
        c.execute("""ALTER TABLE sentences_detailed ADD COLUMN frequency INTEGER""")

        # Use the get_sentence_word_frequency function to get the word frequency of each sentence
        c.execute(
            """SELECT sentence_id, text FROM sentences_detailed WHERE lang = ?""",
            (self.source_language_code,),
        )

        sentences = c.fetchall()
        for sentence in sentences:
            frequency = get_sentence_word_frequency(
                sentence[1], source_language_ietf_code
            )
            c.execute(
                """UPDATE sentences_detailed SET frequency = ? WHERE sentence_id = ?""",
                (frequency, sentence[0]),
            )

        # Add the index to the frequency column
        c.execute(
            """CREATE INDEX ix_sentences_detailed_frequency ON sentences_detailed (frequency)"""
        )
        c.execute("COMMIT")
        conn.close()

    def download_tabfile_dictionary(self):
        dictionary_creator = DictionaryCreator(
            self.source_language, self.target_language
        )
        dictionary_creator.download_data_from_kaikki()
        dictionary_creator.create_database()
        dictionary_creator.export_to_tabfile(tabfile_path=self.dictionary_tabfile_path)

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
        deck = genanki.Deck(
            self.deck_id, self.deck_name, self.deck_description
        )
        # Create a new Anki model using genanki
        audio_note_model = genanki.Model(
            self.model_id,
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

        package = genanki.Package(deck)

        # Get the sentences from the database
        sentences = self.query_relevant_sentences()

        for source_sentence, translation, _, _ in sentences:
            pass

        # Iterate through the sorted sentences and add them to the Anki deck
        for index, row in sorted_sentences.iterrows():
            target_sentence = row["target_sentence"]
            if config["single_word_lookup_mode"] == "Wiktionary":
                target_sentence_html = f"{html.escape(target_sentence)}{generate_wiktionary_link_html(row['sentence_source'], config['wiktionary_base_url'], config['wiktionary_source_language'], config['source_language'])}"
            elif config["single_word_lookup_mode"] == "Dictionary":
                target_sentence_html = f"{html.escape(target_sentence)}{generate_dictionary_html(row['sentence_source'], dictionary, config['source_language'])}"
            else:
                target_sentence_html = html.escape(target_sentence)
            # Create a new Anki note using genanki depending on whether an audio file for it exists
            if os.path.isfile(
                os.path.join("audio_files/", f"{row['sentence_id']}.mp3")
            ):

                note = genanki.Note(
                    model=audio_note_model,
                    fields=[
                        html.escape(row["sentence_source"]),
                        target_sentence_html,
                        f"[sound:{row['sentence_id']}.mp3]",
                    ],
                )
            else:
                note = genanki.Note(
                    model=no_audio_model,
                    fields=[
                        html.escape(row["sentence_source"]),
                        target_sentence_html,
                    ],
                )
            # Add the note to the Anki deck
            deck.add_note(note)

        package.write_to_file(self.deck_output_path)

adc = AnkiDeckCreator("Czech", "English")
adc.create_database()
adc.query_relevant_sentences()
