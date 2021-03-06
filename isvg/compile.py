#
# Compile an SVG and some interactions information
# into embeddable HTML
#

import sys
import xml.etree.ElementTree as ET
import json
import re

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


import datetime

def tag ():
    year = datetime.datetime.now().year
    epoch = datetime.datetime(year,1,1)
    dt = datetime.datetime.now()
    secs = (dt - epoch).total_seconds()
    return str(int(secs))


def compile (svg, instructions,size=None,frame=False,noload=True,minimizeScript=False,widthPerc=100,ajax=None):
    ns = {"svg":"http://www.w3.org/2000/svg",
          "xlink":"http://www.w3.org/1999/xlink"}
    if svg.tag != "svg" and svg.tag != "{{{}}}svg".format(xmlns_svg):
        raise Exception("root element not <svg>")
    ids = available_ids(svg)

    ##for x in ids:
    ##    print x

    ##print "instructions = ",instructions

    set_verbose_flag(True)

    ## NOT NEEDED! 
    ##fix_display(svg)

    # instr = parse_instructions(instructions)
    
    # generate uuid
    # uid = uuid.uuid4().hex
    uid = tag()
    verbose("UUID {}".format(uid))

    ##print "USE="
    ##print svg.findall(".//use")
    ##print "clipPath="
    ##print svg.findall(".//clipPath")
    
    ##for x in svg.findall(".//svg:use",ns):
    ##    print x
    ##    print x.attrib
    
    prefix = "FM{}".format(uid)
    prefix_all_ids(svg,prefix)
    
    # should do some sort of validation here -- don't bother for now
    # should probably rename the ids to something JS-friendly
    verbose("Generating output")
    ## init_shown_ids = instructions["_init"] if "_init" in instructions else []

    output = ""

