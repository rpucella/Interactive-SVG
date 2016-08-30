
from bottle import get, post, run, request, static_file, abort, redirect, template

# use a better web server
from bottle import PasteServer

import os
import sys

import xml.etree.ElementTree as ET
import core



def announce (s):
    print "--------------------------------------------------"
    print s

@get("/")
def GET_root ():
    redirect("/upload_svg")
    

@get("/upload_svg")
def GET_upload_svg ():

    announce("GET /upload_svg")
    
    return static_file("test_upload.html","static")


@get("/create_svg")
def GET_chart ():

    announce("GET /create_svg")

    return static_file("test_create.html","static")
    
    
@post("/edit_svg")
def POST_edit_svg ():

    announce("POST /edit_svg")

    source = request.forms.get("source")

    print "source = ",source

    if source == "file":
        upload = request.files.get("file")
        tree = ET.parse(upload.file)
        svg = tree.getroot()
    
    elif source == "chart":
        svg_string = request.forms.get("file")
        # print svg_string
        svg = ET.fromstring(svg_string)
        
    else:
        print "Unknown source!"
        abort(500,"Unknown source {}".format(source))
        
    if svg.tag != "svg" and svg.tag != "{{{}}}svg".format(core.xmlns_svg):
        raise Exception("root element not <svg>")
    ids = core.available_ids(svg)

    result = ""
    if ids:
        w = max([len(id) for (id,elt) in ids])
        for (id,elt) in ids:
            result += """<li><input id="checkbox_{id}" type="checkbox" {checked}></input><label for="checkbox_{id}" style="margin-left: 10px;">{id}</label></li>\n
                      """.format(checked="" if elt.get("display")=="none" else "checked",
                                 id=id)

    ET.register_namespace('',core.xmlns_svg)
    ET.register_namespace('xlink',core.xmlns_xlink)

    original_x = svg.attrib["x"] if "x" in svg.attrib else "0"
    original_y = svg.attrib["y"] if "y" in svg.attrib else "0"
    original_width = svg.attrib["width"]
    original_height = svg.attrib["height"]

    svg.attrib["x"] = "0";
    svg.attrib["y"] = "0";
    svg.attrib["width"] = "500";
    svg.attrib["height"] = "300";
    svg.attrib["xml:space"] = "preserve";

    instr_string = None

    if source == "file":
             upload.file.seek(0)
             for line in upload.file:
                if line.strip() == "<!--FANTOMAS":
                    instr_string = ""
                elif line.strip() == "-->":
                    break
                elif instr_string is not None: 
                    instr_string += line

    elif source == "chart":
        for line in svg_string.split("\n"):
                if line.strip() == "<!--FANTOMAS":
                    instr_string = ""
                elif line.strip() == "-->":
                    break
                elif instr_string is not None: 
                    instr_string += line+"\n"
        
    if instr_string is None:
        instr_string = ""
        

    return template("edit_svg",
                    page_title = "Interactive SVG Editor",
                    code_svg = ET.tostring(svg),
                    code_ids = result,
                    initial_instr = instr_string,
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
    frame = request.forms.get("frame")

    svg_tree = ET.fromstring(svg)
    instructions = core.parse_instructions(instr)
    frame = True if frame == "true" else False

    size = {"x":ox,
             "y":oy,
             "width":ow,
             "height":oh}

    ###core.set_verbose_flag(True)

    result = core.compile (svg_tree,instructions,size=size,frame=frame,noload=True)

    return result

    

ROOT = "static"

@get('/<path:path>')
def static (path="index.html"):
    return static_file(path, root=ROOT)


# can run non-interactively by calling with 
#  python -i serv-dataviz.py
# it will give an error (port is not given)
# but will remain alive

if __name__ == "__main__":
    if len(sys.argv) > 1:
        port = int(sys.argv[1])
        run(reloader=True,server=PasteServer, host='0.0.0.0', port=port)
    else:
        print "Usage: server <port>"
else:
    print "(loaded)"


