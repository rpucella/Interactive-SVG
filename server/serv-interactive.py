
from bottle import get, post, run, request, static_file, abort, redirect, template

# use a better web server
from bottle import PasteServer

import os
import sys

import xml.etree.ElementTree as ET

def available_ids (svg):
    return [(elt.get("id"),elt) for elt in svg.findall(".//*[@id]")]


xmlns_svg = "http://www.w3.org/2000/svg"

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

    svg.attrib["x"] = "0";
    svg.attrib["y"] = "0";
    svg.attrib["width"] = "500";
    svg.attrib["height"] = "300";

    return template("upload_svg",
                    page_title = "Interactive SVG",
                    code_svg = ET.tostring(svg),
                    code_ids = result,
                    ids = "[{}]".format(",".join([ "\"{}\"".format(id) for (id,_) in ids])))
                    



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


