#
# Compile an SVG and some interactions information
# into embeddable HTML
#

import sys
import xml.etree.ElementTree as ET
import json

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

def load_instructions (instrfile):
    with open(instrfile,"r") as f:
        instrs = json.load(f)
    ##print >>sys.stderr, instrs
    return instrs

xmlns_svg = "http://www.w3.org/2000/svg"

def main (svgfile, insfile,frame):
    ns = {"svg":"http://www.w3.org/2000/svg"}
    print >>sys.stderr, "reading SVG [{}]".format(svgfile)
    tree = ET.parse(svgfile)
    svg = tree.getroot()
    if svg.tag != "svg" and svg.tag != "{{{}}}svg".format(xmlns_svg):
        raise Exception("root element not <svg>")
    ids = available_ids(svg)
    show_available_ids(ids)
    if insfile:
        print >>sys.stderr, "reading interactions instructions [{}]".format(insfile)
        instr = load_instructions(insfile)
        # should do some sort of validation here -- don't bother for now
        # should probably rename the ids to something JS-friendly
        print >>sys.stderr, "generating output HTML"
        init_shown_ids = instr["_init"] if "_init" in instr else []
        bind_ids = "".join([ "var element_{id} = document.getElementById('{id}');".format(id=id) for (id,_) in ids])
        show_ids = mk_show_ids(init_shown_ids)
        hide_ids = mk_hide_ids([ id for (id,_) in ids if id not in init_shown_ids])
        setup_click = "".join([ "element_{id}.addEventListener('click',function() {{ {show}{hide} }});".format(id=id,
                                                                                                                    show=mk_show_ids(get_click_show(instr,id)),
                                                                                                                    hide=mk_hide_ids(get_click_hide(instr,id)))
                                     for (id,_) in ids if id in instr])
        setup_hover = "".join([ "element_{id}.addEventListener('mouseenter',function() {{ {show} }}); element_{id}.addEventListener('mouseleave',function() {{ {hide} }});".format(id=id,
                                                                                                                                                                                  show=mk_show_ids(get_hover(instr,id)),
                                                                                                                                                                                  hide=mk_hide_ids(get_hover(instr,id)))
                                for (id,_) in ids if id in instr])
        script = """window.addEventListener('load',function() {{ {bind_ids}{show_ids}{hide_ids}{setup_click}{setup_hover} }});""".format(bind_ids = bind_ids,
                                                                                                                               show_ids = show_ids,
                                                                                                                               hide_ids = hide_ids,
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

def get_hover (instr,id):
    if "hover" in instr[id]:
        return instr[id]["hover"]
    else:
        return []


def mk_show_ids (ids):
    # return " ".join([ "element_{id}.style.visibility='visible';".format(id=id) for id in ids])
    return " ".join([ "element_{id}.style.display='block';".format(id=id) for id in ids])

def mk_hide_ids (ids):
    # return " ".join([ "element_{id}.style.visibility='hidden';".format(id=id) for id in ids])
    return " ".join([ "element_{id}.style.display='none';".format(id=id) for id in ids])

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print "Usage: compile <svg> [<instructions>] [-frame]"
    else:
        main(sys.argv[1],
             sys.argv[2] if len(sys.argv)>2 else None,
             len(sys.argv)>3 and sys.argv[3]=="-frame")
