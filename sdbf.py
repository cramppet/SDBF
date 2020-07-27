#!/usr/bin/python3

################################################################################
#                                                                              #
#    Copyright (C) 2011-2012 Cynthia Wagner, Jerome Francois, Samuel Marchal   #
#                            Radu State, Thomas Engel                          #
#    Copyright (C) 2011-2012 SnT University of Luxembourg                      #
#                                                                              #
#    This file is part of SDBF GPL Edition, a Smart DNS Brute-Forcing Tool     #
#                                                                              #
#    SDBF GPL Edition is free software: you can redistribute it and/or modify  #
#    it under the terms of the GNU General Public License as published by      #
#    the Free Software Foundation, either version 3 of the License, or         #
#    (at your option) any later version.                                       #
#                                                                              #
#    SDBF GPL Edition is distributed in the hope that it will be useful,       #
#    but WITHOUT ANY WARRANTY; without even the implied warranty of            #
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the             #
#    GNU General Public License for more details.                              #
#                                                                              #
#    You should have received a copy of the GNU General Public License         #
#    along with SDBF GPL Edition.  If not, see <http://www.gnu.org/licenses/>. #
#                                                                              #
################################################################################

import sys
import random
import json

from optparse import OptionParser

import numpy
from bloom_filter import BloomFilter


VALUE = "value"
OTHERS = "Others"

# Model variables
LOWER_CHAR = list(map(chr, range(ord("a"), ord("z") + 1)))
UPPER_CHAR = list(map(chr, range(ord("A"), ord("Z") + 1)))
FIGURES = list(map(str, range(10)))
SPEC_CHAR = []
FREQ_DOM_LENGTH = {}
FREQ_WORD_LENGTH = {}
FREQ_FIRST = {}
TRANSITIONS = {}
MAX_DOM_LENGTH = [None]
MIN_DOM_LENGTH = [None]
MAX_WORD_LENGTH = {}
MIN_WORD_LENGTH = {}
MAX_PROBA_TRANSITIONS = {}


def get_all_chars():
    '''
    get_all_chars build the character set for the generation model
    '''
    all_chars = []
    all_chars.extend(UPPER_CHAR)
    all_chars.extend(LOWER_CHAR)
    all_chars.extend(SPEC_CHAR)
    all_chars.extend(FIGURES)
    return all_chars


def generate_val(dict_freq, eps):
    '''
    generate_val uses the frequencies given in `dict_freq` to perform a weighted
    random element generation. `eps` is an epsilon value used to bias the
    generation, in most cases, it is set to 0.
    '''
    rnd = random.random()
    gen_total = 0.0

    # We remove the Others from the counting
    if OTHERS in dict_freq.keys():
        nvalues = len(dict_freq.keys()) - 1
    else:
        nvalues = len(dict_freq.keys())

    for k, v in dict_freq.items():
        if k != OTHERS:
            gen_total = gen_total + v - (eps / (1.0 * nvalues))
            if rnd < gen_total:
                return k

    # if we are here, no selection has been made, random selection over others
    return dict_freq[OTHERS][random.randint(0, len(dict_freq[OTHERS]) - 1)]


def get_proba(dict_freq, eps, val):

    # We remove the Others from the counting
    if OTHERS in dict_freq.keys():
        nvalues = len(dict_freq.keys()) - 1
    else:
        nvalues = len(dict_freq.keys())

    if val in dict_freq.keys():
        return dict_freq[val] - (eps / (1.0 * nvalues))
    else:
        return eps / len(get_all_chars())


