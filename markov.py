'''markov.py: Markov modeling of observed DNS names'''

#!/usr/bin/env python3

import json
import sys
import random
import tldextract

from bloom_filter import BloomFilter


# TODO: In the same way we track and use first_char, do the same for last_char
# BUG: Our "total_chars_per_level" counter is different for level 0
class MarkovChain:
    '''MarkovChain represents a simple Markov model for DNS names'''

    MAX_LEVELS = 4
    NGRAM_LEN = 2


    # https://tools.ietf.org/html/rfc4343#section-2
    #UPPER_CHAR = list(map(chr, range(ord("A"), ord("Z") + 1)))
    LOWER_CHAR = list(map(chr, range(ord("a"), ord("z") + 1)))
    FIGURES = list(map(str, range(10)))


    def __init__(self):
        #
        self.others = "Others"
        #
        self.spec_char = []
        #
        self.freq_dom_length = {}
        #
        self.freq_word_length = {}
        #
        self.freq_first = {}
        #
        self.freq_char = {}
        #
        self.transitions = {}
        #
        self.max_dom_length = [None]
        #
        self.min_dom_length = [None]
        #
        self.max_word_length = {}
        #
        self.min_word_length = {}
        #
        self.max_proba_transitions = {}
        # Total length of all observed DNS names
        self._total_length = 0
        # Total number of levels for all observed DNS names
        self._total_levels = 0
        # Histogram of characters over all observed DNS names
        self._char_count = {}
        # Histogram of occurances of number of levels in names; ex. 'a.b.com' = 3
        self._level_count = {}
        # Histogram of number of chars for observed levels
        self._total_chars_per_level = {0: 0, 1: 0, 2: 0, 3: 0}
        # Histogram of observed first characters for each level
        self._first_chars_per_level = {0: {}, 1: {}, 2: {}, 3: {}}
        # Histogram of lengths of levels for observed DNS names
        self._level_len_count = {0: {}, 1: {}, 2: {}, 3: {}}
        # Histogram of first character of n-grams for observed levels
        self._first_chars_per_ngram = {0: {}, 1: {}, 2: {}, 3: {}}
        # Histogram of n-grams for observed levels
        self._ngrams_per_level = {0: {}, 1: {}, 2: {}, 3: {}}


    def _inc_or_insert(self, dictionary, key, default=1, inc=1):
        if not key in dictionary:
            dictionary[key] = default
        else:
            dictionary[key] += inc


    def _get_ngrams(self, base):
        for i in range(0, len(base)-self.NGRAM_LEN+1):
            t = base[i:i+self.NGRAM_LEN]
            if len(t) == self.NGRAM_LEN:
                yield t


    def _get_all_chars(self):
        '''
        get_all_chars build the character set for the generation model
        '''
        all_chars = []
        #all_chars.extend(self.UPPER_CHAR)
        all_chars.extend(self.LOWER_CHAR)
        all_chars.extend(self.FIGURES)
        all_chars.extend(self.spec_char)
        return all_chars


    # The model can be extended beyond what it directly observed; this is
    # achieved using a small bias factor called epsilon. epsilon alters the
    # random generation process of `_generate_val` such that the sum of
    # probabilites is not equal to 1. This means that for some small number of
    # cases we will have to sample from additional possibilities; these
    # additional possibilities are identified as "others".
    def _extend_model(self):
        # Update transitions to include the entire defined character set.
        for lev, v in self.transitions.items():
            for c_from, c_to in v.items():
                all_chars = self._get_all_chars()
                for char in c_to.keys():
                    all_chars.remove(char)
                v[c_from][self.others] = all_chars

        # Include all possible first chars based on character set.
        for lev, v in self.freq_first.items():
            all_chars = self._get_all_chars()
            for c2 in v.keys():
                all_chars.remove(c2)
            self.freq_first[lev][self.others] = all_chars

        # Include all possible word lengths (based on range observed)
        for lev, v in self.freq_word_length.items():
            lev_min, lev_max = self.min_word_length[lev], self.max_word_length[lev]
            all_lengths = list(range(lev_min, lev_max + 1))
            for k2 in v.keys():
                all_lengths.remove(k2)
            self.freq_word_length[lev][self.others] = all_lengths


    # TODO: If eps is always set to 0, then Others never comes into play
    def _generate_val(self, dict_freq, epsilon=0):
        '''
        generate_val uses the frequencies given in `dict_freq` to perform a
        weighted random element generation. `eps` is an epsilon value used to
        bias the generation, in most cases, it is set to 0. epsilon can be used
        to extend the Markov model outside of cases directly observed. see the
        `_extend_model` function.
        '''
        rnd = random.random()
        gen_total = 0.0

        # We remove the Others from the counting
        if self.others in dict_freq.keys():
            nvalues = len(dict_freq.keys()) - 1
        else:
            nvalues = len(dict_freq.keys())

        for k, v in dict_freq.items():
            if k != self.others:
                gen_total = gen_total + v - (epsilon/nvalues)
                if rnd < gen_total:
                    return k

        # if we are here, no selection has been made, random selection over
        # others. BUG: This assertion sometimes fails, why?
        #
        # the asset fails when there are no other entities to move to, ie when
        # we trained with insufficent data (eg. 1 sample)
        assert len(dict_freq[self.others]) != 0
        return dict_freq[self.others][random.randint(0, len(dict_freq[self.others]) - 1)]


    #def generate_name(pref, suff, custom_length, levels_opt, eps_mat, eps_length, eps_start):
    def generate_name(self, prefix="", suffix=""):
        # Generation is done from right to left
        name = prefix
        trans_temp = {self.others: self._get_all_chars()}

        # Determine the number of words to generate:
        nlevels = self._generate_val(self.freq_dom_length, 0.0) - len(prefix)

        # Iterate over the levels
        for i in range(nlevels):
            # Get the length of the word for this level
            length = self._generate_val(self.freq_word_length[i])

            # Generate the first letter
            last_char = self._generate_val(self.freq_first[i])
            gen = "" + last_char

            # Generate following letters
            for _ in range(length - 1):
                if last_char in self.transitions[i]:
                    last_char = self._generate_val(self.transitions[i][last_char])
                else:
                    # this character was never in a digram (it has been selectionned due to epsilon
                    last_char = self._generate_val(trans_temp, 0.0)
                gen = gen + last_char

            if name != "":
                name = gen + "." + name
            else:
                name = gen

        return name + suffix


    def train(self, dns_names):
        for name in dns_names:
            levels = list(filter(lambda x: len(x) > 0, name.split('.')))
            n = len(levels)
            k = min(n, self.MAX_LEVELS)

            self._total_length += len(name)
            self._total_levels += n
            self._inc_or_insert(self._level_count, k-1)

            for i in range(k):
                self._inc_or_insert(self._first_chars_per_level[i], levels[k-(i+1)][0])
                self._inc_or_insert(self._level_len_count[i], len(levels[k-(i+1)]))
                self._inc_or_insert(self._total_chars_per_level, i)

                for ngram in self._get_ngrams(levels[k-(i+1)]):
                    self._inc_or_insert(self._ngrams_per_level[i], ngram)
                    self._inc_or_insert(self._first_chars_per_ngram[i], ngram[0])

            for letter in name:
                self._inc_or_insert(self._char_count, letter)

        for char in sorted(self._char_count.keys()):
            freq = self._char_count[char] / self._total_length
            self.freq_char[char] = freq
            #if not char in (self.LOWER_CHAR + self.UPPER_CHAR + self.FIGURES):
            if not char in (self.LOWER_CHAR + self.FIGURES):
                self.spec_char.append(char)

        # BUG: We need to fix the "level + 1" in sdbf.py
        for level in sorted(self._level_count.keys()):
            freq = self._level_count[level] / len(dns_names)
            self.freq_dom_length[level+1] = freq

            if not level+1 in self.freq_dom_length:
                self.freq_dom_length[level+1] = {}

            if self.max_dom_length[0] is None or freq > self.max_dom_length[0]:
                self.max_dom_length[0] = freq

            if self.min_dom_length[0] is None or freq < self.min_dom_length[0]:
                self.min_dom_length[0] = freq

        for level in sorted(self._level_len_count.keys()):
            if not level in self.freq_word_length:
                self.freq_word_length[level] = {}

            self.max_word_length[level] = 0
            self.min_word_length[level] = 100

            for length in sorted(self._level_len_count[level].keys()):
                freq = self._level_len_count[level][length] / self._total_chars_per_level[level]
                self.freq_word_length[level][length] = freq

                if length > self.max_word_length[level]:
                    self.max_word_length[level] = length

                if length < self.min_word_length[level]:
                    self.min_word_length[level] = length

        for level in sorted(self._first_chars_per_level.keys()):
            if not level in self.freq_first:
                self.freq_first[level] = {}

            for char in sorted(self._first_chars_per_level[level].keys()):
                freq = self._first_chars_per_level[level][char] / self._total_chars_per_level[level]
                self.freq_first[level][char] = freq

        # Setup ngram transition matrix of Markov Chain
        for level in sorted(self._ngrams_per_level.keys()):
            if level not in self.transitions:
                self.transitions[level] = {}

            # BUG: Turns out this program only works for bigrams. It does not
            # work currently for general ngrams.
            for ngram in sorted(self._ngrams_per_level[level].keys()):
                c_from, c_to = ngram[0], ngram[1]
                count = self._ngrams_per_level[level][ngram]

                if c_from not in self.transitions[level]:
                    self.transitions[level][c_from] = {}

                for char in sorted(self._first_chars_per_ngram[level].keys()):
                    if c_from == char:
                        prob = count / self._first_chars_per_ngram[level][char]
                        self.transitions[level][char][c_to] = prob

        self._extend_model()


