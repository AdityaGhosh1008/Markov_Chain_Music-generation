
from markov_chain import MarkovChain

import mido
import sys
from parser import Parser


class Chain_Factory:

    def __init__(self, markov_chain):
        self.markov_chain = markov_chain

    def create_track(self):
        track = mido.MidiTrack()
        last_note = None

        for i in range(50):
            new_note = self.markov_chain.get_next(last_note)
            message = [
                mido.Message('note_on', note=new_note.note, velocity=127,
                             time=0),
                mido.Message('note_off', note=new_note.note, velocity=0,
                             time=new_note.duration)
            ]
            track.extend(message)

        return track

    def generate(self, filename):

        midi = mido.midifiles.MidiFile()
        track = self.create_track()

        midi.tracks.append(track)
        midi.save(filename)


if __name__ == "__main__":
    
    max_args = 1
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
