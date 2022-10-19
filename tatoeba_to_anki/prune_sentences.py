from enum import Enum
import random
import pandas as pd
import wordfreq


def delete_punctuation(sentence: str) -> str:
    """
    Deletes the punctuation from the sentence.
    """
    return (
        sentence.replace(".", "")
        .replace(",", "")
        .replace(":", "")
        .replace(";", "")
        .replace("!", "")
        .replace("?", "")
        .replace("(", "")
        .replace(")", "")
        .replace("[", "")
        .replace("]", "")
        .replace("{", "")
        .replace("}", "")
        .replace('"', "")
        .replace("'", "")
        .replace("„", "")
        .replace("“", "")
    )


def are_duplicates(sentence1: str, sentence2: str) -> bool:
    """
    Checks if two sentences are duplicates with only different punctuation
    """
    sentence1 = delete_punctuation(sentence1)
    sentence2 = delete_punctuation(sentence2)
    return sentence1 == sentence2


PruneSentenceMode = Enum("PruneSentenceMode", "S random")


def prune_sentences(
    df: pd.DataFrame, max_sentence_num: int, sentences_with_audio
) -> pd.DataFrame:
    """
    Prunes the sentences to the max_sentence_num.
    """
    # Create a set of sentences without punctuation
    sentences_set = set()
    # Iterate over all sentence_source fields and remove duplicates
    for i in range(len(df)):
        sentence = df["sentence_source"][i]
        sentence_without_punctuation = delete_punctuation(sentence)
        if sentence_without_punctuation in sentences_set:
            print(sentence)
            # Delete sentence
            df = df.drop(i)
        else:
            sentences_set.add(sentence_without_punctuation)

    # In rare cases a row is not correctly loaded because of quotes, so we need to remove it
    df = df.dropna()

    df = df.reset_index(drop=True)

    # If there are less sentences than max_sentence_num, return the dataframe
    if len(df) <= max_sentence_num:
        return df

    # Return the first max_sentence_num sentences
    return df.head(max_sentence_num)

    ## Create a frequency list of the words of the sentences
    # word_freq = {}
    # for i in range(len(df)):
    #    for word in wordfreq.tokenize, df["sentence_source"][i]():
    #        if word in word_freq:
    #            word_freq[word] += 1
    #        else:
    #            word_freq[word] = 1

    # Maybe delete the sentences where the rarest word occurs very often, preferably longer ones
    # Or iterate over everything and skip all sentences where there is no new word (they only get added on the second run)
    # Until the max number of sentences is reached
    # Maybe delete sentences from behind that only consist of duplicate words
#
