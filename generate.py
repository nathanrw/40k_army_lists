#!/bin/env python

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
    try:
        return COSTS[item]
    except KeyError:
        print ("No item '%s' in item table." % item)
        sys.exit(1)

def lookup_formation(formation):
    try:
        return FORMATIONS[formation]
    except KeyError:
        print ("No formation '%s' in formations table." % formation)

def write_army_file(out_dir, army):
    basename = army["Name"] + ".html"
    filename = os.path.join(out_dir, basename)
    with open(filename, "w") as outfile:
        outfile.write("<html>\n")
        outfile.write("<body>\n")
        army_name = army["Name"]
        limit = army["Points"]
        warlord = army["Warlord"]
        outfile.write("<h1>%s</h1>\n" % army_name)
        outfile.write("<ul>\n")
        outfile.write("<li>Warlord: %s</li>\n" % warlord)
        outfile.write("<li>Points limit: %s</li>\n" % limit)
        outfile.write("</ul>\n")
        total = 0
        cp_total = 0
        for detachment in army["Detachments"]:

            # Get the formation info and update cp count.
            formation = lookup_formation(detachment["Type"])
            cp = formation.cp
            cp_total += cp

            # Write out the detachment title.
            title = "%s (%s) (%sCP)" % (detachment["Name"], detachment["Type"], cp)
            outfile.write("<h2>%s</h2>\n" % title)

            # Write out the table of force organisation slots
            outfile.write("<table>\n")
            outfile.write("<tr>\n")
            for slot in formation.slots:
                outfile.write("<td>%s</td>\n" % slot)
            outfile.write("<td>Transports</td>\n")
            outfile.write("</tr>\n")
            outfile.write("<tr>\n")
            for slot in formation.slots:
                min, max = formation.slots[slot]
                count = 0
                for squad in detachment["Units"]:
                    if squad["Slot"] == slot:
                        count += 1
                outfile.write("<td>%s/%s</td>\n" % (count, max))
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

            # Write out each squad.
            for squad in detachment["Units"]:
                squad_total = 0
                name = squad["Name"]
                for item in squad["Items"].keys():
                    squad_total += lookup_item(item).cost * squad["Items"][item]
                outfile.write("<h3>%s [%s] (%spts)</h3>\n" % (name, squad["Slot"], squad_total))
                outfile.write("<ul>\n")
                for item in squad["Items"]:
                    outfile.write("<li>%s (%sx%spts)</li>\n" % (item, squad["Items"][item], lookup_item(item).cost))
                outfile.write("</ul>\n")
                total += squad_total
                outfile.write("\n")
        outfile.write("<h2>Totals</h2>\n")
        outfile.write("<ul>\n")
        outfile.write("<li>Total Points: %s -> %s to spare</li>\n" % (total, limit-total))
        outfile.write("<li>Total CP: %s</li>\n" % cp_total)
        outfile.write("</ul>\n")
        outfile.write("</body>\n")
        outfile.write("</html>\n")
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

    # Write out each army.
    with open("index.html", "w") as outfile:
        outfile.write("<html>\n")
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
