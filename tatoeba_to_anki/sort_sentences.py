import math
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
