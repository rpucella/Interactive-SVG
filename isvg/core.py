#
# Compile an SVG and some interactions information
# into embeddable HTML
#

import sys
import xml.etree.ElementTree as ET
import json
# import re

import uuid

import tokenize as tok

VERBOSE_FLAG = False

def set_verbose_flag (flag):
    global VERBOSE_FLAG
    VERBOSE_FLAG = flag

def verbose (msg):
    if VERBOSE_FLAG:
        print >>sys.stderr, msg

xmlns_svg = "http://www.w3.org/2000/svg"
xmlns_xlink = "http://www.w3.org/1999/xlink"

def compile (svg, instructions,size=None,frame=False,noload=False):
    ns = {"svg":"http://www.w3.org/2000/svg",
          "xlink":"http://www.w3.org/1999/xlink"}
    if svg.tag != "svg" and svg.tag != "{{{}}}svg".format(xmlns_svg):
        raise Exception("root element not <svg>")
    ids = available_ids(svg)

    ##for x in ids:
    ##    print x

    print "instructions = ",instructions

    ## NOT NEEDED! 
    ##fix_display(svg)

    # instr = parse_instructions(instructions)
    
    # generate uuid
    uid = uuid.uuid4().hex
    verbose("UUID {}".format(uid))

    ##print "USE="
    ##print svg.findall(".//use")
    ##print "clipPath="
    ##print svg.findall(".//clipPath")
    
    ##for x in svg.findall(".//svg:use",ns):
    ##    print x
    ##    print x.attrib
    
    prefix = "FM_{}".format(uid)
    prefix_all_ids(svg,prefix)
    
    # should do some sort of validation here -- don't bother for now
    # should probably rename the ids to something JS-friendly
    verbose("Generating output HTML")
    ## init_shown_ids = instructions["_init"] if "_init" in instructions else []

    output = ""

