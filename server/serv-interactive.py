
from bottle import get, post, run, request, static_file, abort, redirect, template

# use a better web server
from bottle import PasteServer

import os
import sys
import uuid

import xml.etree.ElementTree as ET

import StringIO

def available_ids (svg):
    return [(elt.get("id"),elt) for elt in svg.findall(".//*[@id]")]

xmlns_svg = "http://www.w3.org/2000/svg"

def parse_instructions (instrfile):
    print >>sys.stderr, "parsing interaction instructions"
    instrs = {}
    instructions = []
    current = ""
    for line in instrfile.split("\n"):
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
        if name not in instrs:
            instrs[name] = {}
        # clobber old event for that name if one exists
        instrs[name][event] = [ parse_action(part) for part in parts[1:]]
        # for part in parts[1:]:
        #     (action,targets) = parse_action(part)

        #     if name not in instrs:
        #         instrs[name] = {}
        #     if event not in instrs[name]:
        #         instrs[name][event] = {}
        #     instrs[name][event][action] = targets
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

#def parse_action (s):
#    p = tokenize(s)
#    if len(p) < 1:
#        print >>sys.stderr,"Cannot parse action part of instruction:"
#        print >>sys.stderr,"  ",s
#        raise Exception("Parsing error")
#    return (p[0],p[1:])
 
def parse_action (s):
    p = tokenize(s)
    if len(p) > 0 and p[0] in ["show","hide"]:
        return {"action":p[0],
                "elements":p[1:]}
    elif len(p) > 1 and p[0] in ["enable","disable"]:
        return {"action":p[0],
                "value":p[1],
                "elements":p[2:]}
    else:
        print >>sys.stderr,"Cannot parse action part of instruction:"
        print >>sys.stderr,"  ",s
        raise Exception("Parsing error")


def load_instructions (instrfile):
    try:
        with open(instrfile,"r") as f:
            instrs = json.load(f)
    except: 
        instrs = parse_instructions(instrfile)
    return instrs

xmlns_svg = "http://www.w3.org/2000/svg"

def process (svgtext, x,y,width,height,instext,frame,noload):
    ns = {"svg":"http://www.w3.org/2000/svg"}
    svg = ET.fromstring(svgtext)
    # svg = tree.getroot()
    if svg.tag != "svg" and svg.tag != "{{{}}}svg".format(xmlns_svg):
        raise Exception("root element not <svg>")
    ids = available_ids(svg)

    instr = parse_instructions(instext)
    
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

    output = ""

    setup = "var e=function(i){return document.getElementById(i);};var s=function(i){i.style.display=\"block\";};var h=function(i){i.style.display=\"none\";};"

    bind_ids = "".join([ "var fantomas_{cid} = e(\"{p}_{id}\");".format(p=prefix,cid=clean_id(id),id=id) for (id,_) in ids])

    # clean IDs because they will end up in identifiers
    ids = [ (clean_id(id),elt) for (id,elt) in ids]

    setup_click = ""
    setup_hover = ""

    for id in [id for (id,_) in ids if id in instr]:
        for event in instr[id]:
            if event == "click":
                actions = "".join([ compile_action(act) for act in instr[id]["click"] ])
                setup_click += "fantomas_{id}.addEventListener(\"click\",function() {{ {actions} }});".format(id=id,actions=actions)
                setup_click += "fantomas_{id}.style.cursor=\"pointer\";".format(id=id);
            elif event == "hover":
                do_actions = "".join([ save_action(i,act)+compile_action(act) for (i,act) in enumerate(instr[id]["hover"])] )
                undo_actions = "".join(reversed([ restore_action(i,act) for (i,act) in enumerate(instr[id]["hover"]) ]))
                setup_hover += "fantomas_{id}.addEventListener(\"mouseenter\",function() {{ {do_actions} }}); fantomas_{id}.addEventListener(\"mouseleave\",function() {{ {undo_actions} }});".format(id=id,do_actions=do_actions,undo_actions=undo_actions)

    if noload:
        script_base = """(function() {{ {setup}{bind_ids}{setup_click}{setup_hover} }})();"""
    else:
        script_base = """window.addEventListener(\"load\",function() {{ {setup}{bind_ids}{setup_click}{setup_hover} }});"""
    script = script_base.format(bind_ids = bind_ids,
                                setup=setup,
                                setup_click=setup_click,
                                setup_hover=setup_hover)
    if frame:
        output += "<html><body>"
    output +=  "<div>"
        # suppress namespace for svg
    ET.register_namespace('',xmlns_svg)
    svg.attrib["x"] = x
    svg.attrib["y"] = y
    svg.attrib["width"] = width
    svg.attrib["height"] = height
    output += ET.tostring(svg)
    output += "<script>"
    output += script
    output += "</script>"
    output += "</div>"
    if frame:
        output += "</body></html>"

    return output


def clean_id (id):
    # letting you use - in IDs without it causing problems
    # augment with others characters that may sensibly show up
    return id.replace("-","_")

            
def prefix_all_ids (svg,prefix):

    for elt in svg.findall(".//*[@id]"):
        elt.set("id","{}_{}".format(prefix,elt.get("id")))