# TODO: They didn't use the character distribution in the original for anything
# other than trying to identify characters not within their pre-existing charset.
#def read_info(input_file_name, mxw, miw):
def read_info(input_file_name):
    with open(input_file_name, 'r') as input_file:
        root_obj = json.loads(input_file.read())['dist']

    for char in root_obj['freq_char'].keys():
        if not char in (LOWER_CHAR + UPPER_CHAR + FIGURES):
            SPEC_CHAR.append(char)

    for level in root_obj['freq_dom_length'].keys():
        if not int(level) in FREQ_DOM_LENGTH:
            FREQ_DOM_LENGTH[int(level)] = {}

        v = root_obj['freq_dom_length'][level]
        FREQ_DOM_LENGTH[int(level)] = float(v)

        if MAX_DOM_LENGTH[0] == None or float(v) > MAX_DOM_LENGTH[0]:
            MAX_DOM_LENGTH[0] = float(v)

        if MIN_DOM_LENGTH[0] == None or float(v) < MIN_DOM_LENGTH[0]:
            MIN_DOM_LENGTH[0] = float(v)

    for level in root_obj['freq_word_length'].keys():
        if not str(level) in FREQ_WORD_LENGTH:
            FREQ_WORD_LENGTH[int(level)] = {}

        MAX_WORD_LENGTH[int(level)] = mxw[int(level)]
        MIN_WORD_LENGTH[int(level)] = miw[int(level)]

        for key in root_obj['freq_word_length'][level].keys():
            v = root_obj['freq_word_length'][level][key]
            FREQ_WORD_LENGTH[int(level)][int(key)] = v

            if int(key) > MAX_WORD_LENGTH[int(level)]:
                MAX_WORD_LENGTH[int(level)] = int(key)

            if int(key) < MIN_WORD_LENGTH[int(level)]:
                MIN_WORD_LENGTH[int(level)] = int(key)

    for level in root_obj['freq_first'].keys():
        if not int(level) in FREQ_FIRST:
            FREQ_FIRST[int(level)] = {}

        for key in root_obj['freq_first'][level].keys():
            v = root_obj['freq_first'][level][key]
            FREQ_FIRST[int(level)][key] = v


def read_trans(input_file_name):
    global TRANSITIONS
    global MAX_PROBA_TRANSITIONS

    with open(input_file_name, 'r') as input_file:
        root_obj = json.loads(input_file.read())['trans']
        levels = list(map(int, root_obj.keys()))

    for level in levels:
        if not level in TRANSITIONS:
            TRANSITIONS[level] = {}
        if not level in MAX_PROBA_TRANSITIONS:
            MAX_PROBA_TRANSITIONS[level] = []

        # BUG: Turns out this program only works for bigrams, not general ngrams
        for bigram in root_obj[str(level)]:
            c_from, c_to = bigram[0], bigram[1]
            prob = root_obj[str(level)][bigram]
            if not c_from in TRANSITIONS[level]:
                TRANSITIONS[level][c_from] = {}
            TRANSITIONS[level][c_from][c_to] = prob
            MAX_PROBA_TRANSITIONS[level].append(prob)

    # TODO: Figure out what the fuck this is supposed to be doing
    for level in MAX_PROBA_TRANSITIONS:
        MAX_PROBA_TRANSITIONS[level] = numpy.mean(MAX_PROBA_TRANSITIONS[level])


#def update_freq(custom_length, levels_opt):
def update_freq(custom_length):

    for lev, v in TRANSITIONS.items():
        for c1, v2 in v.items():

            all_chars = get_all_chars()
            for c2 in v2.keys():
                all_chars.remove(c2)
            v[c1][OTHERS] = all_chars

    for lev, v in FREQ_FIRST.items():
        all_chars = get_all_chars()
        for c2 in v.keys():
            all_chars.remove(c2)
        FREQ_FIRST[lev][OTHERS] = all_chars

    for lev, v in FREQ_WORD_LENGTH.items():
        all_lengths = list(range(MIN_WORD_LENGTH[lev], MAX_WORD_LENGTH[lev] + 1))

        for k2 in v.keys():
            all_lengths.remove(k2)

        FREQ_WORD_LENGTH[lev][OTHERS] = all_lengths

    toRemove = []
    tot = 0.0

    for k, v in FREQ_DOM_LENGTH.items():
        if k <= custom_length or k > custom_length + len(levels_opt):
            toRemove.append(k)
        else:
            tot = tot + v

    for r in toRemove:
        del FREQ_DOM_LENGTH[r]

    for k, v in FREQ_DOM_LENGTH.items():
        FREQ_DOM_LENGTH[k] = v / tot