#    setup = """var e=function(i){var x=document.getElementById(i);x.FM_active=true;return x;};var s=function(i){i.setAttribute("display","display");i.setAttribute("opacity","1");i.FM_active=true;};var h=function(i){i.setAttribute("display","none");};var d=function(i){i.setAttribute("display","display");i.setAttribute("opacity","0.25");i.FM_active=false;}; var evHdl=function(el,ev,f) { if (el.addEventListener) { el.addEventListener(ev,f);} else if (el.attachEvent) { el.attachEvent(ev,f); } }; var hasC=function(el,c) { var s=$(el); if (s.attr("class")) { return s.attr("class").indexOf(c) >= 0; } else { return false; }}; var addC=function(el,c) { var s=$(el); if (!(hasC(el,c))) { var cs=s.attr("class"); if (cs) { s.attr("class",(cs+" "+c).trim()); } else { s.attr("class",c.trim());}}}; var remC=function(el,c) { var s=$(el); if (hasC(el,c)) { var cs=s.attr("class"); s.attr("class",cs.replace(c," ").trim()); }};"""

    setup = """var e=function(i){var x=document.getElementById(i);x.FM_active=true;return x;};var s=function(i){i.setAttribute("display","display");i.setAttribute("opacity","1");i.FM_active=true;};var h=function(i){i.setAttribute("display","none");};var d=function(i){i.setAttribute("display","display");i.setAttribute("opacity","0.25");i.FM_active=false;}; var evHdl=function(el,ev,f) { if (el.addEventListener) { el.addEventListener(ev,f);} else if (el.attachEvent) { el.attachEvent(ev,f); } }; var hasC=function(el,c) { if (el.getAttribute("class")) { return el.getAttribute("class").indexOf(c) >= 0; } else { return false; }}; var addC=function(el,c) { if (!(hasC(el,c))) { var cs=el.getAttribute("class"); if (cs) { el.setAttribute("class",(cs+" "+c).trim()); } else { el.setAttribute("class",c.trim());}}}; var remC=function(el,c) { if (hasC(el,c)) { var cs=el.getAttribute("class"); el.setAttribute("class",cs.replace(c," ").trim()); }};"""

    ###if (el.addEventListener) { el.addEventListener(ev,f);} else if (el.attachEvent) { el.attachEvent("on"+ev,f); } };"""

    bind_ids = "".join([ "var FM_{cid} = e(\"{p}_{id}\");".format(p=prefix,cid=clean_id(id),id=id) for (id,_) in ids])

    # clean IDs because they will end up in identifiers
    ###ids = [ (clean_id(id),elt) for (id,elt) in ids]

    setup_click = ""
    setup_hover = ""
    setup_select = ""
    setup_hover_start = ""
    setup_hover_end = ""

    styling = ""

    creates = ""
    if "__create" in instructions:
        for c in instructions["__create"]:
            if c[0] == "selector":
                options = "".join(["""o=document.createElement("option");o.setAttribute("value","{}");o.innerHTML="{}";x.appendChild(o);""".format(txt,txt) for txt in c[4:]])
                creates += """(function() {{ var x=document.createElement("select");x.setAttribute("id","{prefix}_{id}"); x.style.position="absolute";x.style.left="{x}px";x.style.top="{y}px";x.style.width="100px";x.style.height="20px";{options}e("{prefix}___main_div").appendChild(x); }})();""".format(id=c[1],x=c[2],y=c[3],prefix=prefix,options=options)
                ids.append((c[1],None))
            elif c[0] == "style":
                styling += """.{prefix}_{name} {{ {body} }} """.format(prefix=prefix,name=clean_id(c[1]),body=c[2])
                
    for id in [id for (id,_) in ids if id in instructions and not id.startswith("__")]:
        ###print "checking id = {}".format(id)
        # clean ID that can be used in identifiers
        cid = clean_id(id)
        for event in instructions[id]:
            ###print "  checking event = {}".format(event)
            if event == "click":
                actions = "".join([ compile_action(act,prefix) for act in instructions[id]["click"] ])
                setup_click += "evHdl(FM_{id},\"click\",function() {{ if (this.FM_active) {{ {actions} }} }});".format(id=cid,actions=actions)
                setup_click += "FM_{id}.style.cursor=\"pointer\";".format(id=cid);
            elif event == "hover":
                do_actions = "".join([ save_action(i,act)+compile_action(act,prefix) for (i,act) in enumerate(instructions[id]["hover"])] )
                undo_actions = "".join(reversed([ restore_action(i,act) for (i,act) in enumerate(instructions[id]["hover"]) ]))
                setup_hover += "evHdl(FM_{id},\"mouseenter\",function() {{ if (this.FM_active) {{ {do_actions} }} }}); evHdl(FM_{id},\"mouseleave\",function() {{ if (this.FM_active) {{ {undo_actions} }} }});".format(id=cid,do_actions=do_actions,undo_actions=undo_actions)
            elif event == "hover-start":
                do_actions = "".join([ compile_action(act,prefix) for act in instructions[id]["hover-start"] ])
                setup_hover_start += "evHdl(FM_{id},\"mouseenter\",function() {{ if (this.FM_active) {{ {do_actions} }} }});".format(id=cid,do_actions=do_actions)
            elif event == "hover-end":
                do_actions = "".join([ compile_action(act,prefix) for act in instructions[id]["hover-end"] ])
                setup_hover_end += "evHdl(FM_{id},\"mouseleave\",function() {{ if (this.FM_active) {{ {do_actions} }} }});".format(id=cid,do_actions=do_actions)
            elif event == "select":
                change_code = ",".join([ """ "{value}" : function() {{ {actions} }} """.format(value=v,
                                                                                               actions="".join([ compile_action(act,prefix) for act in instructions[id]["select"][v]])) for v in instructions[id]["select"].keys()])
                setup_select += """evHdl(e("{prefix}_{id}"),"change",function() {{ ({{ {change_code} }}[this.value])(); }});""".format(change_code=change_code,prefix=prefix,id=id)
                

    if noload:
        script_base = """(function() {{ {setup}{creates}{bind_ids}{setup_click}{setup_hover}{setup_hover_start}{setup_hover_end}{setup_select} }})();"""
    else:
        script_base = """evHdl(window,\"load\",function() {{ {setup}{creates}{bind_ids}{setup_click}{setup_hover}{setup_hover_start}{setup_hover_end}{setup_select} }});"""
    script = script_base.format(bind_ids = bind_ids,
                                setup=setup,
                                creates=creates,
                                setup_click=setup_click,
                                setup_hover=setup_hover,
                                setup_hover_start=setup_hover_start,
                                setup_hover_end=setup_hover_end,
                                setup_select=setup_select)
    if frame:
        output += "<html><body>"
    output +=  """<div id="{}___main_div" style="position: relative; left: 0px; top:0px;">""".format(prefix)
    # suppress namespace for svg
    ET.register_namespace('',xmlns_svg)

    if size:
        svg.attrib["x"] = size["x"]
        svg.attrib["y"] = size["y"]
        svg.attrib["width"] = size["width"]
        svg.attrib["height"] = size["height"]

    if styling:
        output += """<style>{}</style>""".format(styling);
    output += ET.tostring(svg)
    output += "<script>"
    output += script
    output += "</script>"
    output += "</div>"
    if frame:
        output += "</body></html>"

    return output



