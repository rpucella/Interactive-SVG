
from compile import *

import optparse


def show_available_ids (ids):
    if ids:
        verbose("Available IDs:")
        w = max([len(id) for (id,elt) in ids])
        for (id,elt) in ids:
            verbose("  {}   {}".format((id+" "*w)[:w],elt.tag))
    else:
        verbose("No available IDs")


def main (svgfile, insfile,frame,load,ajax,fixfonts):

    #  !!
    noload = not load

    set_verbose_flag(True)

    verbose("Reading SVG [{}]".format(svgfile))
    tree = ET.parse(svgfile)
    svg = tree.getroot()

    if fixfonts:
        svg = fix_fonts(svg,"Arial,sans-serif")

    original_x = svg.attrib["x"] if "x" in svg.attrib else "0"
    original_y = svg.attrib["y"] if "y" in svg.attrib else "0"
    original_width = svg.attrib["width"]
    original_height = svg.attrib["height"]

    size = {"x":original_x,
             "y":original_y,
             "width":original_width,
             "height":original_height}

    ids = available_ids(svg)
    show_available_ids(ids)
    
    if insfile:
        # we have an instruction file

        verbose("Reading interaction instructions [{}]".format(insfile))
        instr = load_instructions(insfile)

        output = compile(svg,instr,size=size,frame=frame,noload=noload,ajax=ajax,minimizeScript=True)
        if ajax:
            fname_html = "{}.html".format(ajax)
            print "Saving HTML file [{}]".format(fname_html)
            with open(fname_html,"wb") as fout:
                fout.write(output)
        else:
            print output

    else:
        #check to see if we can read it from the SVG itself
        
        with open(svgfile,"r") as f:
            instr_string = None
            for line in f:
                if line.strip() == "<!--FM INTERACTIVE SVG SCRIPT":
                    verbose("Reading instructions from SVG file")
                    instr_string = ""
                elif line.strip() == "-->":
                    instr = parse_instructions(instr_string)
                    output = compile(svg,instr,size=size,frame=frame,noload=noload,ajax=ajax,minimizeScript=True)
                    if ajax:
                        fname_html = "{}.html".format(ajax)
                        print "Saving HTML file [{}]".format(fname_html)
                        with open(fname_html,"wb") as fout:
                            fout.write(output)
                    else:
                        print output
                    return
                elif instr_string is not None: 
                    instr_string += line



if __name__ == "__main__":
    parser = optparse.OptionParser(usage="%prog [options] <svg> [<instructions>]")
    parser.add_option("--frame", dest="frame", action="store_true", default=False)
    parser.add_option("--onload", dest="onload", action="store_true", default=False)
    parser.add_option("--fixfonts", dest="fixfonts", action="store_true", default=False)
    parser.add_option("--ajax", dest="ajax", action="store")
    options, positional = parser.parse_args()
    if len(positional) > 0: 
        main(positional[0],
             positional[1] if len(positional)>1 else None,
             options.frame,
             options.onload,
             options.ajax,
             options.fixfonts)
    else:
        parser.error("SVG file required")
else:
    print "(loaded)"
