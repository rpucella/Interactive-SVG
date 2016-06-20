#
# Compile an SVG and some interactions information
# into embeddable HTML
#

import sys
import xml.etree.ElementTree as ET
import json
# import re

import uuid

VERBOSE_FLAG = False

def set_verbose_flag (flag):
    global VERBOSE_FLAG
    VERBOSE_FLAG = flag

def verbose (msg):
    if VERBOSE_FLAG:
        print >>sys.stderr, msg

xmlns_svg = "http://www.w3.org/2000/svg"

def compile (svg, instructions,size=None,frame=False,noload=False):
    ns = {"svg":"http://www.w3.org/2000/svg"}
    if svg.tag != "svg" and svg.tag != "{{{}}}svg".format(xmlns_svg):
        raise Exception("root element not <svg>")
    ids = available_ids(svg)

    # instr = parse_instructions(instructions)
    
    # generate uuid
    uid = uuid.uuid4().hex
    verbose("UUID {}".format(uid))

    prefix = "fantomas_{}".format(uid)
    prefix_all_ids(svg,prefix)
    
    # should do some sort of validation here -- don't bother for now
    # should probably rename the ids to something JS-friendly
    verbose("Generating output HTML")
    ## init_shown_ids = instructions["_init"] if "_init" in instructions else []

    output = ""

    setup = "var e=function(i){return document.getElementById(i);};var s=function(i){i.style.display=\"block\";};var h=function(i){i.style.display=\"none\";};"

    bind_ids = "".join([ "var fantomas_{cid} = e(\"{p}_{id}\");".format(p=prefix,cid=clean_id(id),id=id) for (id,_) in ids])

    # clean IDs because they will end up in identifiers
    ids = [ (clean_id(id),elt) for (id,elt) in ids]

    setup_click = ""
    setup_hover = ""

    for id in [id for (id,_) in ids if id in instructions]:
        for event in instructions[id]:
            if event == "click":
                actions = "".join([ compile_action(act) for act in instructions[id]["click"] ])
                setup_click += "fantomas_{id}.addEventListener(\"click\",function() {{ {actions} }});".format(id=id,actions=actions)
                setup_click += "fantomas_{id}.style.cursor=\"pointer\";".format(id=id);
            elif event == "hover":
                do_actions = "".join([ save_action(i,act)+compile_action(act) for (i,act) in enumerate(instructions[id]["hover"])] )
                undo_actions = "".join(reversed([ restore_action(i,act) for (i,act) in enumerate(instructions[id]["hover"]) ]))
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

    if size:
        svg.attrib["x"] = size["x"]
        svg.attrib["y"] = size["y"]
        svg.attrib["width"] = size["width"]
        svg.attrib["height"] = size["height"]

    output += ET.tostring(svg)
    output += "<script>"
    output += script
    output += "</script>"
    output += "</div>"
    if frame:
        output += "</body></html>"

    return output






def available_ids (svg):
    return [(elt.get("id"),elt) for elt in svg.findall(".//*[@id]")]


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
        verbose("saving for action {} not implemented".format(act["action"]))
        return ""

def restore_action (i,act):
    if act["action"] in ["show","hide"]:
        return "".join([ "fantomas_{id}.style.display=fantomas_{id}.saved_fantomas_display_{i};".format(id=id,i=i) for id in act["elements"] ])
    else:
        verbose("saving for action {} not implemented".format(act["action"]))
        return ""


def get_click_show (instructions,id):
    if "click" in instructions[id] and "show" in instructions[id]["click"]:
        return instructions[id]["click"]["show"]
    else:
        return []

def get_click_hide (instructions,id):
    if "click" in instructions[id] and "hide" in instructions[id]["click"]:
        return instructions[id]["click"]["hide"]
    else:
        return []

def get_hover_show (instructions,id):
    if "hover" in instructions[id] and "show" in instructions[id]["hover"]:
        return instructions[id]["hover"]["show"]
    else:
        return []

def get_hover_hide (instructions,id):
    if "hover" in instructions[id] and "hide" in instructions[id]["hover"]:
        return instructions[id]["hover"]["hide"]
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





def parse_instructions (instrs_string):
    verbose("Parsing interaction instructions")
    instrs = {}
    instructions = []

    current = ""
    for line in instrs_string.split("\n"):
        #verbose("   "+line)
        #verbose("current = "+current)
        if "#" in line:
            line = line[:line.find("#")]
        if line.strip():
            current += " "+(line.strip())
        elif current:
            instructions.append(current)
            current = ""

    if current:
        instructions.append(current)

    ###verbose(len(instructions))

    for instr in instructions:
        verbose("  {}".format(instr.strip()))

    for instr in instructions:
        parts = instr.split("->")

        if len(parts) < 2: 
            raise Exception("Parsing error - cannot parse {}".format(instr.strip()))

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
    return instrs



def tokenize (s):
    # really, should not break up strings "..." or '...'
    return s.split()

def parseEvent (s):
    p = tokenize(s)
    if len(p) != 2:
        raise Exception("Parsing error - cannot parse event part of instruction {}".format(s))
    return (p[1],p[0])

 
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
        raise Exception("Parsing error - cannot parse action part of instruction {}".format(s))


def load_instructions (instrfile):
    try:
        with open(instrfile,"r") as f:
            instrs = json.load(f)
    except: 
        with open(instrfile,"r") as f:
            instrs = parse_instructions(f.read())
    return instrs