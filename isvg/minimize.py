#
# Script to minimize a <script>...</script> in javascript
#
# Although to be honest, it really just minimizes whatever you give it, collapsing sequence of whitespace to a single space
#

import sys
import re

def minimize (file):

    with open(file,"r") as f:

        for line in f:

            print re.sub("\s+"," ",line).strip(),



if __name__ == "__main__":
    if len(sys.argv) < 2:
        print "Usage: minimize <file>"
    else:
        minimize(sys.argv[1])
        
