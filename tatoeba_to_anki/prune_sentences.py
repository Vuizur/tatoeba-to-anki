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