def main():
    if len(sys.argv) < 2:
        print('usage: ./markov.py <input_file>')
        sys.exit(1)

    observed = BloomFilter(1000000, 0.0001)
    suffix_map = {}
    suffix_freq = {}
    suffix_models = {}

    def preprocess(dns_name):
        return dns_name.strip().lower()

    def generate_val(dict_freq):
        rnd = random.random()
        gen_total = 0.0
        for k, v in dict_freq.items():
            gen_total = gen_total + v
            if rnd < gen_total:
                return k
        assert False

    with open(sys.argv[1]) as input_file:
        dns_names = list(map(preprocess, input_file.readlines()))
        num_names = len(dns_names)

        for name in dns_names:
            parts = name.split('.')[1:]
            if len(parts) == 1:
                num_names -= 1
                continue
            suffix = '.'.join(parts)
            t = tldextract.extract(suffix)
            if t.domain == '':
                num_names -= 1
                continue
            if suffix not in suffix_map:
                suffix_map[suffix] = []
                suffix_freq[suffix] = 1
            else:
                suffix_freq[suffix] += 1
                suffix_map[suffix].append(name)
            observed.add(name)

        for suffix in suffix_freq:
            suffix_freq[suffix] /= num_names

    count = 0
    while count != 1000000:
        suffix = generate_val(suffix_freq)
        if suffix not in suffix_models:
            if len(suffix_map[suffix]) > 1:
                suffix_models[suffix] = MarkovChain()
                names = map(lambda x: x.replace('.' + suffix, ''), suffix_map[suffix])
                suffix_models[suffix].train(list(names))
            else:
                continue
        name = suffix_models[suffix].generate_name() + '.' + suffix
        if name not in observed:
            observed.add(name)
            count += 1
            print(name)


if __name__ == '__main__':
    main()