#    setup = """var e=function(i){var x=document.getElementById(i);x.FM_active=true;return x;};var s=function(i){i.setAttribute("display","display");i.setAttribute("opacity","1");i.FM_active=true;};var h=function(i){i.setAttribute("display","none");};var d=function(i){i.setAttribute("display","display");i.setAttribute("opacity","0.25");i.FM_active=false;}; var evHdl=function(el,ev,f) { if (el.addEventListener) { el.addEventListener(ev,f);} else if (el.attachEvent) { el.attachEvent(ev,f); } }; var hasC=function(el,c) { var s=$(el); if (s.attr("class")) { return s.attr("class").indexOf(c) >= 0; } else { return false; }}; var addC=function(el,c) { var s=$(el); if (!(hasC(el,c))) { var cs=s.attr("class"); if (cs) { s.attr("class",(cs+" "+c).trim()); } else { s.attr("class",c.trim());}}}; var remC=function(el,c) { var s=$(el); if (hasC(el,c)) { var cs=s.attr("class"); s.attr("class",cs.replace(c," ").trim()); }};"""

    setup = """
var e=function(i) { 
  var x=document.getElementById(i); 
  x.FM_active=true; 
  return x;
};

var s=function(i) {
  i.setAttribute("display","inline");
  i.setAttribute("opacity","1");
  i.FM_active=true;
};

var h=function(i) {
  i.setAttribute("display","none");
};

var d=function(i) {
  i.setAttribute("display","inline");
  i.setAttribute("opacity","0.25");
  i.FM_active=false;
}; 

var evHdl=function(el,ev,f) { 
  if (el.addEventListener) { 
    el.addEventListener(ev,f);
  } else if (el.attachEvent) { 
    el.attachEvent(ev,f); 
  } 
}; 

var hasC=function(el,c) { 
  if (el.getAttribute("class")) { 
    return el.getAttribute("class").indexOf(c) >= 0; 
  } else { 
    return false; 
  }
}; 

var addC=function(el,c) { 
  if (!(hasC(el,c))) { 
    var cs=el.getAttribute("class"); 
    if (cs) { 
      el.setAttribute("class",(cs+" "+c).trim()); 
    } else { 
      el.setAttribute("class",c.trim());
    }
  }
}; 

var remC=function(el,c) { 
  if (hasC(el,c)) { 
    var cs=el.getAttribute("class"); 
    el.setAttribute("class",cs.replace(c," ").trim()); 
  }
};

"""

    ###if (el.addEventListener) { el.addEventListener(ev,f);} else if (el.attachEvent) { el.attachEvent("on"+ev,f); } };"""

    bind_ids = "".join([ "var FM_{cid} = e(\"{p}_{id}\");\n\n".format(p=prefix,cid=clean_id(id),id=id) for (id,_) in ids])

    # clean IDs because they will end up in identifiers
    ###ids = [ (clean_id(id),elt) for (id,elt) in ids]

    setup_click = ""
    setup_hover = ""
    setup_select = ""
    setup_hover_start = ""
    setup_hover_end = ""

    styling = ""

    vars = ""
    creates = ""
    if "__create" in instructions:
        for c in instructions["__create"]:
            if c[0] == "selector":
                options = "".join(["""o=document.createElement("option");\n o.setAttribute("value","{}");\no.innerHTML="{}";\nx.appendChild(o);\n""".format(txt,txt) for txt in c[4:]])
                creates += """(function() {{ \n var x=document.createElement("select");\n x.setAttribute("id","{prefix}_{id}");\n x.style.position="absolute";\n x.style.left="{x}px";\n x.style.top="{y}px";\n x.style.width="100px";\n x.style.height="20px";\n {options}\n e("{prefix}___main_div").appendChild(x);\n }})();\n""".format(id=c[1],x=c[2],y=c[3],prefix=prefix,options=options)
                ids.append((c[1],None))
            elif c[0] == "style":
                styling += """.{prefix}_{name} {{\n  {body}\n  }}\n """.format(prefix=prefix,name=clean_id(c[1]),body=c[2])
            elif c[0] == "variable":
                vars += "".join([ """var {p}_{n} = 0;""".format(p=prefix,n=n) for n in c[1:]])


    init = ""
    if "__init" in instructions:
        ##print "__init = ",instructions["__init"]
        init = "".join([ compile_action(act,prefix) for act in instructions["__init"]])

    show = ""
    if "__show" in instructions:
        actions = "".join([ compile_action(act,prefix) for act in instructions["__show"]])
        show = """var didScroll = true; 
                   var showStarted = false;
                   var intervalID; 
                   var main_el = e("{prefix}___main_div");
                   var checkAnimation = function() {{ 
                     if (showStarted) {{
                        return; 
                     }};
                     if (didScroll) {{ 
                        didScroll = false; 
                        var rect = main_el.getBoundingClientRect(); 
                        if (rect.top <= (window.innerHeight || document.documentElement.clientHeight)/2) {{ 
                          showStarted = true; 
                          window.clearInterval(intervalID);
                          {actions};
                        }}
                     }}
                   }};
                   evHdl(window,"scroll",function() {{ didScroll = true; }}); 
                   intervalID = window.setInterval(function() {{ if (didScroll) {{ checkAnimation(); }} }}, 500);
                """.format(prefix=prefix,
                           actions=actions)
                
    for id in [id for (id,_) in ids if id in instructions and not id.startswith("__")]:
        ###print "checking id = {}".format(id)
        # clean ID that can be used in identifiers
        cid = clean_id(id)
        for event in instructions[id]:

            ###print "  checking event = {}".format(event)

            if event == "click":
                actions = "".join([ compile_action(act,prefix) for act in instructions[id]["click"] ])
                setup_click += "evHdl(FM_{id},\"click\",function() {{\n  if (this.FM_active) {{ \n {actions} \n }} \n}});\n".format(id=cid,actions=actions)
                setup_click += "FM_{id}.style.cursor=\"pointer\";".format(id=cid);

            elif event == "hover":
                do_actions = "".join([ save_action(i,act)+compile_action(act,prefix) for (i,act) in enumerate(instructions[id]["hover"])] )
                undo_actions = "".join(reversed([ restore_action(i,act) for (i,act) in enumerate(instructions[id]["hover"]) ]))
                setup_hover += "evHdl(FM_{id},\"mouseenter\",function() {{ \n if (this.FM_active) {{ \n {do_actions} \n }} \n}}); \n evHdl(FM_{id},\"mouseleave\",function() {{ \n if (this.FM_active) {{ \n {undo_actions} \n }} \n}});\n".format(id=cid,do_actions=do_actions,undo_actions=undo_actions)

            elif event == "hover-start":
                do_actions = "".join([ compile_action(act,prefix) for act in instructions[id]["hover-start"] ])
                setup_hover_start += "evHdl(FM_{id},\"mouseenter\",function() {{ \n if (this.FM_active) {{ \n {do_actions} \n }} \n}});\n".format(id=cid,do_actions=do_actions)

            elif event == "hover-end":
                do_actions = "".join([ compile_action(act,prefix) for act in instructions[id]["hover-end"] ])
                setup_hover_end += "evHdl(FM_{id},\"mouseleave\",function() {{ \n if (this.FM_active) {{ \n {do_actions} \n }} \n}});\n".format(id=cid,do_actions=do_actions)

            elif event == "select":
                change_code = ",".join([ """ "{value}" : function() {{ {actions} }} """.format(value=v,
                                                                                               actions="".join([ compile_action(act,prefix) for act in instructions[id]["select"][v]])) for v in instructions[id]["select"].keys()])
                setup_select += """evHdl(e("{prefix}_{id}"),"change",function() {{ \n ({{ \n{change_code} \n }}[this.value])(); \n}});\n""".format(change_code=change_code,prefix=prefix,id=id)

    # if noload:
    #     script_base = """(function() {{ {setup}{creates}{bind_ids}{setup_click}{setup_hover}{setup_hover_start}{setup_hover_end}{setup_select}{init}{show} }})();"""
    # else:
    #     # may fail on IE -- use noload
    #     script_base = """window.addEventListener(\"load\",function() {{ \n {setup}{creates}{bind_ids}{setup_click}{setup_hover}{setup_hover_start}{setup_hover_end}{setup_select}{init}{show} }});\n"""

    script_base = """var run_{prefix} = function() {{ {vars}{setup}{creates}{bind_ids}{setup_click}{setup_hover}{setup_hover_start}{setup_hover_end}{setup_select}{init}{show} }};\n"""
    script = script_base.format(vars=vars,
                                prefix=prefix,
                                bind_ids = bind_ids,
                                setup=setup,
                                creates=creates,
                                setup_click=setup_click,
                                setup_hover=setup_hover,
                                setup_hover_start=setup_hover_start,
                                setup_hover_end=setup_hover_end,
                                setup_select=setup_select,
                                init=init,
                                show=show)

    if frame:
        output += """<html><body><div style="width:600px; margin: 0px auto;">"""

    def clean_dim (dim):
        return int(float(dim.replace("px","")))

    if size:
        padding = int(1+100*float(clean_dim(size["height"]))/float(clean_dim(size["width"])))
    else:
        padding = 0
    ## Fix to allow resizing on most browsers (mostly need to fix IE11+)
    ##output +=  """<div id="{}___main_div" style="position: relative; left: 0px; top:0px;">""".format(prefix)
    output +=  """<div id="{}___main_div" style="position: relative; left: 0px; top:0px; height:0; width: {}%; padding-top: {}%;">""".format(prefix,widthPerc,padding)

    # suppress namespace for svg
    ET.register_namespace('',xmlns_svg)

    def delete_svg_attrib (attr):
        try:
            svg.attrib.pop(attr)
        except KeyError:
            pass
        
    if size:
        svg.attrib["x"] = size["x"]
        svg.attrib["y"] = size["y"]
        ##svg.attrib["width"] = size["width"]
        ##svg.attrib["height"] = size["height"]
        delete_svg_attrib("height")
        delete_svg_attrib("width")
        svg.attrib["viewBox"] = "0 0 {} {}".format(clean_dim(size["width"]),clean_dim(size["height"]))
        svg.attrib["style"] = "position: absolute; top:0; left:0;" 

        

    if styling:
        output += """<style>{}</style>""".format(styling);

    if not ajax:
        output += ET.tostring(svg)
    else:
        fname_svg = "{}.svg".format(ajax)
        print "Saving SVG file [{}]".format(fname_svg)
        with open(fname_svg,"wb") as fout:
            fout.write(ET.tostring(svg))

    if minimizeScript:
        script = minimize(script)

    if ajax:
        fname_js = "{}.js".format(ajax)
        print "Saving JS file [{}]".format(fname_js)
        with open(fname_js,"wb") as fout:
            fout.write(script)

        output += """<script src="{}"></script>""".format(fname_js)
        output += """<script>
         (function() {{
           xhr = new XMLHttpRequest();
           xhr.open("GET","{fname}",true);
           xhr.overrideMimeType("image/svg+xml");
           xhr.onload = function(e) {{
             if (xhr.readyState === 4) {{
               if (xhr.status === 200) {{
                 var elt = document.importNode(xhr.responseXML.documentElement,true);
                 document.getElementById("{prefix}___main_div")
                         .appendChild(elt);
                 run_{prefix}();
               }} else {{
                 console.error(xhr.statusText);
               }}
             }}
           }};
           xhr.onerror = function(e) {{
             console.error(xhr.statusText);
           }};
           xhr.send(null);
         }})();
         </script>""".format(prefix=prefix,fname=fname_svg)
    else:
        output += "<script>"
        output += script
        output += """(function() {{ run_{}(); }})();""".format(prefix)
        output += "</script>"

    output += "</div>"

    if frame:
        output += "</div></body></html>"

    return output


