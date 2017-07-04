#!/bin/env python

"""
A warhammer 40,000 army list calculator.  You feed it a list of units with
their wargear options and get back a html page with a breakdown of the costs
and force organisation chart.

Input lists are expressed in YAML so that they are easy to read and write by
hand. They go in the 'lists' subdirectory.

Data for models, formations and weapons are stored in .csv files in the 'data'
subdirectory.

When you run this script, a 'html' subdirectory will be created containing
pages for each army list in 'lists'.
"""

import sys
import csv
import shutil
import os
import yaml
import collections

def read_models():
    """ Read all of the models into a table. """
    models = {}
    class Model(object):
        def __init__(self, name, cost):
            self.name = name
            self.cost = cost
    with open("data/models.csv") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            models[row["Name"]] = Model(row["Name"], int(row["Cost"]))
    return models

def read_weapons():
    """ Read all of the weapons into a table. """
    weapons = {}
    class Weapon(object):
        def __init__(self, name , cost):
            self.name = name
            self.cost = cost
    with open("data/weapons.csv") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            weapons[row["Name"]] = Weapon(row["Name"], int(row["Cost"]))
    return weapons

def read_formations():
    """ Read all of the formations into a table. """
    formations = {}
    class Formation(object):
        def __init__(self, row):
            self.name = row["Name"]
            self.cp = int(row["CP"])
            self.slots = collections.OrderedDict()
            for slot in ("HQ", "Troops", "Fast Attack", "Elites", "Heavy Support"):
                min, max = row[slot].split("-")
                self.slots[slot] = (int(min), int(max))
            self.transports_ratio = row["Transports"]
    with open("data/formations.csv") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            formations[row["Name"]] = Formation(row)
    return formations

COSTS = {}
COSTS.update(read_models())
COSTS.update(read_weapons())

FORMATIONS = read_formations()

def lookup_item(item):
    """ Lookup an item in the costs table. """
    try:
        return COSTS[item]
    except KeyError:
        print ("No item '%s' in item table." % item)
        sys.exit(1)

def lookup_formation(formation):
    """ Look up a formation in the formations table. """
    try:
        return FORMATIONS[formation]
    except KeyError:
        print ("No formation '%s' in formations table." % formation)

def army_points_cost(army):
    """ Calculate the total points cost of an army"""
    total = 0
    for detachment in army["Detachments"]:
        total += detachment_points_cost(detachment)
    return total

def detachment_points_cost(detachment):
    """ Calculate the total points cost of a detachment. """
    total = 0
    for squad in detachment["Units"]:
        total += squad_points_cost(squad)
    return total

def squad_points_cost(squad):
    """ Calculate the total points cost of a squad. """
    total = 0
    for item in squad["Items"]:
        quantity = squad["Items"][item]
        total += lookup_item(item).cost * quantity
    return total

def army_cp_total(army):
    """ Calculate the total command points available to an army. """
    total = 0
    for detachment in army["Detachments"]:
        formation = lookup_formation(detachment["Type"])
        total += formation.cp
    return total

def write_army_header(outfile, army):
    """ Write the army header. """
    army_name = army["Name"]
    limit = army["Points"]
    total = army_points_cost(army)
    cp_total = army_cp_total(army)
    warlord = army["Warlord"]
    outfile.write("<h1>%s</h1>\n" % army_name)
    outfile.write("<table>\n")
    outfile.write("<tr><th>Warlord</th><td>%s</td></tr>\n" % warlord)
    outfile.write("<tr><th>Points limit</th><td>%s</td></tr>\n" % limit)
    outfile.write("<tr><th>Points total</th><td>%s</td></tr>\n" % total)
    outfile.write("<tr><th>Points to spare</th><td>%s</td></tr>\n" % (limit - total))
    outfile.write("<tr><th>CP</td><td>%s</th></tr>\n" % cp_total)
    outfile.write("</table>\n")

