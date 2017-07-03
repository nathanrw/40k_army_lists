#!/bin/env python

import sys
import csv
import shutil
import os
import yaml

def read_models():
    """ Read all of the models into a table. """
    models = {}
    class Model(object):
        def __init__(self, name, cost):
            self.name = name
            self.cost = cost
    with open("models.csv") as csvfile:
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
    with open("weapons.csv") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            weapons[row["Name"]] = Weapon(row["Name"], int(row["Cost"]))
    return weapons

def read_formations():
    """ Read all of the formations into a table. """
    formations = {}
    class Formation(object):
        def __init__(self, name , cp):
            self.name = name
            self.cp = cp
    with open("formations.csv") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            formations[row["Name"]] = Formation(row["Name"], int(row["CP"]))
    return formations

COSTS = {}
COSTS.update(read_models())
COSTS.update(read_weapons())

FORMATIONS = read_formations()

def lookup_cost(item):
    try:
        return COSTS[item].cost
    except KeyError:
        print ("No cost for '%s' in cost table." % item)
        sys.exit(1)

def lookup_cp(formation):
    try:
        return FORMATIONS[formation].cp
    except KeyError:
        print ("No formation '%s' in formations table." % formation)

def write_army_file(out_dir, army):
    basename = army["Name"] + ".txt"
    filename = os.path.join(out_dir, basename)
    with open(filename, "w") as outfile:
        army_name = army["Name"]
        limit = army["Points"]
        warlord = army["Warlord"]
        outfile.write(army_name + "\n")
        outfile.write("=" * len(army_name) + "\n")
        outfile.write("\n")
        outfile.write("Warlord: %s\n" % warlord)
        outfile.write("Points limit: %s\n" % limit)
        outfile.write("\n")
        total = 0
        cp_total = 0
        for detachment in army["Detachments"]:
            cp = lookup_cp(detachment["Type"])
            title = "%s (%s) (%sCP)" % (detachment["Name"], detachment["Type"], cp)
            outfile.write(title + "\n")
            outfile.write("-" * len(title) + "\n")
            outfile.write("\n")
            cp_total += cp
            for squad in detachment["Units"]:
                squad_total = 0
                name = squad["Name"]
                for item in squad["Items"].keys():
                    squad_total += lookup_cost(item) * squad["Items"][item]
                outfile.write("%s (%spts)\n" % (name, squad_total))
                for item in squad["Items"]:
                    outfile.write("  %s (%sx%spts)\n" % (item, squad["Items"][item], lookup_cost(item)))
                total += squad_total
                outfile.write("\n")
        outfile.write("Totals\n")
        outfile.write("------\n")
        outfile.write("Total points: %s -> %s to spare\n" % (total, limit-total))
        outfile.write("Total CP: %s\n" % cp_total)
        outfile.write("\n")
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
        for army in armies:
            filename = write_army_file("lists", army)
            outfile.write("<a href=\"%s\">%s</a><br/>\n" % (filename, army["Name"]))
        outfile.write("</body>\n")
        outfile.write("</html>\n")

if __name__ == '__main__':
    main()