def minimize (inp):

    return re.sub("\s+"," ",inp).strip()



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
    elif act["action"] == "apply":
        c = act["elements"][0]
###        return "".join(["""FM_{}.classList.add("{}_{}");""".format(clean_id(id),prefix,clean_id(c)) for id in act["elements"][1:]])
        return "".join(["""addC(FM_{},"{}_{}");\n""".format(clean_id(id),prefix,clean_id(c)) for id in act["elements"][1:]])
###        return "".join(["""$(FM_{}).attr("class",($(FM_{}).attr("class")+" {}_{}").trim());""".format(clean_id(id),clean_id(id),prefix,clean_id(c)) for id in act["elements"][1:]])
    elif act["action"] == "remove":
        c = act["elements"][0]
###        return "".join(["""FM_{}.classList.remove("{}_{}");""".format(clean_id(id),prefix,clean_id(c)) for id in act["elements"][1:]])
        return "".join(["""remC(FM_{},"{}_{}");\n""".format(clean_id(id),prefix,clean_id(c)) for id in act["elements"][1:]])
###        return "".join(["""if ($(FM_{}).attr("class")) {{ $(FM_{}).attr("class",$(FM_{}).attr("class").replace(new RegExp("(\\s|^){}_{}(\\s|$)","g"),"").trim());}}; """.format(clean_id(id),clean_id(id),clean_id(id),prefix,clean_id(c)) for id in act["elements"][1:]])
    elif act["action"] == "delay":
        t = act["time"]
        subact = compile_action(act["delayed_action"],prefix)
        return """window.setTimeout(function() {{ {act} }}, {t});\n""".format(act=subact,t=t)
    elif act["action"] == "js":
        if prefix:
            return """(function(prefix) {{ {} }})("{}");""".format(act["elements"][0],prefix)
        else:
            return act["elements"][0]
        
    elif act["action"] == "set":
        return "{p}_{n} = {v}".format(p=prefix,n=act["variable"],v=act["value"])

    elif act["action"] == "ifzero":
        subact = compile_action(act["conditional_action"],prefix)
        return "if ({p}_{n} == 0) {{ {c} }};".format(p=prefix,n=act["variable"],c=subact)
    
    else:
        return ""


