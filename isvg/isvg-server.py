
############################################################
# Server-based interactive SVG editor
#
#
# to use:
#   python isvg-server 8080
#
# Point your browser to localhost:8080
#



from bottle import get, post, run, request, static_file, abort, redirect, template
# use a better web server than the default
from bottle import PasteServer

import os
import sys

import xml.etree.ElementTree as ET

import compile

import json



@get("/")
@get("/isvg")
@get("/isvg/")
def GET_root ():

    redirect("/isvg/edit_svg")

    
@get("/isvg/create_svg")
def GET_chart ():

    return static_file("test_create.html","static")


@get("/isvg/edit_svg")
def GET_edit_svg ():

    return template("edit_svg",
                    page_title = "Interactive SVG Editor",
                    code_svg = "",
                    initial_instr = "",
                    svg_data = "{}")


@post("/isvg/api/upload_svg")
def POST_upload_svg ():
    # called by SVG editor when submitting a SVG for upload

    print "file = ", request.files.get("file")

    upload = request.files.get("file")
    tree = ET.parse(upload.file)
    svg = tree.getroot()

    result = process_svg(svg)

    # read instructions from input if it exists
    instr_string = None
    
    upload.file.seek(0)
    for line in upload.file:
        if has_interactive_script(line):
            instr_string = ""
        elif line.strip() == "-->":
            break
        elif instr_string is not None: 
            instr_string += line
            
    if instr_string is None:
        instr_string = ""

    result["instr"] = instr_string

    result["fonts"] = compile.get_fonts(svg)
        
    return result



@post("/isvg/api/fix_fonts_svg")
def POST_upload_svg ():
    # called by SVG editor when submitting a SVG for upload

    print "file = ", request.files.get("file")

    ox = request.forms.get("ox")
    oy = request.forms.get("oy")
    ow = request.forms.get("ow")
    oh = request.forms.get("oh")

    upload = request.files.get("file")
    tree = ET.parse(upload.file)
    svg = tree.getroot()

    svg = compile.fix_fonts(svg,"sans-serif")

    svg.attrib["x"] = ox
    svg.attrib["y"] = oy
    svg.attrib["width"] = ow
    svg.attrib["height"] = oh
    
    result = process_svg(svg)

    # read instructions from input if it exists
    instr_string = None
    
    upload.file.seek(0)
    for line in upload.file:
        if has_interactive_script(line):
            instr_string = ""
        elif line.strip() == "-->":
            break
        elif instr_string is not None: 
            instr_string += line
            
    if instr_string is None:
        instr_string = ""

    result["instr"] = instr_string

    result["fonts"] = compile.get_fonts(svg)
        
    return result



def has_interactive_script (line):

    return (line.strip() == "<!--FM INTERACTIVE SVG SCRIPT")



def process_svg (svg):

    if svg.tag != "svg" and svg.tag != "{{{}}}svg".format(compile.xmlns_svg):
        raise Exception("root element not <svg>")
    ids = compile.available_ids(svg)

    result = ""
    if ids:
        w = max([len(id) for (id,elt) in ids])
        for (id,elt) in ids:
            result += """<li><input id="checkbox_{id}" type="checkbox" {checked}></input><label for="checkbox_{id}" style="margin-left: 10px;">{id}</label></li>\n
                      """.format(checked="" if elt.get("display")=="none" else "checked",
                                 id=id)

    ET.register_namespace('',compile.xmlns_svg)
    ET.register_namespace('xlink',compile.xmlns_xlink)

    original_x = svg.attrib["x"] if "x" in svg.attrib else "0"
    original_y = svg.attrib["y"] if "y" in svg.attrib else "0"
    original_width = svg.attrib["width"]
    original_height = svg.attrib["height"]

    svg.attrib["x"] = "0";
    svg.attrib["y"] = "0";
    svg.attrib["width"] = "100%";
    svg.attrib["height"] = "100%";
    svg.attrib["xml:space"] = "preserve";

    return {"svg": ET.tostring(svg),
            "ids_list": result,
            "original_x": original_x,
            "original_y": original_y,
            "original_width": original_width,
            "original_height": original_height,
            "ids": [ id for (id,_) in ids]}

    
@post("/isvg/api/edit_svg")
def POST_edit_svg ():
    # Called by external routines that _create_ svgs for editing

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


    result = process_svg(svg)

    ##print "JSON:",
    ##print json.dumps(result)
        
    # deal with instructions if they are present
    instr_string = None

    if source == "file":
             upload.file.seek(0)
             for line in upload.file:
                if has_interactive_script(line):
                    instr_string = ""
                elif line.strip() == "-->":
                    break
                elif instr_string is not None: 
                    instr_string += line

    elif source == "chart":
        for line in svg_string.split("\n"):
                if has_interactive_script(line):
                    instr_string = ""
                elif line.strip() == "-->":
                    break
                elif instr_string is not None: 
                    instr_string += line+"\n"
        
    if instr_string is None:
        instr_string = ""

    svg_data = {"ids_list": result["ids_list"],
                "original_x": result["original_x"],
                "original_y": result["original_y"],
                "original_width": result["original_width"],
                "original_height": result["original_height"],
                "ids": result["ids"]}

    return template("edit_svg",
                    page_title = "Interactive SVG Editor",
                    code_svg = result["svg"],
                    initial_instr = instr_string,
                    svg_data = json.dumps(svg_data))



@post("/isvg/api/compile_svg")
def POST_compile_svg ():
    # called by SVG editor when asked to compile an SVG + a script

    svg = request.forms.get("svg")
    instr = request.forms.get("instr")
    ox = request.forms.get("ox")
    oy = request.forms.get("oy")
    ow = request.forms.get("ow")
    oh = request.forms.get("oh")
    frame = request.forms.get("frame")
    minimize = request.forms.get("minimize")
    widthPerc = request.forms.get("widthPerc")

    try:
        widthPerc = int(widthPerc)
    except:
        widthPerc = 100

    svg_tree = ET.fromstring(svg)
    instructions = compile.parse_instructions(instr)
    frame = True if frame == "true" else False
    minimize = True if minimize == "true" else False

    size = {"x":ox,
            "y":oy,
            "width":ow,
            "height":oh}

    result = compile.compile (svg_tree,instructions,size=size,frame=frame,noload=True,minimizeScript=minimize,widthPerc=widthPerc)

    return result

    

# can run non-interactively by calling with 
#  python -i serv-dataviz.py
# it will give an error (port is not given)
# but will remain alive

if __name__ == "__main__":
    if len(sys.argv) > 1:
        port = int(sys.argv[1])
        run(reloader=True,server=PasteServer, host='0.0.0.0', port=port, debug=True)
    else:
        print "Usage: server <port>"
else:
    print "(loaded)"

