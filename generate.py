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

import sys
import csv
import shutil
import os
import yaml
import collections
import re

def read_abilities():
    """ Read all of the abilities into a table. """
    abilities = collections.OrderedDict()
    class Ability(object):
        def __init__(self, name, description):
            self.name = name
            self.description = description
    with open("data/abilities.csv") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            abilities[row["Name"]] = Ability(row["Name"], row["Description"])
    return abilities

def read_models():
    """ Read all of the models into a table. """

    # Store models in 'document order'.
    models = collections.OrderedDict()

    # Represents a model.
    class Model(object):
        def __init__(self, name, cost):
            self.name = name
            self.cost = cost
            self.stats = collections.OrderedDict()
            self.abilities = []
            self.damage_variants = []

    # Read in each model definition from the file.
    with open("data/models.csv") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:

            # Read in the model from the table row.
            name = row["Name"]
            cost = int(row["Cost"])
            model = Model(name, cost)
            stats = ["Name", "Cost", "M", "WS", "BS", "S", "T", "W", "A", "Ld", "Sv"]
            for stat in stats:
                model.stats[stat] = row[stat]
            model.abilities = [x.strip() for x in row["Abilities"].split("|")]

            # The model might actually be a damage variant of another model.  If
            # it is, then add it to the base model's list.
            pattern = "(.*)\\(([0-9]+)W\\)"
            match = re.match(pattern, name)
            if match:
                base_name = match.group(1).strip()
                threshold = int(match.group(2))
                models[base_name].damage_variants.append((threshold, model))
            else:
                models[name] = model

    # Done!
    return models

def read_weapons():
    """ Read all of the weapons into a table. """

    # We want weapons in 'document order'.
    weapons = collections.OrderedDict()

    # Represents a weapon. Should always be accessed via 'modes()'.
    class Weapon(object):
        def __init__(self, name , cost):
            self.name = name
            self.cost = cost
            self.stats = collections.OrderedDict()
            self.stats["Name"] = name
            self.stats["Cost"] = cost
            self.modes = []
        def get_modes(self):
            if len(self.modes) > 0:
                return self.modes
            else:
                return [self]

    # Read in the weapons table.
    with open("data/weapons.csv") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:

            # Read in the weapon from the table row.
            name = row["Name"]
            cost = int(row["Cost"])
            weapon = Weapon(name, cost)
            stats = ["Name", "Cost", "Range", "Type", "S", "AP", "D", "Abilities"]
            for stat in stats:
                weapon.stats[stat] = row[stat]

            # Weapons with different firing modes have the modes grouped
            # together as separate 'weapons' under a dummy base weapon entry.
            pattern = "(.*)\\[.*\\]"
            match = re.match(pattern, name)
            if match:
                base_name = match.group(1).strip()
                if not base_name in weapons:
                    weapons[base_name] = Weapon(base_name, cost)
                weapons[base_name].modes.append(weapon)
            else:
                weapons[name] = weapon

    # Phew, we're done.
    return weapons

def read_formations():
    """ Read all of the formations into a table. """
    formations = collections.OrderedDict()
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

# Read in static data.
WEAPONS = read_weapons()
MODELS = read_models()
COSTS = {}
COSTS.update(WEAPONS)
COSTS.update(MODELS)
FORMATIONS = read_formations()
ABILITIES = read_abilities()

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

def lookup_ability(ability):
    """ Look up an ability in the abilities table. """
    try:
        return ABILITIES[ability]
    except KeyError:
        print ("No ability '%s' in abilities table." % ability)

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

def list_army_weapons(army):
    """ List all of the weapons in the army."""
    weapons = []
    seen = set()
    for detachment in army["Detachments"]:
        for unit in detachment["Units"]:
            for item in unit["Items"]:
                if item in WEAPONS and not item in seen:
                    seen.add(item)
                    weapons.append(item)
    return weapons

def list_army_models(army):
    """ List each distinct model in the army. """
    models = []
    seen = set()
    for detachment in army["Detachments"]:
        for unit in detachment["Units"]:
            for item in unit["Items"]:
                if item in MODELS and not item in seen:
                    seen.add(item)
                    models.append(item)
    return models

def write_weapons_table(outfile, item_names, squad=None):
    """ Write a table of weapons. """
    if len (item_names) == 0:
        return
    stats = ["Name", "Cost", "Range", "Type", "S", "AP", "D", "Abilities"]
    outfile.write("<table class='weapons_table'>\n")
    outfile.write("<tr>\n")
    for stat in stats:
        outfile.write("<th class='title'>%s</th>\n" % stat)
    if squad is not None:
        outfile.write("<th class='title'>Qty</th>\n")
    outfile.write("</tr>\n")
    for name in item_names:
        item = lookup_item(name)
        modes = item.get_modes()

        # If the item has multiple firing modes, write an extra line to display
        # the cost and quantity.
        multiple_modes = len(modes) > 1
        if multiple_modes:
            outfile.write("<tr>\n")
            for stat in stats:
                value = ""
                if stat != "Cost" and stat != "Name":
                    value = "-"
                else:
                    value = item.stats[stat]
                outfile.write("<td>%s</td>\n" % value)
            if squad is not None:
                outfile.write("<td>%s</td>\n" % squad["Items"][name])
            outfile.write("</tr>\n")

        # Write out the stats for the weapon. If we've already written the
        # cost and quantity (because there are multiple modes) then we dont
        # want to do it again.
        for mode in modes:
            outfile.write("<tr>\n")
            for stat in stats:
                value = mode.stats[stat]
                if multiple_modes and stat == "Cost":
                    value = "-"
                outfile.write("<td>%s</td>\n" % value)
            if squad is not None:
                value = "-"
                if not multiple_modes:
                    value = squad["Items"][name]
                outfile.write("<td>%s</td>\n" % value)
            outfile.write("</tr>\n")
    outfile.write("</table>\n")

