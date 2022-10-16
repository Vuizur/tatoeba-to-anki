from dataclasses import dataclass

@dataclass
class Entry:
    headword_and_inflections: dict[str, str]
    # This is for faster lookup
    headword_and_inflections_lower: dict[str, str]
    definition: str = ""    

class SimpleTabfileDictionary:

    def __init__(self, filename):
        self.filename = filename
        self.entry_list = []

        self.read_dictionary()

    def read_dictionary(self):
        # Read the dictionary tsv
        with open(self.filename, 'r', encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if "\t" in line:
                    line = line.split('\t')
                    definition = line[1]
                    headword_and_inflections = dict.fromkeys(line[0].split('|'))
                    headword_and_inflections_lower = dict.fromkeys([word.lower() for word in line[0].split('|')])
                    entry = Entry(headword_and_inflections,headword_and_inflections_lower, definition)
                    
                    self.entry_list.append(entry)
    def get_entries(self, word: str) -> list[Entry]:
        return [entry for entry in self.entry_list if word.lower() in entry.headword_and_inflections_lower]
        

if __name__ == "__main__":
    dictionary = SimpleTabfileDictionary("Tschechisch-Deutsch.txt")
    print(dictionary.get_entries("moc"))