# SDBF (Smart DNS Brute-Forcer) 

## Package Overview

This package propose 3 tools to generate and discover domain names or subdomains
of a domain names.

**Release:** sdbf-1.0
**Date:** 15-07-2012
**Authors**:
- Cynthia Wagner, University of Luxembourg
- Samuel Marchal, University of Luxembourg
- Jérôme François, University of Luxembourg
- Radu State, University of Luxembourg
- Thomas Engel, University of Luxembourg
- Peter Crampton, Just a guy

## Package Usage

0. Install dependencies with `pip3 install -r requirements.txt`

1. Use `markov.pl` script to generate 2 files based on a list of domain names
   contained (1 domain per line). The generated files are:
    - a "distribution" file which contains character frequencies, length
      distribution of domains, length distribution of names for differents
      domain levels, etc.
    - a "transition" file which contains probability of transitioning from a
      n-gram to a subsequent character

Usage: `./markov.pl REAL_DOMAIN_LIST N-GRAM_SIZE OUTPUT_DISTRIBUTON_FILE OUTPUT_TRANSITION_FILE` 
Example: `./markov.pl domains.txt 3 distribution.txt transition.txt`

2. Next, use `sdbf.py` script to generate new domain names based on the
   "distribution" and the "transition" files previously generated (sample
   "distribution" and "transition" files are given in the package)

Examples: 

1. `./sdbf.py -d distribution.txt -t transition.txt -n 1000 -o results.txt`
  - Probe of 1000 generated domain names and store positive results in
    results.txt

2. `./sdbf.py -d distribution.txt -t transition.txt -n 1000 -p www. -w "0 1" -o results.txt`
  - Probe of 1000 generated domain names starting with "www." and of size 3
    (level 0 and 1 generated) (ex : www.amazon.com) and store positive results
    in results.txt

3. `./sdbf.py -d distribution.txt -t transition.txt -n 5000 -s google.com --cw 2 -w 2 -o results.txt`
  - Probe of 5000 generated domain names ending with "google.com" and of size 3
    (level 2 generated) (ex : mail.google.com) and store positive results in
    results.txt
