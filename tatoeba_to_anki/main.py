

# Load the TSV file with the list of sentences
import csv
from dataclasses import dataclass
import math
import random
import time
import wordfreq
import pandas as pd

from tatoeba_to_anki.download_audio import SENTENCES_WITH_AUDIO_PATH, AudioDownloader

TSV_FILE_PATH = "Satzpaare Tschechisch-Deutsch - 2022-05-30.tsv"
SOURCE_LANGUAGE = "cs"
AUDIO_DIR = "audio_files"

# Some code inspired from https://github.com/kmicklas/sentence-pairs/blob/master/sort.py
def get_sentence_word_frequency(sentence:str) -> float:

    words = wordfreq.tokenize(sentence, SOURCE_LANGUAGE)
    #
    freqs = [wordfreq.zipf_frequency(word, SOURCE_LANGUAGE)
                     for word in words]
    avgfreq = sum(freqs) / float(len(freqs))
    sentence_length = len(words)
    # Calculate log value of sentence_length
    sentence_length_log = 0.0
    if sentence_length > 0:
        sentence_length_log = math.log(sentence_length)
    return avgfreq - sentence_length_log

def czech_strings_are_very_similar(string1:str, string2:str) -> bool:
    
    # Return True if only the punctuation (.,:;!) is different
    if string1.replace(".", "").replace(",", "").replace(":", "").replace(";", "").replace("!", "") == \
            string2.replace(".", "").replace(",", "").replace(":", "").replace(";", "").replace("!", ""):
        return True
    # Return False if number of words is different
    if len(string1.split()) != len(string2.split()):
        return False

    #TODO: Return True if all words are the same or only differ in the last characters if the last characters are "l" or "ly"
   
    return False


def generate_ordered_sentences_tsv():
    with open(TSV_FILE_PATH, 'r', encoding="utf-8") as f:
        # Read tsv to pandas
        df = pd.read_csv(TSV_FILE_PATH, sep='\t', encoding='utf-8')
        # Set pandas dataframe columns to "sentence_id", "sentence_source", "target_sentence_id", "target_sentence"
        df.columns = ["sentence_id", "sentence_source", "target_sentence_id", "target_sentence"]
        # Remove columns with duplicate sentence_id (keep first occurence)
        df.drop_duplicates(subset=['sentence_id'], keep='first', inplace=True)
        # Add a column with the sentence word frequency
        df["sentence_word_frequency"] = df["sentence_source"].apply(get_sentence_word_frequency)

        # Sort the dataframe by sentence word frequency
        df = df.sort_values(by=["sentence_word_frequency"], ascending=False)

        # Turn pandas dataframe continuous again
        df = df.reset_index(drop=True)

        # TODO: Find all sentence_source sentences that are very similar:        
        #for i in range(len(df)):
        #    for j in range(i+1, len(df)):
        #        if strings_are_extremely_similar(df["sentence_source"][i], df["sentence_source"][j]):
        #            print(df["sentence_source"][i])
        #            print(df["sentence_source"][j])
        #            print("\n")
        df.to_csv("sorted_sentences.tsv", sep='\t', encoding='utf-8', index=False)


if __name__ == "__main__":

    #generate_ordered_sentences_tsv()
    # Load the sorted_sentences.tsv file with the sorted list of sentences into pandas
    with open("sorted_sentences.tsv", 'r', encoding="utf-8") as f:
        tsv_data = csv.reader(f, delimiter='\t')
        # Read tsv to pandas
        sorted_sentences = pd.read_csv(f, sep='\t', encoding='utf-8')

    audio_downloader = AudioDownloader(SOURCE_LANGUAGE, SENTENCES_WITH_AUDIO_PATH, audio_dir=AUDIO_DIR)
    # Iterate through the dataframe and download the audio files
    for i in range(len(sorted_sentences)):
        audio_downloader.download_audio(sorted_sentences["sentence_id"][i], sorted_sentences["sentence_source"][i], random.randint(1, 2))
