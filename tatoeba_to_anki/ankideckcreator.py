import html
import os
from numpy import source
import pycountry
from requests import delete

from sqlalchemy import create_engine, Index
import sqlite3
from sort_sentences import get_sentence_word_frequency
from ebook_dictionary_creator.e_dictionary_creator.dictionary_creator import (
    DictionaryCreator,
)
import genanki

from prune_sentences import are_duplicates

from tatoebatools import tatoeba
from tatoebatools.models import (
    Base,
    SentenceDetailed,
    SentenceWithAudio,
    UserLanguage,
    Link,
    Tag,
)

from generate_anki_deck import generate_dictionary_html
from tabfile_dictionary import TabfileDictionary

from prune_sentences import delete_punctuation


class AnkiDeckCreator:
    def __init__(
        self,
        source_language: str,
        target_language: str,
        deck_id=1329331698,
        model_id=1524505956,
        outdated_tags: list[str] = ["outdated, old-fashioned"],
        audio_folder="audio",
        dictionary_tabfile_path=None,
        minimum_skill_level = 4,
        download_and_create_english_dictionary=True,
        deck_output_path=None,
        deck_name=None,
        deck_description=None,
        deck_author="Vuizur",
        max_sentence_number=10000,
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

        self.minimum_skill_level = minimum_skill_level
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
            self.deck_name = f"{self.source_language} - {self.target_language} frequency sentences deck"
        else:
            self.deck_name = deck_name

        if deck_description == None:
            self.deck_description = f"Frequency sentences deck for {self.source_language} - {self.target_language}"
        else:
            self.deck_description = deck_description

        self.deck_author = deck_author
        self.max_sentence_number = max_sentence_number

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
        self.conn = sqlite3.connect(self.database_name)
        self.cur = self.conn.cursor()
        self.cur.execute(
            "DELETE FROM sentences_detailed WHERE rowid NOT IN (SELECT MIN(rowid) FROM sentences_detailed GROUP BY sentence_id)"
        )
        self.calculate_sentence_frequency()
        # Ok, not safe, but it's good enough for now
        self.cur.execute(
            f"""CREATE VIEW sentences_with_translations AS
                SELECT
                sd1.sentence_id AS source_sentence_id,
                sd1.text AS source_text,
                sd2.sentence_id AS translation_sentence_id,
                sd2.text AS translation_text,
                sentences_with_audio.audio_id AS audio_id,
                sd1.username AS source_username, 
                sd1.frequency,
                user_languages.skill_level AS source_lang_skill_level
                FROM sentences_detailed sd1
                JOIN links l ON sd1.sentence_id = l.sentence_id
                JOIN sentences_detailed sd2 ON l.translation_id = sd2.sentence_id
                LEFT JOIN sentences_with_audio ON sd1.sentence_id = sentences_with_audio.sentence_id
				INNER JOIN user_languages ON user_languages.username = sd1.username
                WHERE user_languages.lang = "{self.source_language_code}" 
                AND sd1.lang = "{self.source_language_code}"
                AND sd2.lang = "{self.target_language_code}"
            """
        )

        self.conn.commit()
        # Sqlalchemy vacuum, but too slow
        # engine.execute("VACUUM")
        self.prune_duplicates()
        # self.delete_sentences_over_max_sentence_number()

    def delete_sentences_over_max_sentence_number(self):
        # TODO: Fix this
        unique_words: set[str] = set()
        sentences_that_contain_unique_words: set[int] = set()
        for row in self.cur.execute(
            """SELECT sentence_id, "text" FROM sentences_detailed WHERE lang=? ORDER BY frequency DESC""",
            (self.source_language_code,),
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
                "SELECT sentence_id FROM sentences_detailed WHERE lang=? ORDER BY RANDOM() LIMIT ?",
                (self.source_language_code, self.max_sentence_number),
            ):
                if len(sentences_that_contain_unique_words) >= self.max_sentence_number:
                    break
                sentences_that_contain_unique_words.add(row[0])

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
        con = sqlite3.connect(self.database_name)
        cur = con.cursor()

        cur.execute(
            "SELECT sentence_id, text FROM sentences_detailed WHERE lang = ?",
            (self.source_language_code,),
        )
        rows = cur.fetchall()
        seen = set()
        for sentence_id, text in rows:
            no_punct = delete_punctuation(text)
            if no_punct in seen:
                cur.execute(
                    "DELETE FROM sentences_detailed WHERE sentence_id = ?",
                    (sentence_id,),
                )
            else:
                seen.add(no_punct)
        con.commit()
        con.close()

    def calculate_sentence_frequency(self):
        # Adds a column to the sentences_detailed table which contains the word frequency of the sentence

        # Calculate the IETF BCP 47 language code
        source_language_ietf_code = pycountry.languages.get(
            name=self.source_language
        ).alpha_2

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
                sentence[1], source_language_ietf_code
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
        dictionary_creator = DictionaryCreator(
            self.source_language, self.target_language
        )
        dictionary_creator.download_data_from_kaikki()
        dictionary_creator.create_database()
        dictionary_creator.export_to_tabfile(tabfile_path=self.dictionary_tabfile_path)

    
    def query_relevant_sentences(self) -> list:
        return self.cur.execute("""SELECT source_sentence_id, source_text, translation_text, audio_id
        FROM sentences_with_translations
        ORDER BY frequency DESC
        """).fetchall()

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

        # Generate ietf language code
        source_language_ietf_code = pycountry.languages.get(
            name=self.source_language
        ).alpha_2

        package = genanki.Package(deck)

        # Get the sentences from the database
        sentences = self.query_relevant_sentences()


        tabfile_dictionary = TabfileDictionary(self.dictionary_tabfile_path)

        card_num = 0

        for source_sentence_id, source_sentence, translation, audio_id in sentences:
            target_sentence_html = f"{html.escape(translation)}{generate_dictionary_html(source_sentence, tabfile_dictionary, source_language_ietf_code)}"

            # if os.path.isfile(
            #    os.path.join("audio_files/", f"{row['sentence_id']}.mp3")
            # ):
            if False:

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
        print("Downloading dictionary...")
        self.download_tabfile_dictionary()
        print("Generating Anki deck...")
        self.generate_anki_deck()

    # Close the database connection when the object is garbage collected
    def __del__(self):
        self.conn.commit()
        self.conn.close()

if __name__ == "__main__":
    adc = AnkiDeckCreator("Czech", "German")
    adc.export_anki_deck()
