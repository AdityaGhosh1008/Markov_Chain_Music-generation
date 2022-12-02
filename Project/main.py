import mido as md
from collections import Counter, defaultdict, namedtuple
import random

from matplotlib.backends.backend_pdf import PdfPages
import numpy as np
import matplotlib.pyplot as plt


class Chain_Factory:

    def __init__(self, markov_chain):
        self.markov_chain = markov_chain

    def to_create_new_midi_track(self):
        track = md.MidiTrack()
        thisdic=dict()
        last_processed_note = None
        j=0
        for i in range(40):
            new_processing_note = self.markov_chain.get_next(
                last_processed_note)
            thisdic.update({j*0.003:new_processing_note.note})
            j=j+new_processing_note.duration
            message = [
                md.Message('note_on', note=new_processing_note.note, velocity=127,
                           time=0),
                md.Message('note_off', note=new_processing_note.note, velocity=0,
                           time=new_processing_note.duration)
            ]
            last_processed_note = new_processing_note
            track.extend(message)
        x = list(thisdic.keys())           
        y= list(thisdic.values())        
        plt.plot(x, y)
        plt.ylabel("Note no.")
        plt.xlabel("Time(seconds)")
        plt.savefig('graph.png')
        return track

    def create_new_mid_output_file(self, name_of_output_mid_file):

        midi = md.midifiles.MidiFile()
        track = self.to_create_new_midi_track()

        midi.tracks.append(track)
        midi.save(name_of_output_mid_file)


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
    def transition_matrix(self):
        def _col(string): return '{:<8}'.format(string)
        def _note(note): return '{}:{}'.format(note.note,note.duration)
        columns = []
        for from_note, to_notes in self.chain.items():
            for note in to_notes:
                if note not in columns:
                    columns.append(note)
        with open('transitionmatrix.txt', 'w') as f:
            f.write("        ")
            f.write(''.join([_col(_note(note)) for note in columns[:]]))
            f.write('\n')
            for from_note, to_notes in self.chain.items():
                f.write(_col(from_note))
                for note in columns[:]:
                    k=to_notes[note]
                    k=k/self.sums[from_note]
                    k=round(k,3)
                    if((k*1000)%100==0):
                        f.write(str(k)+"     ")
                    elif((k*1000)%10==0):
                        f.write(str(k)+"    ")
                    else:
                        f.write(str(k)+"   ")
                f.write('\n')
    def matrix(self):
        def _col(string): return '{:<8}'.format(string)
        def _note(note): return '{}:{}'.format(note.note,note.duration)
        columns = []
        for from_note, to_notes in self.chain.items():
            for note in to_notes:
                if note not in columns:
                    columns.append(note)
        with open('countmatrix.txt', 'w') as f:
            f.write("        ")
            f.write(''.join([_col(_note(note)) for note in columns[:]]))
            f.write('\n')
            for from_note, to_notes in self.chain.items():
                f.write(_col(from_note))
                for note in columns[:]:
                    f.write(_col(to_notes[note]))
                f.write('\n')


class Parser:

    def __init__(self, name_of_mid_file):
        self.name_of_mid_file = name_of_mid_file
        self.tempo = None
        self.ticks = None
        self.markov_chain = MarkovChain()
        self.parsing_done_here()

    def parsing_done_here(self):
        midi = md.MidiFile(self.name_of_mid_file)
        self.ticks = midi.ticks_per_beat
        notes_already_processed = []
        notes_currently_being_processed = []
        with open('data.txt', 'w') as f:
            for track in midi.tracks:
                for note in track:
                    f.write(str(note))
                    f.write('\n')
                    if note.type == "set_tempo":
                        self.tempo = note.tempo
                    elif note.type == "note_on":
                        if note.time == 0:
                            notes_currently_being_processed.append(note.note)
                        else:
                            self.add_new_node_to_markov_chain(notes_already_processed,
                                                              notes_currently_being_processed,
                                                              note.time)
                            notes_already_processed = notes_currently_being_processed
                            notes_currently_being_processed = []

    def add_new_node_to_markov_chain(self, notes_already_processed, notes_currently_being_processed, time):
        for n1 in notes_already_processed:
            for n2 in notes_currently_being_processed:
                self.markov_chain.add(
                    n1, n2, self.convert_ticks_to_ms(time))

    def convert_ticks_to_ms(self, ticks):
        ms = ((ticks / self.ticks) * self.tempo) / 1000
        return int(ms)

    def get_chain(self):
        return self.markov_chain


if __name__ == "__main__":
    main_markov_chain = Parser("midi/river_flows.mid").get_chain()
    # arg_no = 3
    # while arg_no < max_args + 1:
    #     new_chain = Parser(sys.argv[arg_no]).get_chain()
    #     chain.merge(new_chain)
    #     arg_no = arg_no + 1
    #     print('Generated markov chain')
    factory = Chain_Factory(main_markov_chain)
    factory.create_new_mid_output_file("midi/out.mid")
    main_markov_chain.matrix()
    main_markov_chain.transition_matrix()
    #out_markov_chain = Parser("midi/out.mid").get_chain()
    #out_markov_chain.matrix()
    #out_markov_chain.transition_matrix()
