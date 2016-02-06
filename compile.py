#
# Compile an SVG and some interactions information
# into embeddable HTML
#

import sys
import xml.etree.ElementTree as ET

def available_ids (svg):
    return [(elt.get("id"),elt.tag) for elt in svg.findall(".//*[@id]")]

def show_available_ids (ids):
    if ids:
        print "available IDs:"
        w = max([len(id) for (id,tag) in ids])
        for (id,tag) in ids:
            print "  {}   {}".format((id+" "*w)[:w],tag)
    else:
        print "no available IDs"

xmlns_svg = "http://www.w3.org/2000/svg"


def main (svgfile, insfile):
    ns = {"svg":"http://www.w3.org/2000/svg"}
    print "reading SVG [{}]".format(svgfile)
    tree = ET.parse(svgfile)
    svg = tree.getroot()
    if svg.tag != "svg" and svg.tag != "{{{}}}svg".format(xmlns_svg):
        raise Exception("root element not <svg>")
    ids = available_ids(svg)
    show_available_ids(ids)
    print "reading interactions instructions [{}]".format(insfile)

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print "Usage: compile <svg> <instructions>"
    else:
        main(sys.argv[1],sys.argv[2])