def write_models_table(outfile, item_names, squad=None):
    """ Write a table of models. """
    if len (item_names) == 0:
        return
    stats = ["Name", "Cost", "M", "WS", "BS", "S", "T", "W", "A", "Ld", "Sv"]
    outfile.write("<table class='models_table'>\n")
    outfile.write("<tr>\n")
    for stat in stats:
        outfile.write("<th class='title'>%s</th>\n" % stat)
    if squad is not None:
        outfile.write("<th class='title'>Qty</th>\n")
    outfile.write("</tr>\n")
    for name in item_names:
        item = lookup_item(name)
        variants = [item]
        for (threshold, variant) in item.damage_variants:
            variants.append(variant)
        first = True
        for variant in variants:
            outfile.write("<tr>\n")
            for stat in stats:
                value = variant.stats[stat]
                if stat in ("WS", "BS", "Sv"):
                    value += "+"
                elif stat == "M":
                    value += "''"
                elif stat == "Cost" and not first:
                    value = "-"
                outfile.write("<td>%s</td>\n" % value)
            if squad is not None:
                value = "-"
                if first:
                    value = squad["Items"][name]
                outfile.write("<td>%s</td>\n" % value)
            outfile.write("</tr>\n")
            first = False
    outfile.write("</table>\n")

def write_army_header(outfile, army, link=None):
    """ Write the army header. """
    army_name = army["Name"]
    if link is not None:
        army_name = "<a href='%s'>%s</a>" % (link, army_name)
    limit = army["Points"]
    total = army_points_cost(army)
    cp_total = army_cp_total(army)
    warlord = army["Warlord"]
    outfile.write("<div class='army_header'>\n")
    outfile.write("<table class='army_table'>\n")
    outfile.write("<tr><th colspan='2' class='title'>%s</th></tr>\n" % army_name)
    outfile.write("<tr><th>Warlord</th><td>%s</td></tr>\n" % warlord)
    outfile.write("<tr><th>Points limit</th><td>%s</td></tr>\n" % limit)
    outfile.write("<tr><th>Points total</th><td>%s</td></tr>\n" % total)
    outfile.write("<tr><th>Points to spare</th><td>%s</td></tr>\n" % (limit - total))
    outfile.write("<tr><th>CP</td><td>%s</th></tr>\n" % cp_total)
    outfile.write("</table>\n")
    outfile.write("<table>\n")
    outfile.write("<tr>\n")
    outfile.write("<th class='title'>Detachment</th>\n")
    outfile.write("<th class='title'>Type</th>\n")
    outfile.write("<th class='title'>CP</th>\n")
    outfile.write("<th class='title'>Cost</th>\n")
    outfile.write("</tr>\n")
    for detachment in army["Detachments"]:
        outfile.write("<tr>\n")
        outfile.write("<td colspan='1'>%s</td>\n" % detachment["Name"])
        outfile.write("<td colspan='1'>%s</td>\n" % detachment["Type"])
        outfile.write("<td colspan='1'>%s</td>\n" % lookup_formation(detachment["Type"]).cp)
        outfile.write("<td colspan='1'>%s</td>\n" % detachment_points_cost(detachment))
        outfile.write("</tr>\n")
    outfile.write("</table>\n")
    outfile.write("</div>\n")

