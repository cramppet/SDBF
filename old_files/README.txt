!!!!!!!!!!!!!!! To use the third tool of the package you need to download :

* DISCO at http://www.linguatools.de/disco/disco-1.2.jar
  and the following disctionnaries (follow the instructions given on the website for 
  dictionnary installation)
	- http://www.linguatools.de/disco/disco-languagedatapackets_en.html#enwiki
	- http://www.linguatools.de/disco/disco-languagedatapackets_en.html#frwiki
	- http://www.linguatools.de/disco/disco-languagedatapackets_en.html#degen
  create a new folder called "Disco" at the same level of the scripts and copy
  the jar file and the 3 folder corresponding to each dictionnary



**Third, use semanticexp.py script to discover subdomains of a given domain based on a 
  list of existing subdomains (of a common domain) contained in a txt file (1 domain per line)
  this list can be generated from sdbf.py for instance as with the last example.
  three different tools available :
	- semantic exploration (-d)
	- incremental discovery (-p)
	- splitter (-s)

Options:

  -h, --help            show this help message and exit
  -d, --disco           use DISCO semantic tool
  -s, --splitter        use word splitter tool (combined with DISCO)
  -p, --increment       use incremental discovery tool
  -i FILE, --input=FILE
                        domains previously discovered
  -o FILE, --output=FILE
                        output file with accessible names or feature
  -n COUNT, --horizontal=COUNT
                        horizontal depth : number of domains tested per domain
                        in the initial dataset
  -v VERTICAL, --vertical=VERTICAL
                        vertical depth : number of iteration over the new
                        domain lists (only for -d)
  -e, --english         use the english dictionnary (only for -d)
  -g, --german          use the german dictionnary (only for -d)
  -f, --french          use the french dictionnary (only for -d)

ex :

./semanticexp.py -d -egf -i scan_google.com -o semanticexp_google.com -n 100 -v 3
# use DISCO semantic tool with the 3 dictionnaries to discover new subdomains
  100 domains are tested for each subdomains in the initial dataset
  and a maximum of 3 iterations are made (we apply at most 3 times the technique
  on newly discovered domain) results are stored in semanticexp_google.com

./semanticexp.py -sp -i scan_google.com -o semanticexp_google.com -n 50 
# use splitter and incremental discovery tool to discover new subdomains
  50 domains are tested for each subdomains in the initial dataset
