
from compile import *



def show_available_ids (ids):
    if ids:
        verbose("Available IDs:")
        w = max([len(id) for (id,elt) in ids])
        for (id,elt) in ids:
            verbose("  {}   {}".format((id+" "*w)[:w],elt.tag))
    else:
        verbose("No available IDs")


def main (svgfile, insfile,frame,noload):

    set_verbose_flag(True)

    verbose("Reading SVG [{}]".format(svgfile))
    tree = ET.parse(svgfile)
    svg = tree.getroot()

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

        output = compile(svg,instr,size=size,frame=frame,noload=noload)
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
                    output = compile(svg,instr,size=size,frame=frame,noload=noload)
                    print output
                    return
                elif instr_string is not None: 
                    instr_string += line



if __name__ == "__main__":
    if len(sys.argv) < 2:
        print "Usage: isvg <svg> [<instructions>] [-frame] [-noload]"
    else:
        main(sys.argv[1],
             sys.argv[2] if len(sys.argv)>2 else None,
             len(sys.argv)>3 and "-frame" in sys.argv[3:],
             len(sys.argv)>3 and "-noload" in sys.argv[3:])
else:
    print "(loaded)"
