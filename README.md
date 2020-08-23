# Smart DNS Brute Forcer (SDBF)

This project was originally based on the 2012 paper found here:

https://ieeexplore.ieee.org/document/6212021

This fork is a complete re-write of their entire codebase with several changes
to the underlying Markov model.

## How it works

The tool accepts an input list of observed DNS names and creates a simple Markov
model to understand the observations. This model is endowed with generative
capabilites through the use of a **Markov Chain**, which performs random walks
within the joint probability distribution of the trained Markov model.

The tool will generate new DNS names which have the same statistical properties
as those provided in the input list. These names can then be used in conjunction
with a DNS brute forcing tool like **MassDNS** to perform DNS resolution of the
generated names.

One other point about this tool is the inclusion of several bias factors all
called **epsilon** values. These bias factors are used to extend the Markov
model outside of direct observations. The bias factors can be controlled by
modifying the script. There are no command line options for manipulating them as
they are typically inconsequential.

The suggested usage of this tool is to passively observe as many DNS names as
possible from a target domain and only then supply that entire listing to this
tool for analysis and further generation.

## How to use it

First install the dependencies:

```
pip3 install -r requirements.txt
```

Next, once you have a list for a given domain, you can run the tool like so:

```
python3 markov.py -n 100 observed_names.txt > generated_names.txt
```

This will generate 100 new names based on the previously observed ones which you
can then use with **MassDNS** like so:

```
./bin/massdns -r lists/resolvers.txt -t A -o S -w results.txt generated_names.txt
```
