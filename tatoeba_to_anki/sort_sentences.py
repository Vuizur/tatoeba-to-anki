import math
import pandas as pd
import wordfreq

# Some code inspired from https://github.com/kmicklas/sentence-pairs/blob/master/sort.py
def get_sentence_word_frequency(sentence: str, source_lang: str) -> float:

    words = wordfreq.tokenize(sentence, source_lang)
    #
    freqs = [wordfreq.zipf_frequency(word, source_lang) for word in words]
    avgfreq = sum(freqs) / float(len(freqs))
    sentence_length = len(words)
    # Calculate log value of sentence_length
    sentence_length_log = 0.0
    if sentence_length > 0:
        sentence_length_log = math.log(sentence_length)
    return avgfreq - sentence_length_log


def order_sentences(df: pd.DataFrame, source_lang: str) -> pd.DataFrame:
    # Remove columns with duplicate sentence_id (keep first occurence)
    df.drop_duplicates(subset=["sentence_id"], keep="first", inplace=True)
    # Add a column with the sentence word frequency
    df["sentence_word_frequency"] = df["sentence_source"].apply(
        lambda sentence: get_sentence_word_frequency(sentence, source_lang)
    )
    # Sort the dataframe by sentence word frequency
    df = df.sort_values(by=["sentence_word_frequency"], ascending=False)
    # Turn pandas dataframe continuous again
    df = df.reset_index(drop=True)
    return df
