#!/bin/env python

"""
A warhammer 40,000 army list calculator.  You feed it a list of units with
their wargear options and get back a html page with a breakdown of the costs
and force organisation chart.  Units are output in the form of quick reference
cards that can be printed for convenience.

Input lists are expressed in YAML so that they are easy to read and write by
hand. They go in the 'lists' subdirectory.

Data for models, formations and weapons are stored in .csv files in the 'data'
subdirectory.

When you run this script, a 'docs' subdirectory will be created containing
pages for each army list in 'lists'.
"""

import shutil
import os

from cogitator.database import read_armies, Database
from cogitator.writers.army import ArmyWriter
from cogitator.writers.armyheader import ArmyHeaderWriter
from cogitator.output import Outfile


def main():

    # Make sure we're in the right place.
    directory = os.path.dirname(__file__)
    if len(directory) > 0:
        os.chdir(directory)

    # Read in the data.
    forty_k = Database("40k", "data")
    kill_team = Database("Kill Team", "data")

    # The army lists.
    armies = read_armies("lists")

    # Create / clean the directory structure.
    if not os.path.exists("docs"):
        os.mkdir("docs")
    if os.path.exists("docs/lists"):
        shutil.rmtree("docs/lists")
    if os.path.exists("docs/index.html"):
        os.remove("docs/index.html")

    # Write out each army and list it in the index file.
    os.chdir("docs")
    os.mkdir("lists")
    shutil.copytree("../lists/images", "lists/images")
    with open("index.html", "w") as f:
        outfile = Outfile(f)
        outfile.start_tag("html")
        outfile.start_tag("head")
        outfile.content("<link rel='stylesheet' type='text/css' href='./style/style.css'/>")
        outfile.end_tag()
        outfile.start_tag("body")
        outfile.content("<h1> Army Lists </h1>")
        for army in armies:
            database = kill_team if army["Game"] == "Kill Team" else forty_k
            armywriter = ArmyWriter(database)
            armyheaderwriter = ArmyHeaderWriter(database)
            variants = get_variants("lists", army)
            for variant in variants:
                filename = variant["filename"]
                sections = variant["sections"]
                assert not os.path.exists(filename)
                with open(filename, "w") as f2:
                    outfile2 = Outfile(f2)
                    armywriter.write_army(outfile2, army, sections)
            armyheaderwriter.write_army_header(outfile, army, variants)
        outfile.end_tag() # body
        outfile.end_tag() # html


def get_variants(out_dir, army):
    """
    Get the variants of an army list to write.
    :param out_dir: Location of output files.
    :param army: Army definition
    :return: List of variant maps.
    """
    variants = [
        {
            "name": "full",
            "filename": os.path.join(out_dir, army["Basename"] + ".html"),
            "sections": []
        },
        {
            "name": "cards",
            "filename": os.path.join(out_dir,
                                     army["Basename"] + "_cards.html"),
            "sections": ["units"]
        },
        {
            "name": "appendices",
            "filename": os.path.join(out_dir,
                                     army["Basename"] + "_appendices.html"),
            "sections": ["header", "appendices"]
        }
    ]
    return variants


if __name__ == '__main__':
    main()