def write_force_organisation_chart(outfile, detachment):
    """ Write the force organisation chart for the detachment. """

    outfile.write("<div class='detachment_header'>\n")

    outfile.write("<table class='detachment_table'>\n")
    outfile.write("<tr>\n")
    outfile.write("<th colspan='6' class='title'>%s</th>\n" % detachment["Name"])
    outfile.write("</tr>\n")
    outfile.write("<tr>\n")
    outfile.write("<th>Type</th>\n")
    outfile.write("<td colspan='1'>%s</td>\n" % detachment["Type"])
    outfile.write("<th>CP</th>\n")
    outfile.write("<td colspan='1'>%s</td>\n" % lookup_formation(detachment["Type"]).cp)
    outfile.write("<th>Cost</th>\n")
    outfile.write("<td colspan='1'>%s</td>\n" % detachment_points_cost(detachment))
    outfile.write("</tr>\n")
    outfile.write("</table>\n")

    # Write the column header. Note that transports are handled as a special
    # case.
    outfile.write("<table class='detachment_table'>\n")
    outfile.write("<tr>\n")
    formation = lookup_formation(detachment["Type"])
    for slot in formation.slots:
        outfile.write("<th class='title'>%s</th>\n" % slot)
    outfile.write("<th class='title'>Transports</th>\n")
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

    # Write a summary of all units in detachment.
    outfile.write("<table>\n")
    outfile.write("<tr>\n")
    outfile.write("<th class='title'>Unit</th>\n")
    outfile.write("<th class='title'>Slot</th>\n")
    outfile.write("<th class='title'>Cost</th>\n")
    outfile.write("</tr>\n")
    for squad in detachment["Units"]:
        outfile.write("<tr>\n")
        outfile.write("<td>%s</td>\n" % squad["Name"])
        outfile.write("<td>%s</td>\n" % squad["Slot"])
        outfile.write("<td>%s</td>\n" % squad_points_cost(squad))
        outfile.write("</tr>\n")
    outfile.write("</table>\n")

    outfile.write("</div>\n")

def write_detachment(outfile, detachment):
    """ Write a detachment. """

    # Write out the table of force organisation slots
    write_force_organisation_chart(outfile, detachment)

    # Write out each squad.
    outfile.write("<div class='detachment'>\n")
    for squad in detachment["Units"]:
        write_squad(outfile, squad)
    outfile.write("</div'>\n")

def write_squad(outfile, squad):
    """ Write out the cost breakdown for a squad. """

    # Determine weapons and models used in the squad.
    weapons = []
    models = []
    abilities = []
    num_models = 0
    for item in squad["Items"]:
        if item in WEAPONS and not item in weapons:
            weapons.append(item)
        elif item in MODELS and not item in models:
            models.append(item)
            num_models += squad["Items"][item]
            for ability in lookup_item(item).abilities:
                if not ability in abilities:
                    abilities.append(ability)

    # Start the squad.
    outfile.write("<div class='squad'>\n")

    # Squad name and total cost.
    outfile.write("<table class='unit_table'>\n")
    outfile.write("<tr>\n")
    outfile.write("<th colspan='6' class='title'>%s</th>\n" % squad["Name"])
    outfile.write("</tr>\n")
    outfile.write("<tr>\n")
    outfile.write("<th>Slot</th>\n")
    outfile.write("<td>%s</td>\n" % squad["Slot"])
    outfile.write("<th>Models</th>\n")
    outfile.write("<td>%s</td>\n" % num_models)
    outfile.write("<th>Cost</th>\n")
    outfile.write("<td>%s</td>\n" % squad_points_cost(squad))
    outfile.write("</tr>\n")
    outfile.write("</table>\n")

    # Write quick reference tables for the squad.
    write_models_table(outfile, models, squad)
    write_weapons_table(outfile, weapons, squad)

    # Write out the list of abilities.
    if len(abilities) > 0:
        outfile.write("<table>\n")
        outfile.write("<tr>\n")
        outfile.write("<th class='title' colspan='2'>Abilities</th>\n")
        outfile.write("</tr>\n")
        for ability in abilities:
            outfile.write("<tr>\n")
            outfile.write("<td><span class='ability_tag'>%s: </span> %s</td>\n" % (ability, lookup_ability(ability).description))
            outfile.write("</tr>\n")
        outfile.write("</table>\n")

    # Done with the squad.
    outfile.write("</div>\n")

def write_army(outfile, army):
    """ Write the HTML for an army to a stream. """

    # Start of HTML file.
    outfile.write("<html>\n")
    outfile.write("<head>\n")
    outfile.write("<link rel='stylesheet' type='text/css' href='../style.css'/>\n")
    outfile.write("</head>\n")
    outfile.write("<body>\n")

    # Output totals and army info.
    write_army_header(outfile, army)

    # Output breakdown for each detachment.
    outfile.write("<div class='army'>\n")
    for detachment in army["Detachments"]:
        write_detachment(outfile, detachment)
    outfile.write("</div>\n")

    # Write out stat tables for all weapons and models in army. Since
    # we have those in place, I'm not sure how useful this is, so it's
    # switched off for now.
    write_appendices = False
    if write_appendices:
        write_models_table(outfile, list_army_models(army))
        write_weapons_table(outfile, list_army_weapons(army))

    # End of HTML file.
    outfile.write("</body>\n")
    outfile.write("</html>\n")

def write_army_file(out_dir, army):
    """ Process a single army. """

    # Filename based on army name.
    basename = army["Name"] + ".html"
    filename = os.path.join(out_dir, basename)

    # File should not already exist (army name should be unique.)
    assert not os.path.isfile(filename)

    # Write the army.
    with open(filename, "w") as outfile:
        write_army(outfile, army)

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
    shutil.rmtree("docs", True)
    os.mkdir("docs")
    os.chdir("docs")
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
        for army in armies:
            filename = write_army_file("lists", army)
            write_army_header(outfile, army, filename)
        outfile.write("</body>\n")
        outfile.write("</html>\n")

if __name__ == '__main__':
    main()