def write_force_organisation_chart(outfile, detachment):
    """ Write the force organisation chart for the detachment. """
    outfile.write("<table>\n")

    outfile.write("<tr>\n")
    outfile.write("<th colspan='6'>%s</th>\n" % detachment["Name"])
    outfile.write("</tr>\n")
    outfile.write("<tr>\n")
    outfile.write("<th>Type</th>\n")
    outfile.write("<td colspan='2'>%s</td>\n" % detachment["Type"])
    outfile.write("<th>CP</th>\n")
    outfile.write("<td colspan='2'>%s</td>\n" % lookup_formation(detachment["Type"]).cp)
    outfile.write("</tr>\n")

    # Write the column header. Note that transports are handled as a special
    # case.
    outfile.write("<tr>\n")
    formation = lookup_formation(detachment["Type"])
    for slot in formation.slots:
        outfile.write("<th>%s</th>\n" % slot)
    outfile.write("<th>Transports</th>\n")
    outfile.write("</tr>\n")

    # Write the slot totals and limits.
    outfile.write("<tr>\n")
    for slot in formation.slots:
        min, max = formation.slots[slot]
        count = 0
        for squad in detachment["Units"]:
            if squad["Slot"] == slot:
                count += 1
        outfile.write("<td>%s/%s</td>\n" % (count, max))

    # Again handle transports as a special case since their limit depends
    # on everything else.
    assert formation.transports_ratio == "1:1"
    transport_count = 0
    transport_limit = 0
    for squad in detachment["Units"]:
        if squad["Slot"] == "Transports":
            transport_count += 1
        else:
            transport_limit += 1
    outfile.write("<td>%s/%s</td>\n" % (transport_count, transport_limit))
    outfile.write("</tr>\n")
    outfile.write("</table>\n")

def write_detachment(outfile, detachment):
    """ Write a detachment. """

    # Get the formation info and update cp count.
    formation = lookup_formation(detachment["Type"])
    cp = formation.cp

    # Write out the detachment title.
    title = "%s (%s) (%sCP)" % (detachment["Name"], detachment["Type"], cp)
    outfile.write("<h2>%s</h2>\n" % title)

    # Write out the table of force organisation slots
    write_force_organisation_chart(outfile, detachment)

    # Write out each squad.
    for squad in detachment["Units"]:
        write_squad(outfile, squad)

def write_squad(outfile, squad):
    """ Write out the cost breakdown for a squad. """

    # Squad name and total cost.
    squad_total = squad_points_cost(squad)
    name = squad["Name"]
    outfile.write("<h3>%s [%s] (%spts)</h3>\n" %
                  (name, squad["Slot"], squad_total))

    # List each item with cost and quantity.
    outfile.write("<ul>\n")
    for item in squad["Items"]:
        quantity = squad["Items"][item]
        cost = lookup_item(item).cost
        outfile.write("<li>%s (%sx%spts)</li>\n" %
                      (item, quantity, cost))
    outfile.write("</ul>\n")

def write_army_file(out_dir, army):
    """ Process a single army. """

    # Filename based on army name.
    basename = army["Name"] + ".html"
    filename = os.path.join(out_dir, basename)

    # File should not already exist (army name should be unique.)
    assert not os.path.isfile(filename)

    # Write the army.
    with open(filename, "w") as outfile:

        # Start of HTML file.
        outfile.write("<html>\n")
        outfile.write("<head>\n")
        outfile.write("<link rel='stylesheet' type='text/css' href='../style.css'/>")
        outfile.write("</head>\n")
        outfile.write("<body>\n")

        # Output totals and army info.
        write_army_header(outfile, army)

        # Output breakdown for each detachment.
        for detachment in army["Detachments"]:
            write_detachment(outfile, detachment)

        # End of HTML file.
        outfile.write("</body>\n")
        outfile.write("</html>\n")

    # Output the name of the file we wrote.
    return filename

def read_armies(dirname):
    """ Read the army data into dicts. """
    armies = []
    for filename in os.listdir(dirname):
        with open(os.path.join("lists", filename), "r") as infile:
            armies.append(yaml.load(infile))
    return armies

def main():

    # The army lists.
    armies = read_armies("lists")

    # Create the necessary directory structure.
    shutil.rmtree("html", True)
    os.mkdir("html")
    os.chdir("html")
    os.mkdir("lists")
    shutil.copy("../style/style.css", "style.css")

    # Write out each army and list it in the index file.
    with open("index.html", "w") as outfile:
        outfile.write("<html>\n")
        outfile.write("<head>\n")
        outfile.write("<link rel='stylesheet' type='text/css' href='style.css'/>")
        outfile.write("</head>\n")
        outfile.write("<body>\n")
        outfile.write("<h1> Army Lists </h1>\n")
        outfile.write("<ul>\n")
        for army in armies:
            filename = write_army_file("lists", army)
            outfile.write("<li><a href=\"%s\">%s</a></li>\n" % (filename, army["Name"]))
        outfile.write("</ul>\n")
        outfile.write("</body>\n")
        outfile.write("</html>\n")

if __name__ == '__main__':
    main()
