
## To install

Download and unzip the files in their own folder. The code is in the `isvg/` folder.
The main command line entry point is `isvg.py`, which is the Python script
that turns an SVG and an instructions file into embeddable HTML
code.

There is also a web app that can be used to run the script with a browser-based interface.

You will need [Python 2.7](https://www.python.org/downloads/).


## To use

Usage: `python isvg.py <svg> [<instructions>] [-frame] [-noload]`

You will need an SVG file, say `sample.svg`.

Running 

  `python isvg.py sample.svg`

from the directory containing `isvg.py` will list all the
available element IDs in `sample.svg` that you can use in your
instructions file. 

To create an HTML file that incorporates the SVG (say, `sample.svg`)
and the desired interaction (say, `interactions.txt`), run 

  `python isvg.py sample.svg interactions.txt > out.html`

This will create a file `out.html` containing the embeddable HTML code
that you can open in a web browser to test. 

You can specify a flag `-noload` to initialize the interaction
directly upon loading the HTML as opposed to waiting for the page
`load` event. (Recommended)

  `python isvg.py sample.svg interaction.txt -noload > out.html`


## Format of the instructions file

The instructions file is a simple text file containing a sequence of
interaction instructions. 

An interaction instruction has the following form:

   _trigger_ _id_ `->` _action_ _id_ ... _id_ `->` ... -> _action_ _id_ ... _id_`.`

which describes a sequence of actions to be performed when the given
trigger happens. It must be terminated by a period.

A trigger is one of:
* `click`: the user clicks on the specified element (given by the
following ID)
* `hover`: the user hovers over the specified element (given by the
following ID)
* `hover-start`: the user starts to hover over the specified element
(given by the following ID) -- nothing gets undone when the user stops hovering over the
element. 


An action is one of:
* `show`: make the elements specified by the following IDs visible
* `hide`: make the elements specified by the following IDs invisible

The actions triggered by a `hover` are automatically undone when the
user stops hovering. The actions triggered by a `click` remain until
undone explicitly by another trigger.

For example:

   `click red -> show back -> hide red text_red.`

specifies that upon a click on element with ID `red`, the element
`back` should be made visible, and then the elements `red` and
`text_red` should be made invisible.


## Running the web app

Start the web app using

  `python isvg-server.py 8080`

where 8080 can be replaced by any available port number on your machine.

To use the web app once the server is running, simply point your browser
to `localhost:8080` where 8080 should be replaced by the port number you
specified when you started the server.
