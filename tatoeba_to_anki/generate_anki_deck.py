import wordfreq

# from tabfiledictionary import SimpleTabfileDictionary
from tabfile_dictionary.dictionary import TabfileDictionary


def generate_wiktionary_link_html(
    sentence: str,
    wiktionary_base_url,
    wiktionary_source_language: str,
    ietf_language_code: str,
) -> str:
    # Tokenize the sentence using wordfreq
    tokens = wordfreq.tokenize(sentence, ietf_language_code)
    html = "<p>"
    for token in tokens:
        html += f"<a href='{wiktionary_base_url}{token}#{wiktionary_source_language}'>{token}</a> "
    html += "</p>"
    return html


def generate_dictionary_html(
    sentence: str,
    dictionary: TabfileDictionary,
    ietf_language_code: str,
) -> str:
    tokens = wordfreq.tokenize(sentence, ietf_language_code)
    html = "<p>"
    for token in tokens:
        results = dictionary.lookup(token)
        if len(results) > 0:
            html += "<details><summary>" + token + "</summary>"
            for result in results:
                html += f"<b>{result.word.strip()}</b>"
                html += f"<br>{result.definition.strip()}<br><br>"
            html += "</details>"
    html += "</p>"
    return html
