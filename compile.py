#
# Compile an SVG and some interactions information
# into embeddable HTML
#

import sys
import xml.etree.ElementTree as ET
import json
import re
import uuid

def available_ids (svg):
    return [(elt.get("id"),elt.tag) for elt in svg.findall(".//*[@id]")]

def show_available_ids (ids):
    if ids:
        print >>sys.stderr, "available IDs:"
        w = max([len(id) for (id,tag) in ids])
        for (id,tag) in ids:
            print >>sys.stderr, "  {}   {}".format((id+" "*w)[:w],tag)
    else:
        print >>sys.stderr, "no available IDs"


def parse_instructions (instrfile):
    print >>sys.stderr, "parsing interaction instructions"
    instrs = {}
    instructions = []
    with open(instrfile,"r") as f:
        current = ""
        for line in f:
            if "#" in line:
                line = line[:line.find("#")].strip()
            if line:
                if line.strip(): 
                    current += " "+(line.strip())
                elif current:
                    instructions.append(current)
                    current = ""
        if current:
            instructions.append(current)

    for instr in instructions:
        print >>sys.stderr, " ", instr.strip()

    for instr in instructions:
        parts = instr.split("->")

        if len(parts) < 2: 
            print >>sys.stderr,"Cannot parse instruction:"
            print >>sys.stderr,"  ",instr.strip()
            raise Exception("Parsing error")

        (name,event) = parseEvent(parts[0])
        for part in parts[1:]:
            (action,targets) = parseAction(part)

            if name not in instrs:
                instrs[name] = {}
            if event not in instrs[name]:
                instrs[name][event] = {}
            instrs[name][event][action] = targets
    ##print >>sys.stderr,instrs
    return instrs



def tokenize (s):
    # really, should not break up strings "..." or '...'
    return s.split()

def parseEvent (s):
    p = tokenize(s)
    if len(p) != 2:
        print >>sys.stderr,"Cannot parse event part of instruction:"
        print >>sys.stderr,"  ",s
        raise Exception("Parsing error")
    return (p[1],p[0])

def parseAction (s):
    p = tokenize(s)
    if len(p) < 1:
        print >>sys.stderr,"Cannot parse action part of instruction:"
        print >>sys.stderr,"  ",s
        raise Exception("Parsing error")
    return (p[0],p[1:])
    


def load_instructions (instrfile):
    try:
        with open(instrfile,"r") as f:
            instrs = json.load(f)
    except: 
        instrs = parse_instructions(instrfile)
    return instrs

xmlns_svg = "http://www.w3.org/2000/svg"

def main (svgfile, insfile,frame,noload):
    ns = {"svg":"http://www.w3.org/2000/svg"}
    print >>sys.stderr, "reading SVG [{}]".format(svgfile)
    tree = ET.parse(svgfile)
    svg = tree.getroot()
    if svg.tag != "svg" and svg.tag != "{{{}}}svg".format(xmlns_svg):
        raise Exception("root element not <svg>")
    ids = available_ids(svg)
    show_available_ids(ids)
    if insfile:
        print >>sys.stderr, "reading interaction instructions [{}]".format(insfile)
        instr = load_instructions(insfile)

        # generate uuid
        uid = uuid.uuid4().hex
        print >>sys.stderr, "uuid",uid
        prefix = "fantomas_{}".format(uid)
        prefix_all_ids(svg,prefix)

        ##ET.register_namespace('',xmlns_svg)
        ##print >>sys.stderr, ET.tostring(svg)
        ##return

        # should do some sort of validation here -- don't bother for now
        # should probably rename the ids to something JS-friendly
        print >>sys.stderr, "generating output HTML"
        ## init_shown_ids = instr["_init"] if "_init" in instr else []

        setup = "var e=function(i){return document.getElementById(i);};var s=function(i){i.style.display='block';};var h=function(i){i.style.display='none';};"

        bind_ids = "".join([ "var fantomas_{id} = e('{p}_{id}');".format(p=prefix,id=id) for (id,_) in ids])
        setup_click = "".join([ "fantomas_{id}.addEventListener('click',function() {{ {show}{hide} }});"
                                  .format(id=id,
                                          show=mk_show_ids(get_click_show(instr,id)),
                                          hide=mk_hide_ids(get_click_hide(instr,id)))
                                for (id,_) in ids if id in instr])
        setup_hover = "".join([ "fantomas_{id}.addEventListener('mouseenter',function() {{ {show} }}); fantomas_{id}.addEventListener('mouseleave',function() {{ {hide} }});"
                                  .format(id=id,
                                          show=mk_show_ids(get_hover_show(instr,id)),
                                          hide=mk_hide_ids(get_hover_show(instr,id)))
                                for (id,_) in ids if id in instr])
        if noload:
            script_base = """(function() {{ {setup}{bind_ids}{show_ids}{hide_ids}{setup_click}{setup_hover} }})();"""
        else:
            script_base = """window.addEventListener('load',function() {{ {setup}{bind_ids}{setup_click}{setup_hover} }});"""
        script = script_base.format(bind_ids = bind_ids,
                                    setup=setup,
                                    setup_click=setup_click,
                                    setup_hover=setup_hover)
        if frame:
            print "<html><body>"
        print "<div>"
        # suppress namespace for svg
        ET.register_namespace('',xmlns_svg)
        print ET.tostring(svg)
        print "<script>"
        print script
        print "</script>"
        print "</div>"
        if frame:
            print "</body></html>"


def prefix_all_ids (svg,prefix):

    for elt in svg.findall(".//*[@id]"):
        elt.set("id","{}_{}".format(prefix,elt.get("id")))



def get_click_show (instr,id):
    if "click" in instr[id] and "show" in instr[id]["click"]:
        return instr[id]["click"]["show"]
    else:
        return []

def get_click_hide (instr,id):
    if "click" in instr[id] and "hide" in instr[id]["click"]:
        return instr[id]["click"]["hide"]
    else:
        return []

def get_hover_show (instr,id):
    if "hover" in instr[id] and "show" in instr[id]["hover"]:
        return instr[id]["hover"]["show"]
    else:
        return []

def get_hover_hide (instr,id):
    if "hover" in instr[id] and "hide" in instr[id]["hover"]:
        return instr[id]["hover"]["hide"]
    else:
        return []


def mk_show_ids (ids):
    # return " ".join([ "fantomas_{id}.style.visibility='visible';".format(id=id) for id in ids])
    # return " ".join([ "fantomas_{id}.style.display='block';".format(id=id) for id in ids])
    return " ".join([ "s(fantomas_{id});".format(id=id) for id in ids])

def mk_hide_ids (ids):
    # return " ".join([ "fantomas_{id}.style.visibility='hidden';".format(id=id) for id in ids])
    # return " ".join([ "fantomas_{id}.style.display='none';".format(id=id) for id in ids])
    return " ".join([ "h(fantomas_{id});".format(id=id) for id in ids])

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print "Usage: compile <svg> [<instructions>] [-frame] [-noload]"
    else:
        main(sys.argv[1],
             sys.argv[2] if len(sys.argv)>2 else None,
             len(sys.argv)>3 and "-frame" in sys.argv[3:],
             len(sys.argv)>3 and "-noload" in sys.argv[3:])
else:
    print "(loaded)"