def fix_display (svg):
    # take an svg and replace all the "display" attribute by "display" style tags
    for elt in svg.iter():
        if elt.get("display"):
            d = elt.get("display")
            del elt.attrib["display"]
            if elt.get("style"):
                elt.set("style","{} display:\"{}\";".format(elt.get("style"),d))
            else:
                elt.set("style","display:\"{}\";".format(d))

def available_ids (svg):
    return [(elt.get("id"),elt) for elt in svg.findall(".//*[@id]")]


def clean_id (id):
    # letting you use - in IDs without it causing problems
    # augment with others characters that may sensibly show up
    return id.replace("-","_")

            
def prefix_all_ids (svg,prefix):

    for elt in svg.findall(".//*[@id]"):
        elt.set("id","{}_{}".format(prefix,elt.get("id")))

    for elt in svg.findall(".//*[@clip-path]"):
        p = elt.get("clip-path")
        elt.set("clip-path",p.replace("#","#"+prefix+"_"))  # hack!

    xmlns_xlink = "http://www.w3.org/1999/xlink"
    for elt in svg.findall(".//*[@xlink:href]",{"xlink":xmlns_xlink}):
        p = elt.get("{{{}}}href".format(xmlns_xlink))
        elt.set("xlink:href",p.replace("#","#"+prefix+"_")) # hack!


def compile_action (act,prefix=None):
    if act["action"] == "show":
        return mk_show_ids(act["elements"])
    elif act["action"] == "hide":
        return mk_hide_ids(act["elements"])
    elif act["action"] == "dim":
        return mk_dim_ids(act["elements"])
    elif act["action"] == "style":
        c = act["elements"][0]
###        return "".join(["""FM_{}.classList.add("{}_{}");""".format(clean_id(id),prefix,clean_id(c)) for id in act["elements"][1:]])
        return "".join(["""addC(FM_{},"{}_{}");""".format(clean_id(id),prefix,clean_id(c)) for id in act["elements"][1:]])
###        return "".join(["""$(FM_{}).attr("class",($(FM_{}).attr("class")+" {}_{}").trim());""".format(clean_id(id),clean_id(id),prefix,clean_id(c)) for id in act["elements"][1:]])
    elif act["action"] == "unstyle":
        c = act["elements"][0]
###        return "".join(["""FM_{}.classList.remove("{}_{}");""".format(clean_id(id),prefix,clean_id(c)) for id in act["elements"][1:]])
        return "".join(["""remC(FM_{},"{}_{}");""".format(clean_id(id),prefix,clean_id(c)) for id in act["elements"][1:]])
###        return "".join(["""if ($(FM_{}).attr("class")) {{ $(FM_{}).attr("class",$(FM_{}).attr("class").replace(new RegExp("(\\s|^){}_{}(\\s|$)","g"),"").trim());}}; """.format(clean_id(id),clean_id(id),clean_id(id),prefix,clean_id(c)) for id in act["elements"][1:]])
        
    else:
        return ""


def save_action (i,act):
    if act["action"] in ["show","hide"]:
        return "".join([ """FM_{id}.saved_FM_display_{i}=FM_{id}.getAttribute("display");""".format(id=clean_id(id),i=i) for id in act["elements"] ])
    elif act["action"] in ["dim"]: 
        return "".join([ """FM_{id}.saved_FM_display_{i}=FM_{id}.getAttribute("display"); FM_{id}.saved_FM_opacity_{i}=FM_{id}.getAttribute("opacity"); FM_{id}.saved_FM_active_{i}=FM_{id}.FM_active;""".format(id=clean_id(id),i=i) for id in act["elements"] ])
    elif act["action"] in ["style","unstyle"]:
        return "".join([ """FM_{id}.saved_FM_class_{i}=FM_{id}.getAttribute("class");""".format(id=clean_id(id),i=i) for id in act["elements"][1:]])
    else:
        verbose("saving for action {} not implemented".format(act["action"]))
        return ""

