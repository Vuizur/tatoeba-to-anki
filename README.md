# Tatoeba to Anki sentence pair flash card creator

This project creates Anki flashcards from a Tatoeba language pair, ordering the cards by difficulty and downloading audio from Google-Text-To-Speech to integrate directly into the deck.

The ordering algorithm takes the average frequency of each sentence and sentence length into account.

It also removes direct duplicates. 

It has been tested for Czech-German, but probably also works for other languages with minimal changes (because the word frequency package I use supports many languages)

### Running it

First you need to get the data: Go to https://tatoeba.org/en/downloads, download the desired sentence pairs.

Then should clone the project, install poetry and then run `poetry install`. 
Move the sentence pair files into the root folder.

Then run `poetry run python ./tatoeba_to_anki/main.py` to sort the files, remove duplicates, and download the audio.
After that run `poetry run python ./tatoeba_to_anki/generate_anki_deck.py` to generate the Anki deck.

I plan on adding more features, you can open an issue if you think something should be changed/improved.

### Interesting other projects:
* This [project for generating Swedish cards](https://github.com/vvpd/anki_swedish) is pretty sophisticated and is probably worth understanding more fully

* [Sentence pairs](https://github.com/kmicklas/sentence-pairs) is a pretty simple package which has given me the idea of using the wordfreq package