
from collections import Counter, defaultdict, namedtuple

import random

Note = namedtuple('Note', ['note', 'duration'])


class MarkovChain:

    def __init__(self):
        self.chain = defaultdict(Counter)
        self.sums = defaultdict(int)

    @staticmethod
    def create_from_dict(dict):
        m = MarkovChain()
        for from_note, to_notes in dict.items():
            for k, v in to_notes.items():
                m.add(from_note, k, v)
        return m

    def serialize(self, note, duration):
        return Note(note, duration)

    def add(self, from_note, to_note, duration):
        self.chain[from_note][self.serialize(to_note, duration)] += 1
        self.sums[from_note] += 1

    def get_next(self, seed_note):
        if seed_note is None or seed_note not in self.chain:
            random_chain = self.chain[random.choice(list(self.chain.keys()))]
            return random.choice(list(random_chain.keys()))
        next_note_counter = random.randint(0, self.sums[seed_note])
        for note, frequency in self.chain[seed_note].items():
            next_note_counter -= frequency
            if next_note_counter <= 0:
                return note

    def merge(self, other):
        assert isinstance(other, MarkovChain)
        self.sums = defaultdict(int)
        for from_note, to_notes in other.chain.items():
            self.chain[from_note].update(to_notes)
        for from_note, to_notes in self.chain.items():
            self.sums[from_note] = sum(self.chain[from_note].values())

    def get_chain(self):
        return {k: dict(v) for k, v in self.chain.items()}

    def matrix(self, limit=28):
        def _col(string): return '{:<4}'.format(string)
        def _note(note): return '{}'.format(note.note)
        columns = []
        for from_note, to_notes in self.chain.items():
            for note in to_notes:
                if note not in columns:
                    columns.append(note)
        out = _col('')
        with open('countmatrix.txt', 'w') as f:
            f.write("    ")
            f.write(''.join([_col(_note(note)) for note in columns[:limit]]))
            f.write('\n')
            for from_note, to_notes in self.chain.items():
                f.write(_col(from_note))
                for note in columns[:limit]:
                    f.write(_col(to_notes[note]))
                f.write('\n')