def restore_action (i,act):
    if act["action"] in ["show","hide"]:
        return "".join([ """FM_{id}.setAttribute("display",FM_{id}.saved_FM_display_{i});""".format(id=clean_id(id),i=i) for id in act["elements"] ])
    elif act["action"] in ["dim"]: 
        return "".join([ """FM_{id}.setAttribute("display",FM_{id}.saved_FM_display_{i}); FM_{id}.setAttribute("opacity",FM_{id}.saved_FM_opacity_{i}); FM_{id}.FM_active=FM_{id}.saved_FM_active_{i};""".format(id=clean_id(id),i=i) for id in act["elements"] ])
    elif act["action"] in ["style","unstyle"]:
        return "".join([ """FM_{id}.setAttribute("class",FM_{id}.saved_FM_class_{i});""".format(id=clean_id(id),i=i) for id in act["elements"][1:]])
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
    return "".join([ "s(FM_{id});".format(id=clean_id(id)) for id in ids])

def mk_hide_ids (ids):
    return "".join([ "h(FM_{id});".format(id=clean_id(id)) for id in ids])

def mk_dim_ids (ids):
    return "".join([ "d(FM_{id});".format(id=clean_id(id)) for id in ids])
    


def parse_instructions (instrs_string):
    verbose("Parsing interaction instructions")
    instrs = {}
    instructions = []
    tokens = []

    current = ""
    for line in instrs_string.split("\n"):
        #verbose("   "+line)
        #verbose("current = "+current)

### the tokenizer takes care of comments!
#        if "#" in line:
#            line = line[:line.find("#")]

        

        tokens.extend(tok.tokenize(line))
#        if line.strip():
#            current += " "+(line.strip())
#        elif current:
#            instructions.append(current)
#            current = ""
#
#    if current:
#        instructions.append(current)

    ###verbose(len(instructions))

    #for instr in instructions:
    #    verbose("  {}".format(instr.strip()))

    instructions = split_at_periods([ s for (_,s) in tokens])

    # always have a __create
    instrs["__create"] = []

    for instr in instructions:
        parts = split_at_arrows(instr)

        if len(parts) == 1 and len(parts[0]) > 1 and parts[0][0] == "create":
            parse_create(parts[0],instrs)
            continue

        if len(parts) < 2: 
            raise Exception("Parsing error - cannot parse {}".format(instr))

        (name,event,extras) = parse_event(parts[0])
        if name not in instrs:
            instrs[name] = {}
        # clobber old event for that name if one exists
        # FIXME - merge instead??
        if event == "select":
            if "select" not in instrs[name]:
                instrs[name]["select"] = {}
            instrs[name]["select"][extras[0]] = [ parse_action(part) for part in parts[1:]]
        else:
            instrs[name][event] = [ parse_action(part) for part in parts[1:]]
    return instrs


def parse_create (create, instrs):
    # parse a create instruction
    # right now, only deal with create selector name x y v1 ...
    # result: __create: [ [selector, name, x, y, v1, ...] ]

    if len(create) > 5 and create[1] == "selector":
        instrs["__create"].append(create[1:])
    elif len(create) > 3 and create[1] == "style":
        instrs["__create"].append(create[1:])
    else:
        verbose("Ignoring unrecognized create instruction: {}".format(" ".join(create)))


def split_at_arrows (lst):
    # xxx xxx xxx -> xxx xxx xxx -> xxx xxx xx

    result = []
    current = []

    for s in lst:
        if s == "->":
            result.append(current)
            current = []
        else:
            current.append(s)

    result.append(current)
    
    return result
    
def split_at_periods (lst):
    #  xxx xxx xxx . xxx xxx xxx . xxx xxx xxx .

    result = []
    current = []

    for s in lst:
        if s in [".", ";"]:
            result.append(current)
            current = []
        else:
            current.append(s)

    if current:
        raise Exception("Parsing error - instructions not terminated with .")

    return result
    

def tokenize (s):
    # really, should not break up strings "..." or '...'
    return s.split()

def parse_event (p):
    if len(p) < 2:
        raise Exception("Parsing error - cannot parse event part of instruction {}".format(s))
    if p[0] == "select" and len(p) > 2:
        return (p[1],p[0],p[2:])
    return (p[1],p[0],[])

 
def parse_action (s):
    # p = tokenize(s)
    p = s
    if len(p) > 0 and p[0] in ["show","hide","dim","style","unstyle"]:
        return {"action":p[0],
                "elements":p[1:]}
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
