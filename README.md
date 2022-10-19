# Tatoeba to Anki sentence pair flash card creator

<img src="https://raw.githubusercontent.com/Vuizur/tatoeba-to-anki/main/img/anki_screenshot.png" width="50%" class="center">

This project creates Anki flashcards from a Tatoeba language pair, ordering the cards by difficulty, downloading audio from Tatoeba (and E-Text-To-Speech if the native audio is not available) and reducing the card number to a set maximum.

The ordering algorithm takes the average frequency of each sentence and sentence length into account.

It also removes duplicates. 

Additionally it supports the generation of automatic help to lookup single words directly on the back of the card. By default, it downloads a dictionary for this automatically (limited to English definitions currently). You can also pass a custom tabfile dictionary (use [pyglossary](https://github.com/ilius/pyglossary) to convert other dictionaries).

It should work for all languages pairs.

### Running it

You should install it with `pip install git+https://github.com/Vuizur/tatoeba-to-anki` or `poetry add git+https://github.com/Vuizur/tatoeba-to-anki`.

I plan on adding more features, you can open an issue if you think something should be changed/improved or send a pull request.

### Interesting other projects:
* This [project for generating Swedish cards](https://github.com/vvpd/anki_swedish) is pretty sophisticated and is probably worth understanding more fully

* [Sentence pairs](https://github.com/kmicklas/sentence-pairs) is a pretty simple package which has given me the idea of using the wordfreq package

* Older solutions such as [Tatoeba-Ankigeneration](https://github.com/alexanderk409/Tatoeba-anki-deckgeneration) scrape parts of the site by themselves, but that should not be necessary anymore with the new downloadable data