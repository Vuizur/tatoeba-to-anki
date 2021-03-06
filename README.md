# Tatoeba to Anki sentence pair flash card creator

<img src="https://raw.githubusercontent.com/Vuizur/tatoeba-to-anki/main/img/anki_screenshot.png" width="50%" class="center">

This project creates Anki flashcards from a Tatoeba language pair, ordering the cards by difficulty and downloading audio from Tatoeba (and Google-Text-To-Speech if the native audio is not available) to integrate directly into the deck.

The ordering algorithm takes the average frequency of each sentence and sentence length into account.

It also removes duplicates. 

Additionally it supports the generation of automatic help to lookup single words. You can pass a tabfile dictionary (use [pyglossary](https://github.com/ilius/pyglossary) to convert other dictionaries), which will add the translation of each word directly to each card. Or you can choose to add links to Wiktionary instead.

It has been tested for Czech-German, but also works for other languages (because the word frequency package I use supports many languages)

### Running it

First you need to get the data: Go to https://tatoeba.org/en/downloads and download the desired sentence pairs. Then on the same page, download the sentences_with_audio.tar.bz2 as well.

Then should clone the project, install poetry and then run `poetry install`. 
Move the sentence pair files and sentences_with_audio.tar.bz2 into the root folder and edit the settings in `config.toml` to set the names of the relevant input/output files, the language and some other settings.

Then run `poetry run python ./tatoeba_to_anki/main.py` for the program to generate the Anki deck.

I plan on adding more features, you can open an issue if you think something should be changed/improved or send a pull request.

#### Language-specific requirements

In Chinese, the external library jieba is required. Install it with `poetry add jieba`.

Also, to quote the wordfreq package:
    
In Japanese and Korean, instead of using the regex library, it uses the external library mecab-python3. This is an optional dependency of wordfreq, and compiling it requires the libmecab-dev system package to be installed.
### Interesting other projects:
* This [project for generating Swedish cards](https://github.com/vvpd/anki_swedish) is pretty sophisticated and is probably worth understanding more fully

* [Sentence pairs](https://github.com/kmicklas/sentence-pairs) is a pretty simple package which has given me the idea of using the wordfreq package

* Older solutions such as [Tatoeba-Ankigeneration](https://github.com/alexanderk409/Tatoeba-anki-deckgeneration) scrape parts of the site by themselves, but that should not be necessary anymore with the new downloadable data