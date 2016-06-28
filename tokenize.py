
# A simple tokenizer

import re

class TokenizationError (Exception):
    def __init__ (self,inp):
        self.inp = inp
    def __str__ (self):
        return "Cannot tokenize %s" % self.inp

DEBUG_FLAG = False #True

def debug (str):
    if DEBUG_FLAG:
        print str


############################################################
#
# LEXER
#
############################################################

TOKENS = [ (re.compile(r"->"),("THEN",lambda x:"->")),
           (re.compile(r"\."),("PERIOD",lambda x:".")),
           (re.compile(r'".*?"'),("STRING",lambda x:x[1:-1])),
           (re.compile(r"'.*?'"),("STRING",lambda x:x[1:-1])),
           (re.compile(r"-?\.[0-9]+"),("NUMBER",lambda x:x)),  # float(x))),
           (re.compile(r"-?[0-9]+\.[0-9]+"),("NUMBER",lambda x:x)), # float(x))),
           (re.compile(r"-?[0-9]+[0-9]*"),("NUMBER",lambda x:x)),   #int(x))),
           (re.compile(r"[A-Za-z_$][A-Za-z0-9-_$@]*"),("ID",lambda x:x))]

def tokenize (string):
    # compiled = [ (re.compile(regexp,re.IGNORECASE),tok) for (regexp,tok) in TOKENS]
    ws = re.compile(r"([ \n\t\r]+)|(#.*)")   # skip whitespace & comments
    stream = []
    current = string
    while current:
        match_ws = ws.match(current)
        while match_ws:
            current = current[match_ws.end():]
            match_ws = ws.match(current)
        if current:
            match_found = False
            for (r,(tok,f)) in TOKENS:
                match = r.match(current)
                if match:
                    val = f(current[match.start():match.end()])
                    # if tok=="ID":
                    #    (tok,val) = convertIdentifier(val)
                    stream.append((tok,val))
                    current = current[match.end():]
                    match_found = True
                    break
            if not match_found:
                raise TokenizationError(current)
    return stream

def convertIdentifier (s):
    dispatch = { "true": "TRUE",
                 "false": "FALSE",
                 "if": "IF",
                 "then": "THEN",
                 "else": "ELSE",
                 "let": "LET",
                 "in": "IN" }
    return (dispatch[s],None) if (s in dispatch.keys()) else ("ID",s)