def save_action (i,act):
    if act["action"] in ["show","hide"]:
        return "".join([ """FM_{id}.saved_FM_display_{i}=FM_{id}.getAttribute("display");""".format(id=clean_id(id),i=i) for id in act["elements"] ])
    elif act["action"] in ["dim"]: 
        return "".join([ """FM_{id}.saved_FM_display_{i}=FM_{id}.getAttribute("display"); FM_{id}.saved_FM_opacity_{i}=FM_{id}.getAttribute("opacity"); FM_{id}.saved_FM_active_{i}=FM_{id}.FM_active;""".format(id=clean_id(id),i=i) for id in act["elements"] ])
    elif act["action"] in ["apply","remove"]:
        return "".join([ """FM_{id}.saved_FM_class_{i}=FM_{id}.getAttribute("class");""".format(id=clean_id(id),i=i) for id in act["elements"][1:]])
    else:
        verbose("saving for action {} not implemented".format(act["action"]))
        return ""

def restore_action (i,act):
    if act["action"] in ["show","hide"]:
        return "".join([ """FM_{id}.setAttribute("display",FM_{id}.saved_FM_display_{i});""".format(id=clean_id(id),i=i) for id in act["elements"] ])
    elif act["action"] in ["dim"]: 
        return "".join([ """FM_{id}.setAttribute("display",FM_{id}.saved_FM_display_{i}); FM_{id}.setAttribute("opacity",FM_{id}.saved_FM_opacity_{i}); FM_{id}.FM_active=FM_{id}.saved_FM_active_{i};""".format(id=clean_id(id),i=i) for id in act["elements"] ])
    elif act["action"] in ["apply","remove"]:
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
    return "".join([ "s(FM_{id});\n".format(id=clean_id(id)) for id in ids])

