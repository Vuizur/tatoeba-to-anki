from dataclasses import dataclass
import pandas as pd

# work in progress

class Reference:
    def __init__(self, word: str):
        self.word = word

class TabfileDictionary:
    def __init__(self, filename):
        # Create new pandas dataframe
        self.df = pd.DataFrame(columns=["headword", "headword_lower", "definitions", "references"])

        #self.read_dictionary()

    def read_dictionary(self):
        # Read the dictionary tsv
        with open(self.filename, 'r', encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if "\t" in line:
                    line = line.split('\t')
                    definition = line[1]
                    headword_and_inflections = line[0].split('|')
                    headword = headword_and_inflections[0]
                    inflections = headword_and_inflections[1:]

                    # Merge the data into the dataframe so that only one line exists for each headword
                    if len(self.df) == 0:
                        self.df = self.df.append({"headword": headword, "headword_lower": headword.lower(), "definitions": definition, "references": []}, ignore_index=True)
                    else:
                        # Check if the headword already is in the table
                        if self.df["headword"].str.contains(headword).any():
                            # If it does, add the definition to the existing row
                            index = self.df["headword"].str.contains(headword).idxmax()
                            self.df.at[index, "definitions"] += "\n" + definition
                        else:
                            # If it doesn't, add a new row
                            self.df = self.df.append({"headword": headword, "headword_lower": headword.lower(), "definitions": definition, "references": []}, ignore_index=True)
                    

                    # Add the headword to the dictionary
                    #if headword not in self.dictionary:
                    #    self.dictionary[headword] = []
#
                    #self.dictionary[headword].append(definition)
#
                    #for inflection in inflections:
                    #    base_word_reference = Reference(headword)
                    #    # Add the base word reference to the dictionary structure
                    #    if inflection not in self.dictionary:
                    #        self.dictionary[inflection] = []
                    #    # Add the inflection to the dictionary structure
                    #    self.dictionary[inflection].append(base_word_reference)


@dataclass
class Entry:
    headword_and_inflections: dict
    # This is for faster lookup
    headword_and_inflections_lower: dict
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
    print(dictionary.get_entries("fdfd"))