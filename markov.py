#!/usr/bin/env python3

import sys


MAX_LEVELS = 4


def main():
    print("n-gram analysis and stats")

    # Total length of all observed DNS names
    total_length = 0
    # Total number of tokens for observed DNS names
    total_tokens = 0
    # Histogram of characters for observed DNS names
    all_chars = {}
    # Histogram of number of levels for observed DNS names
    levels_per_name = {}
    # Histogram of number of tokens for observed levels
    total_tokens_per_level = { 0: 0, 1: 0, 2: 0, 3: 0 }
    # Histogram of observed first characters for each level
    first_chars_per_level = { 0: {}, 1: {}, 2: {}, 3: {} }
    # Histogram of lengths of levels for observed DNS names
    length_of_levels = { 0: {}, 1: {}, 2: {}, 3: {} }
    # Histogram of first character of n-grams for observed levels
    first_chars_per_ngram = { 0: {}, 1: {}, 2: {}, 3: {} }
    # Histogram of n-grams for observed levels
    ngrams_per_level = { 0: {}, 1: {}, 2: {}, 3: {} }

    if len(sys.argv) < 3:
        print('usage: ./markov.py <input_file> <n-gram length> <dist file> <trans file>')
        sys.exit(1)

    ngram_len = int(sys.argv[2])
    dist_file_name = sys.argv[3]
    trans_file_name = sys.argv[4]

    def preprocess(dns_name):
        return dns_name.strip().lower()

    def inc_or_insert(d, key, default=1, inc=1):
        if not key in d:
            d[key] = default
        else:
            d[key] += inc

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
            total_tokens += n
            inc_or_insert(levels_per_name, k-1) 

            for i in range(k):
                inc_or_insert(first_chars_per_level[i], levels[k-(i+1)][0])
                inc_or_insert(length_of_levels[i], len(levels[k-(i+1)]))
                inc_or_insert(total_tokens_per_level, i)

                for ngram in get_ngrams(levels[k-(i+1)]):
                    inc_or_insert(ngrams_per_level[i], ngram)
                    inc_or_insert(first_chars_per_ngram[i], ngram[0])

            for letter in name:
                inc_or_insert(all_chars, letter)
        
        # TODO: Change output format to single file in JSON format

        with open(dist_file_name, 'w') as dist_file:
            dist_file.write(f"# Amount of domain names: {len(dns_names)}\n")
            dist_file.write(f"# Average domain length considering all characters: {total_length/len(dns_names)}\n")

            dist_file.write("# Character frequences\n")
            for char in sorted(all_chars.keys()):
                dist_file.write(f"{char}: {all_chars[char]/total_length}\n")

            # TODO: We track levels starting from 0, the original reported them
            # as starting from 1, be aware!

            dist_file.write("# Words of domain names :\n")
            for level in sorted(levels_per_name.keys()):
                dist_file.write(f"{level+1}: {levels_per_name[level]/len(dns_names)}\n")

            # BUG: Our "total_tokens_per_level" counter is different for level 0

            dist_file.write("\n# distribution of word-length per domain word\n")
            for level in sorted(length_of_levels.keys()):
                dist_file.write(f"level {level}: ")
                for length in sorted(length_of_levels[level].keys()):
                    dist_file.write(f"{length}: {length_of_levels[level][length]/total_tokens_per_level[level]},")
                dist_file.write('\n')

            dist_file.write("\n# Most occurring first characters:\n")
            for level in sorted(first_chars_per_level.keys()):
                dist_file.write(f"level {level}: ")
                for char in sorted(first_chars_per_level[level].keys()):
                    dist_file.write(f"{char}: {first_chars_per_level[level][char]/total_tokens_per_level[level]},")
                dist_file.write('\n')

        with open(trans_file_name, 'w') as trans_file:
            for level in sorted(ngrams_per_level.keys()):
                if level != 0:
                    trans_file.write(f"level {level}:\n")
                for ngram in sorted(ngrams_per_level[level].keys()):
                    first = ngram[0]
                    count = ngrams_per_level[level][ngram]
                    for char in sorted(first_chars_per_ngram[level].keys()):
                        if first == char:
                            freq = count / first_chars_per_ngram[level][char]
                            trans_file.write(f"{level} {ngram}: {freq}\n")


if __name__ == '__main__':
    main()
