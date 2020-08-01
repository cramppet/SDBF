#!/usr/bin/env python3

import json
import sys


MAX_LEVELS = 4


# BUG: Our "total_chars_per_level" counter is different for level 0
def main():
    # Total length of all observed DNS names
    total_length = 0
    # Total number of levels for all observed DNS names
    total_levels = 0
    # Histogram of characters over all observed DNS names
    char_count = {}
    # Histogram of occurances of number of levels in names; ex. 'a.b.com' = 3
    level_count = {}
    # Histogram of number of chars for observed levels
    total_chars_per_level = {0: 0, 1: 0, 2: 0, 3: 0}
    # Histogram of observed first characters for each level
    first_chars_per_level = {0: {}, 1: {}, 2: {}, 3: {}}
    # Histogram of lengths of levels for observed DNS names
    level_len_count = {0: {}, 1: {}, 2: {}, 3: {}}
    # Histogram of first character of n-grams for observed levels
    first_chars_per_ngram = {0: {}, 1: {}, 2: {}, 3: {}}
    # Histogram of n-grams for observed levels
    ngrams_per_level = {0: {}, 1: {}, 2: {}, 3: {}}

    if len(sys.argv) < 3:
        print('usage: ./markov.py <input_file> <n-gram length> <output file>')
        sys.exit(1)

    ngram_len = int(sys.argv[2])
    output_file_name = sys.argv[3]
    output_root = {
        'trans': {0: {}, 1: {}, 2: {}, 3: {}},
        'dist': {
            'freq_char': {},
            'freq_word_length': {0: {}, 1: {}, 2: {}, 3: {}},
            'freq_first': {0: {}, 1: {}, 2: {}, 3: {}},
            # TODO: We track levels starting from 0, the original reported them
            # as starting from 1, be aware!
            'freq_dom_length': {0: 0, 1: 0, 2: '0', 3: 0, 4: 0},
        },
    }

    def preprocess(dns_name):
        return dns_name.strip().lower()

    def inc_or_insert(dictionary, key, default=1, inc=1):
        if not key in dictionary:
            dictionary[key] = default
        else:
            dictionary[key] += inc

    def get_ngrams(base):
        for i in range(0, len(base)-ngram_len+1):
            t = base[i:i+ngram_len]
            if len(t) == ngram_len:
                yield t

    with open(sys.argv[1]) as input_file:
        dns_names = list(map(preprocess, input_file.readlines()))

        for name in dns_names:
            levels = list(filter(lambda x: len(x) > 0, name.split('.')))
            n = len(levels)
            k = min(n, MAX_LEVELS)

            total_length += len(name)
            total_levels += n
            inc_or_insert(level_count, k-1)

            for i in range(k):
                inc_or_insert(first_chars_per_level[i], levels[k-(i+1)][0])
                inc_or_insert(level_len_count[i], len(levels[k-(i+1)]))
                inc_or_insert(total_chars_per_level, i)

                for ngram in get_ngrams(levels[k-(i+1)]):
                    inc_or_insert(ngrams_per_level[i], ngram)
                    inc_or_insert(first_chars_per_ngram[i], ngram[0])

            for letter in name:
                inc_or_insert(char_count, letter)

        for char in sorted(char_count.keys()):
            freq = char_count[char] / total_length
            output_root['dist']['freq_char'][char] = freq

        for level in sorted(level_count.keys()):
            # BUG: We need to fix the "level+1" in sdbf.py
            freq = level_count[level] / len(dns_names)
            output_root['dist']['freq_dom_length'][level + 1] = freq

        for level in sorted(level_len_count.keys()):
            for length in sorted(level_len_count[level].keys()):
                # TODO: Is this wrong???
                freq = level_len_count[level][length] / total_chars_per_level[level]
                output_root['dist']['freq_word_length'][level][length] = freq

        for level in sorted(first_chars_per_level.keys()):
            for char in sorted(first_chars_per_level[level].keys()):
                freq = first_chars_per_level[level][char] / total_chars_per_level[level]
                output_root['dist']['freq_first'][level][char] = freq

        # Serialize ngram transition matrix of Markov Chain
        for level in sorted(ngrams_per_level.keys()):
            for ngram in sorted(ngrams_per_level[level].keys()):
                first = ngram[0]
                count = ngrams_per_level[level][ngram]
                for char in sorted(first_chars_per_ngram[level].keys()):
                    if first == char:
                        prob = count / first_chars_per_ngram[level][char]
                        output_root['trans'][level][ngram] = prob

    with open(output_file_name, 'w') as output_file:
        output_file.write(json.dumps(output_root))


if __name__ == '__main__':
    main()
