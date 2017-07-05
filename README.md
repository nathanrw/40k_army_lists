My 40k Army Lists
=================

A place to put warhammer 40k army lists and a script, generate.py, to convert
them into a convenient 'quick reference card' for with cost breakdown and force
organisation chart.

To use the script, it should simply be run in this directory. A 'docs'
subdirectory will be generated containing an 'index' page and a html document
for each army list in the 'lists' subdirectory. Army lists are expressed in YAML
and reference models and weapons given in the .csv files in the 'data'
subdirectory.

Alternatively the 'write_army()' function could be used to serve html as a web
page, but I've not done anything webby here - the primary purpose of this project
is as a cost calculator and for quick reference printing.

You can view the most recently generated army lists at https://nathanwoodward.github.io/40k_army_lists/