#def generate_name(pref, suff, custom_length, levels_opt, eps_mat, eps_length, eps_start):
def generate_name(pref, suff, custom_length):
    # Generation is done from right to left

    name = ""
    name += suff

    trans_temp = {OTHERS: get_all_chars()}

    # Determine the number of words to generate:

    nwords = generate_val(FREQ_DOM_LENGTH, 0.0) - custom_length

    # Iterate over the words
    for i in range(nwords):
        # Get the level
        # lev = levels_opt[i]

        # Get the length of the word for this level
        length = generate_val(
            FREQ_WORD_LENGTH[levels_opt[i]], eps_length[levels_opt[i]]
        )

        # Generate the first letter
        last_char = generate_val(FREQ_FIRST[levels_opt[i]], eps_start[levels_opt[i]])
        gen = "" + last_char

        # Generate following letters
        for _ in range(length - 1):
            if last_char in TRANSITIONS[levels_opt[i]]:
                last_char = generate_val(
                    TRANSITIONS[levels_opt[i]][last_char], eps_mat[levels_opt[i]]
                )
            else:
                # this character was never in a digram (it has been selectionned due to epsilon

                last_char = generate_val(trans_temp, 0.0)

            gen = gen + last_char

        if name != "":
            name = gen + "." + name
        else:
            name = gen

    name = pref + name
    return name


#def generate_feature(name, eps_mat, eps_length, eps_start):
def generate_feature():

    maxW = max(FREQ_DOM_LENGTH.keys())

    words = name.strip().split(".")
    words = words[max(0, len(words) - maxW) :]
    words.reverse()

    # compute the probability of the domain length
    # proba_length = get_proba(freq_dom_length,0.0,len(words))
    proba_length = len(words)

    # proba_word_lengths = [1.0] * maxW
    proba_word_lengths = [0.0] * maxW
    proba_words = [1.0] * maxW

    for lev in range(len(words)):

        w = words[lev]
        #n_transitions = len(w)

        # Get the proba for the current length
        # proba_word_lengths[lev] = get_proba(freq_word_length[lev],eps_length[lev],len(w))
        proba_word_lengths[lev] = len(w)

        # Get the proba of the words
        last_char = w[0]
        w = w[1:]

        proba = get_proba(FREQ_FIRST[lev], eps_start[lev], last_char)
        # Continuing over following letters
        while w != "":
            last_char2 = w[0]
            w = w[1:]
            proba = proba * get_proba(
                TRANSITIONS[lev][last_char], eps_mat[lev], last_char2
            )
            # proba = proba +  get_proba(transitions[lev][last_char],eps_start[lev],last_char2)
            last_char = last_char2

        proba_words[lev] = proba

    return (proba_length, proba_word_lengths, proba_words)


#def generate_score(name, eps_mat, eps_length, eps_start):
def generate_score():

    maxW = max(FREQ_DOM_LENGTH.keys())

    words = name.strip().split(".")
    words = words[max(0, len(words) - maxW) :]
    words.reverse()

    # compute the probability of the domain length
    proba_length = get_proba(FREQ_DOM_LENGTH, 0.0, len(words))

    proba_word_lengths = [1.0] * maxW
    proba_words = [1.0] * maxW

    for lev in range(len(words)):

        w = words[lev]

        # Get the proba for the current length
        proba_word_lengths[lev] = get_proba(
            FREQ_WORD_LENGTH[lev], eps_length[lev], len(w)
        )

        # Get the proba of the words
        # n_transitions = len(w)
        last_char = w[0]
        w = w[1:6]

        proba = get_proba(FREQ_FIRST[lev], eps_start[lev], last_char)
        # Continuing over following letters
        while w != "":
            last_char2 = w[0]
            w = w[1:]
            proba = proba * get_proba(
                TRANSITIONS[lev][last_char], eps_mat[lev], last_char2
            )
            # proba = proba +  get_proba(transitions[lev][last_char],eps_start[lev],last_char2)
            last_char = last_char2

        proba_words[lev] = proba
        # proba_words[lev] = proba / n_transitions
        # proba_words[lev] = proba / (max_proba_transitions[lev]**(len(words[lev])-1))
        # proba_words[lev] = proba * (len(words[lev])-1)

    # return (proba_length, proba_word_lengths,proba_words)

    mult = 1.0
    for k in list(map(lambda x, y: x * y, proba_word_lengths, proba_words)):
        # for k in proba_words:
        mult = mult * k

    # return mult
    return proba_length * mult