def mk_hide_ids (ids):
    return "".join([ "h(FM_{id});\n".format(id=clean_id(id)) for id in ids])

def mk_dim_ids (ids):
    return "".join([ "d(FM_{id});\n".format(id=clean_id(id)) for id in ids])
    


def parse_instructions (instrs_string):
    verbose("Parsing interaction instructions")
    instrs = {}
    instructions = []
    tokens = []

    if not instrs_string:
        return {}

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
    # instrs["__init"] = []
    # instrs["__show"] = []

    for instr in instructions:
        parts = split_at_arrows(instr)

        if len(parts) == 1 and len(parts[0]) > 1 and parts[0][0] == "create":
            parse_create(parts[0],instrs)
            continue

        if len(parts) == 1 and len(parts[0]) > 1 and parts[0][0] == "define":
            parse_define(parts[0],instrs)
            continue

        if len(parts) < 2: 
            raise Exception("Parsing error - cannot parse {}".format(instr))

        if len(parts[0]) == 1 and parts[0][0] == "__init__":
            parse_init(parts[1:],instrs)
            continue

        if len(parts[0]) == 1 and parts[0][0] == "__show__":
            parse_show(parts[1:],instrs)
            continue

        (name,event,extras) = parse_event(parts[0])
        if name not in instrs:
            instrs[name] = {}
        # clobber old event for that name if one exists
        # FIXME - merge instead?? extend?
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
    else:
        verbose("Ignoring unrecognized create instruction: {}".format(" ".join(create)))


def parse_define (create, instrs):
    
    if len(create) > 3 and create[1] == "style":
        instrs["__create"].append(create[1:])
    elif len(create) > 3 and create[1] == "variable":
        instrs["__create"].append(create[1:])
    else:
        verbose("Ignoring unrecognized define instruction: {}".format(" ".join(create)))


def parse_init (actions_parts,instrs):
    act = [ parse_action(part) for part in actions_parts]
    if "__init" in instrs:
        instrs["__init"].extend(act)
    else:
        instrs["__init"] = act
    
def parse_show (actions_parts,instrs):
    act = [ parse_action(part) for part in actions_parts]
    if "__show" in instrs:
        instrs["__show"].extend(act)
    else:
        instrs["__show"] = act
        

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
    if len(p) > 0 and p[0] in ["show","hide","dim","apply","remove","js"]:
        # print "action = ",p[0]
        # print "elements = "
        # for x in p[1:]:
        #     print "  ",x
        return {"action":p[0],
                "elements":p[1:]}
    if len(p) > 2 and p[0] == "set":
        return {"action":p[0],
                "variable":p[1],
                "value":p[2]}
    if len(p) > 2 and p[0] == "ifzero":
        return {"action":p[0],
                "variable":p[1],
                "conditional_action":parse_action(s[2:])}
    
    if len(p) > 2 and p[0] == "fadein":
        return {"action":p[0],
                "time":int(p[1]),
                "elements":p[2:]}
    if len(p) > 3 and p[0] == "delay": 
        return {"action":p[0],
                "time":int(p[1]),
                "delayed_action":parse_action(s[2:])}
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

def get_fonts (svg):
    # pull out all fonts from elements
    ns = {"svg":"http://www.w3.org/2000/svg",
          "xlink":"http://www.w3.org/1999/xlink"}
    # get all elements with a fontFamily attribute
    fontedElts = [elt for elt in svg.findall(".//*[@font-family]")]
    fonts = set()
    for elt in fontedElts:
        fonts.add(elt.get("font-family"))
    return list(fonts)


def fix_fonts (svg,target):
    # turn all fonts to sans-serif
    # optimized on how AI handles fonts
    # if you recognize a font as being Bold, replace by fontWeight="bold" if appropriate
    fontedElts = [elt for elt in svg.findall(".//*[@font-family]")]
    for elt in fontedElts:
        if elt.get("font-family") not in target:  # check
            if "-bd" in elt.get("font-family").lower():
                elt.set("font-family",target)
                elt.set("font-weight","bold")
            elif "-boldmt" in elt.get("font-family").lower():
                elt.set("font-family",target)
                elt.set("font-weight","bold")
            else: 
                elt.set("font-family",target)
    # supposedly, the above does the modification in-place in the svg
    # (each element remembers where it came from? An element is just a reference to 
    #  an svg location?)
    return svg

    

