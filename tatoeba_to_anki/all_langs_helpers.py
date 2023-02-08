from wordfreq import available_languages

from tatoeba_to_anki.download_audio import get_all_languages

#TODO: Pay attention to special case with fil and tl

def get_all_langs_that_have_voice_and_word_frequency() -> list[str]:
    """Get all languages that have a voice and word frequency."""
    languages_with_frequency: set[str] = set(available_languages().keys())
    languages_with_voice: set[str] = set(get_all_languages())

    return list(languages_with_frequency.intersection(languages_with_voice))


if __name__ == "__main__":
    print(get_all_langs_that_have_voice_and_word_frequency())