if __name__ == "__main__":
    lineparser = OptionParser("")
    lineparser.add_option(
        "-i",
        "--input",
        dest="input",
        default="input.json",
        type="string",
        help="serialized Markov Chain and stats file",
        metavar="FILE",
    )
    lineparser.add_option(
        "-e",
        "--epsilons",
        dest="eps",
        default="0.001 0.001 0.001 0.001",
        type="string",
        help="epsilon values for empty values in transition matrix",
    )
    lineparser.add_option(
        "-b",
        "--epsilons-start",
        dest="eps_start",
        default="0.001 0.001 0.001 0.001",
        type="string",
        help="epsilon values for empty values in starting character distribution",
    )
    lineparser.add_option(
        "-l",
        "--epsilons-length",
        dest="eps_length",
        default="0.001 0.001 0.001 0.001",
        type="string",
        help="epsilon values for empty values in length distribution",
    )
    lineparser.add_option(
        "-n",
        "--number-to-generate",
        dest="number_generate",
        default=100,
        type="int",
        help="number of names to generate",
    )
    lineparser.add_option(
        "-s", "--suffix", dest="suffix", default="", type="string", help="suffix value"
    )
    lineparser.add_option(
        "-p", "--prefix", dest="prefix", default="", type="string", help="prefix value"
    )
    lineparser.add_option(
        "-w",
        "--word-level",
        dest="levels",
        default="0 1 2 3",
        type="string",
        help="word levels to generate",
    )
    lineparser.add_option(
        "--cw",
        "--custom-words",
        dest="cwords",
        default=0,
        type="int",
        help="length (in words) of the custom words (prefix and suffix)",
    )
    lineparser.add_option(
        "--mxw",
        "--max-length-words",
        dest="mxw",
        default="3 7 12 20",
        type="string",
        help="maximal word lengths (may be adjusted regarding the training)",
    )
    lineparser.add_option(
        "--miw",
        "--min-length-words",
        dest="miw",
        default="1 1 1 1",
        type="string",
        help="minimal word lengths (may be adjusted regarding the training)",
    )
    lineparser.add_option(
        "-o",
        "--output",
        dest="output",
        default="output.txt",
        type="string",
        help="output file with accessible names or feature",
        metavar="FILE",
    )

    options, args = lineparser.parse_args()
    tot = 0
    myBloom = BloomFilter(options.number_generate, 0.0001)

    eps_mat = list(map(float, options.eps.split(" ")))
    eps_start = list(map(float, options.eps_start.split(" ")))
    eps_length = list(map(float, options.eps_length.split(" ")))
    levels_opt = list(map(int, options.levels.split(" ")))
    mxw = list(map(int, options.mxw.split(" ")))
    miw = list(map(int, options.miw.split(" ")))

    read_info(options.input)
    read_trans(options.input)
    update_freq(options.cwords)

    for k in range(options.number_generate * 5):
        name = generate_name(options.prefix, options.suffix, options.cwords)
        if not name in myBloom:
            myBloom.add(name)
            tot += 1
            if tot > options.number_generate:
                break
            sys.stdout.write(name + '\n')
