import mido
from collections import Counter, defaultdict, namedtuple
import random


class Chain_Factory:

    def __init__(self, markov_chain):
        self.markov_chain = markov_chain

    def create_track(self):
        track = mido.MidiTrack()
        last_note = None
        for i in range(40):
            new_note = self.markov_chain.get_next(last_note)
            message = [
                mido.Message('note_on', note=new_note.note, velocity=127,
                             time=0),
                mido.Message('note_off', note=new_note.note, velocity=0,
                             time=new_note.duration)
            ]
            last_note = new_note
            track.extend(message)
        return track

    def generate(self, filename):

        midi = mido.midifiles.MidiFile()
        track = self.create_track()

        midi.tracks.append(track)
        midi.save(filename)

Note = namedtuple('Note', ['note', 'duration'])

class MarkovChain:
    def __init__(self):
        self.chain = defaultdict(Counter)
        self.sums = defaultdict(int)

    def add(self, from_note, to_note, duration):
        new_note = Note(to_note, duration)
        self.chain[from_note][new_note] += 1
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

    def get_chain(self):
        return {k: dict(v) for k, v in self.chain.items()}

    def matrix(self):
        def _col(string): return '{:<4}'.format(string)
        def _note(note): return '{}'.format(note.note)
        columns = []
        for from_note, to_notes in self.chain.items():
            for note in to_notes:
                if note not in columns:
                    columns.append(note)
        with open('countmatrix.txt', 'w') as f:
            f.write("    ")
            f.write(''.join([_col(_note(note)) for note in columns[:]]))
            f.write('\n')
            for from_note, to_notes in self.chain.items():
                f.write(_col(from_note))
                for note in columns[:]:
                    f.write(_col(to_notes[note]))
                f.write('\n')

class Parser:

    def __init__(self, filename):
        self.filename = filename
        self.tempo = None
        self.ticks_per_beat = None
        self.markov_chain = MarkovChain()
        self._parse()

    def _parse(self):
        midi = mido.MidiFile(self.filename)
        self.ticks_per_beat = midi.ticks_per_beat
        previous_chunk = []
        current_chunk = []
        for track in midi.tracks:
            for message in track:
                if message.type == "set_tempo":
                    self.tempo = message.tempo
                elif message.type == "note_on":
                    if message.time == 0:
                        current_chunk.append(message.note)
                    else:
                        self._sequence(previous_chunk,
                                       current_chunk,
                                       message.time)
                        previous_chunk = current_chunk
                        current_chunk = []

    def _sequence(self, previous_chunk, current_chunk, duration):
        for n1 in previous_chunk:
            for n2 in current_chunk:
                self.markov_chain.add(
                    n1, n2, self._bucket_duration(duration))

    def _bucket_duration(self, ticks):
        ms = ((ticks / self.ticks_per_beat) * self.tempo) / 1000
        return int(ms)

    def get_chain(self):
        return self.markov_chain

if __name__ == "__main__":
    chain = Parser("midi/river_flows.mid").get_chain()
    # arg_no = 3
    # while arg_no < max_args + 1:
    #     new_chain = Parser(sys.argv[arg_no]).get_chain()
    #     chain.merge(new_chain)
    #     arg_no = arg_no + 1
    #     print('Generated markov chain')
    factory = Chain_Factory(chain)
    factory.generate("midi/out.mid")
    chain.matrix()
