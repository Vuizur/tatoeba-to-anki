from sqlalchemy import create_engine, Index

from tatoebatools import tatoeba
from tatoebatools.models import Base, SentenceDetailed


def create_all_encompassing_database():

    engine = create_engine( "sqlite:///./tatoeba.sqlite")

    table_names = ["sentences_detailed", "user_languages", "sentences_with_audio", "links"]

    # create the tables in the database
    tables = [
        Base.metadata.tables[table_name] 
        for table_name in table_names
    ]
    Base.metadata.create_all(bind=engine, tables=tables)

    # insert data into the tables
    for table_name in table_names:
        with tatoeba.get(table_name, ["*"], chunksize=100000) as reader:
            for chunk in reader:
                chunk.to_sql(table_name, con=engine, index=False, if_exists="append")

    with tatoeba.get("links", ["*"], chunksize=100000) as reader:
            for chunk in reader:
                chunk.to_sql("links", con=engine, index=False, if_exists="append")

    # add an index on the 'username' column of the 'sentences_detailed' table
    ix = Index('ix_sentences_detailed_username', SentenceDetailed.username)
    ix.create(engine)


def debug():

    language_pair = ["eng", "deu"]

    engine = create_engine( "sqlite:///./test.sqlite")

    table_names = ["links"]

    # create the tables in the database
    tables = [
        Base.metadata.tables[table_name] 
        for table_name in table_names
    ]
    Base.metadata.create_all(bind=engine, tables=tables)

    # insert data into the tables
    #for table_name in table_names:
    #    with tatoeba.get(table_name, ["*"], chunksize=100000) as reader:
    #        for chunk in reader:
    #            chunk.to_sql(table_name, con=engine, index=False, if_exists="append")

    with tatoeba.get("links", language_pair, chunksize=100000) as reader:
            for chunk in reader:
                chunk.to_sql("links", con=engine, index=False, if_exists="append")

    # add an index on the 'username' column of the 'sentences_detailed' table
    #ix = Index('ix_sentences_detailed_username', SentenceDetailed.username)
    #ix.create(engine)

if __name__ == "__main__":
    debug()


