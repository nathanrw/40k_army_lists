#!/bin/env python

import sys
import csv
import shutil
import os

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

AL_1000PT = {
    "Name": "1000pt Army",
    "Warlord": "Chaplain",
    "Points": 1000,
    "Detachments": [
        {
            "Name": "Patrol",
            "Type": "Patrol",
            "Units": [
                (
                    "Tactical Squad",
                    [
                        ("Tactical Marine", 10),
                        ("Flamer", 1),
                        ("Missile Launcher", 1)
                    ]
                ),
                (
                    "Rhino",
                    [
                        ("Rhino", 1),
                        ("Storm Bolter", 2)
                    ]
                ),
                (
                    "Death Company",
                    [
                        ("Death Company (Jump Pack)", 10)
                    ]
                ),
                (
                    "Chaplain",
                    [
                        ("Chaplain (Jump Pack)", 1)
                    ]
                ),
                (
                    "Librarian",
                    [
                        ("Librarian (Terminator Armour)", 1),
                        ("Force Axe", 1),
                        ("Storm Bolter", 1)
                    ]
                ),
                (
                    "Terminators",
                    [
                        ("Terminator", 5),
                        ("Power Fist", 4),
                        ("Power Sword", 1),
                        ("Storm Bolter", 5)
                    ]
                )
            ]
        }
    ]
}


AL_1500PT = {
    "Name": "1500pt Army",
    "Warlord": "Chaplain",
    "Points": 1500,
    "Detachments": [
        {
            "Name": "1500pt patrol",
            "Type": "Patrol",
            "Units": [
                (
                    "Tactical Squad",
                    [
                        ("Tactical Marine", 10),
                        ("Flamer", 1),
                        ("Missile Launcher", 1)
                    ]
                ),
                (
                    "Rhino",
                    [
                        ("Rhino", 1),
                        ("Storm Bolter", 2)
                    ]
                ),
                (
                    "Death Company",
                    [
                        ("Death Company (Jump Pack)", 10)
                    ]
                ),
                (
                    "Chaplain",
                    [
                        ("Chaplain (Jump Pack)", 1)
                    ]
                ),
                (
                    "Librarian",
                    [
                        ("Librarian (Terminator Armour)", 1),
                        ("Force Axe", 1),
                        ("Storm Bolter", 1)
                    ]
                ),
                (
                    "Terminators",
                    [
                        ("Terminator", 10),
                        ("Power Fist", 9),
                        ("Power Sword", 1),
                        ("Storm Bolter", 10)
                    ]
                ),
                (
                    "Baal Predator",
                    [
                        ("Baal Predator", 1),
                        ("Twin Assault Cannon", 1),
                        ("Heavy Flamer", 2)
                    ]
                )
            ]
        }
    ]
}

AL_2000PT = {
    "Name": "2000pt Army",
    "Warlord": "Tycho",
    "Points": 2000,
    "Detachments": [
        {
            "Name": "Battalion",
            "Type": "Battalion",
            "Units": [
                (
                    "Tactical Squad 1",
                    [
                        ("Tactical Marine", 10),
                        ("Flamer", 1),
                        ("Missile Launcher", 1)
                    ]
                ),
                (
                    "Rhino 1",
                    [
                        ("Rhino", 1),
                        ("Storm Bolter", 2)
                    ]
                ),
                (
                    "Tactical Squad 2",
                    [
                        ("Tactical Marine", 10),
                        ("Flamer", 1),
                        ("Missile Launcher", 1)
                    ]
                ),
                (
                    "Rhino 2",
                    [
                        ("Rhino", 1),
                        ("Storm Bolter", 2)
                    ]
                ),
                (
                    "Scouts",
                    [
                        ("Scout Marine", 5),
                        ("Sniper Rifle", 2)
                    ]
                ),
                (
                    "Death Company",
                    [
                        ("Death Company (Jump Pack)", 10)
                    ]
                ),
                (
                    "Chaplain",
                    [
                        ("Chaplain (Jump Pack)", 1)
                    ]
                ),
                (
                    "Librarian",
                    [
                        ("Librarian (Terminator Armour)", 1),
                        ("Force Axe", 1),
                        ("Storm Bolter", 1)
                    ]
                ),
                (
                    "Tycho",
                    [
                        ("Captain Tycho", 1)
                    ]
                ),
                (
                    "Terminators",
                    [
                        ("Terminator", 10),
                        ("Power Fist", 9),
                        ("Power Sword", 1),
                        ("Storm Bolter", 10)
                    ]
                ),
                (
                    "Furioso Dreadnaught",
                    [
                        ("Furioso Dreadnaught", 1),
                        ("Furioso Fist (Pair)", 1),
                        ("Meltagun", 1),
                        ("Storm Bolter", 1)
                    ]
                ),
                (
                    "Baal Predator",
                    [
                        ("Baal Predator", 1),
                        ("Twin Assault Cannon", 1),
                        ("Heavy Flamer", 2)
                    ]
                )
            ]
        }
    ]
}

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
                name = squad[0]
                for item in squad[1]:
                    squad_total += lookup_cost(item[0]) * item[1]
                outfile.write("%s (%spts)\n" % (name, squad_total))
                for item in squad[1]:
                    outfile.write("  %s (%sx%spts)\n" % (item[0], item[1], lookup_cost(item[0])))
                total += squad_total
                outfile.write("\n")
        outfile.write("Totals\n")
        outfile.write("------\n")
        outfile.write("Total points: %s -> %s to spare\n" % (total, limit-total))
        outfile.write("Total CP: %s\n" % cp_total)
        outfile.write("\n")
    return filename

def main():

    # The army lists.
    armies = [AL_1000PT, AL_1500PT, AL_2000PT]

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