def compile_action (act):
    if act["action"] == "show":
        return mk_show_ids(act["elements"])
    elif act["action"] == "hide":
        return mk_hide_ids(act["elements"])
    elif act["action"] == "disable":
        return mk_disable_ids(act["value"] if "value" in act else None,act["elements"])
    elif act["action"] == "enable":
        return mk_enable_ids(act["value"] if "value" in act else None,act["elements"])
    else:
        return ""


def save_action (i,act):
    if act["action"] in ["show","hide"]:
        return "".join([ "fantomas_{id}.saved_fantomas_display_{i}=fantomas_{id}.style.display;".format(id=id,i=i) for id in act["elements"] ])
    else:
        print >>sys.stderr,"saving for action {} not implemented".format(act["action"])
        return ""

def restore_action (i,act):
    if act["action"] in ["show","hide"]:
        return "".join([ "fantomas_{id}.style.display=fantomas_{id}.saved_fantomas_display_{i};".format(id=id,i=i) for id in act["elements"] ])
    else:
        print >>sys.stderr,"saving for action {} not implemented".format(act["action"])
        return ""


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
    # return " ".join([ "fantomas_{id}.style.visibility=\"visible\";".format(id=id) for id in ids])
    # return " ".join([ "fantomas_{id}.style.display=\"block\";".format(id=id) for id in ids])
    return "".join([ "s(fantomas_{id});".format(id=id) for id in ids])

def mk_hide_ids (ids):
    # return " ".join([ "fantomas_{id}.style.visibility=\"hidden\";".format(id=id) for id in ids])
    # return " ".join([ "fantomas_{id}.style.display=\"none\";".format(id=id) for id in ids])
    return "".join([ "h(fantomas_{id});".format(id=id) for id in ids])

def mk_disable_ids (val,ids):
    opacity = lambda id: "fantomas_{id}.style.opacity={val};".format(id=id,val=val) if val else ""
    return "".join([ "{opac}fantomas_{id}.style.pointerEvents=\"none\";".format(id=id,opac=opacity(id)) for id in ids])

def mk_enable_ids (val,ids):
    opacity = lambda id: "fantomas_{id}.style.opacity={val};".format(id=id,val=val) if val else ""
    return "".join([ "{opac}fantomas_{id}.style.pointerEvents=\"auto\";".format(id=id,opac=opacity(id)) for id in ids])







def announce (s):
    print "--------------------------------------------------"
    print s


@post("/upload_svg")
def POST_upload_svg ():

    upload     = request.files.get("file")
    
    announce("POST /UPLOAD_SVG");

#    result = "";
#    for r in upload.file:
#        result += r;

#    upload.file.seek(0)

    tree = ET.parse(upload.file)
    svg = tree.getroot()
    
    if svg.tag != "svg" and svg.tag != "{{{}}}svg".format(xmlns_svg):
        raise Exception("root element not <svg>")
    ids = available_ids(svg)

    result = ""
    if ids:
        w = max([len(id) for (id,tag) in ids])
        for (id,elt) in ids:
            result += """<li><input id="checkbox_{id}" type="checkbox" {checked}></input><label for="checkbox_{id}" style="margin-left: 10px;">{id}</label></li>\n
                      """.format(checked="" if elt.get("display")=="none" else "checked",
                                 id=id)

    ET.register_namespace('',xmlns_svg)

    original_x = svg.attrib["x"]
    original_y = svg.attrib["y"]
    original_width = svg.attrib["width"]
    original_height = svg.attrib["height"]

    svg.attrib["x"] = "0";
    svg.attrib["y"] = "0";
    svg.attrib["width"] = "500";
    svg.attrib["height"] = "300";

    return template("upload_svg",
                    page_title = "Interactive SVG",
                    code_svg = ET.tostring(svg),
                    code_ids = result,
                    original_x = original_x,
                    original_y = original_y,
                    original_width = original_width,
                    original_height = original_height,
                    ids = "[{}]".format(",".join([ "\"{}\"".format(id) for (id,_) in ids])))
                    

@post("/compile_svg")
def POST_compile_svg ():

    svg = request.forms.get("svg")
    instr = request.forms.get("instr")
    ox = request.forms.get("ox")
    oy = request.forms.get("oy")
    ow = request.forms.get("ow")
    oh = request.forms.get("oh")
    # print "svg = ",svg
    # print "instr = ",instr

    result = process (svg,ox,oy,ow,oh,instr,True,True)

    return result
    
    

ROOT = "static"

@get('/')
@get('/<path:path>')
def static (path="index.html"):
    return static_file(path, root=ROOT)


def main (p):
    print "Serving folder",ROOT
    run(server=PasteServer, host='0.0.0.0', port=p)


# can run non-interactively by calling with 
#  python -i serv-dataviz.py
# it will give an error (port is not given)
# but will remain alive

if __name__ == "__main__":
    if len(sys.argv) > 1:
        port = int(sys.argv[1])
        main(port)
    else:
        print "Usage: server <port>"
else:
    print "(loaded)"


