
## To install

The only important file is `compile.py`, which is the Python script
that turns an SVG and an instructions file into embeddable HTML
code. That file can live anywhere.

You will need [Python 2.7](https://www.python.org/downloads/).


## To use

Usage: `python compile.py <svg> [<instructions>] [-frame] [-noload]`

You will need an SVG file, say `sample.svg`.

Running 

  `python compile.py sample.svg` 

from the directory containing `compile.py` will list all the
available element IDs that you can use in your instructions file.

To create an HTML file that incorporates the SVG (say, `sample.svg`)
and the desired interaction (say, `interaction.txt`), run 

  `python compile.py sample.svg interaction.txt > out.html`

This will create a file `out.html` containing the embeddable HTML code
that you can open in a web browser to test. 

You can specify a flag `-noload` to initialize the interaction
directly upon loading the HTML as opposed to waiting for the page
`load` event. (Recommended)

  `python compile.py sample.svg interaction.txt -noload > out.html`


## Format of the instructions file

The instructions file is a simple text file containing a sequence of
interaction instructions. An interaction instruction has the following
form:

   _trigger_ _id_ `->` _action_ _id_ ... _id_ `->` ... -> _action_ _id_ ... _id_

which described a sequence of actions to be performed when the given
trigger is performed. 

A trigger is one of:
* `click`: the user clicks on the specified element (given by the
following ID)
* `hover`: the user hovers over the specified element (given by the
following ID)

An action is one of:
* `show`: make the elements specified by the following IDs visible
* `hide`: make the elements specified by the following IDs invisible

The actions triggered by a `hover` are automatically undone when the
user stops hovering. The actions triggered by a `click` remain until
undone explicitly by another trigger.

For example:

   `click red -> show back -> hide red text_red`

specifies that upon a click on element with ID `red`, the element
`back` should be made visible, and then the elements `red` and
`text_red` should be made invisible.
