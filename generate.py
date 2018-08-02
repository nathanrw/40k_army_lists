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


def read_abilities(filename):
    """ Read all of the abilities into a table. """
    abilities = collections.OrderedDict()
    class Ability(object):
        def __init__(self, name, description):
            self.name = name
            self.description = description
    with open(filename) as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            abilities[row["Name"]] = Ability(row["Name"], row["Description"])
    return abilities


def read_models(filename):
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
            self.includes_wargear = False

    # Read in each model definition from the file.
    with open(filename) as csvfile:
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

            # Some models include the price of their wargear.
            includes_wargear = row["IncludesWargear"]
            if len(includes_wargear) != 0 and int(includes_wargear)!=0:
                model.includes_wargear = True

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


def read_psykers(filename):
    """ Read in table of models with psychic powers. """

    class Psyker(object):
        def __init__(self, name):
            self.name = name
            self.powers_per_turn = 0
            self.deny_per_turn = 0
            self.num_known_powers = 0
            self.discipline = None

    # Read in each psyker definition from the file.
    psykers = collections.OrderedDict()
    with open(filename) as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            psyker = Psyker(row["Name"])
            psyker.powers_per_turn = int(row["PowersPerTurn"])
            psyker.deny_per_turn = int(row["DenyPerTurn"])
            psyker.num_known_powers = int(row["NumKnownPowers"])
            psyker.discipline = row["Discipline"]
            psykers[row["Name"]] = psyker

    return psykers


def read_weapons(filename):
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
            self.abilities = []
        def get_modes(self):
            if len(self.modes) > 0:
                return self.modes
            else:
                return [self]

    # Read in the weapons table.
    with open(filename) as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:

            # Read in the weapon from the table row.
            name = row["Name"]
            cost = int(row["Cost"])
            weapon = Weapon(name, cost)
            stats = ["Name", "Cost", "Range", "Type", "S", "AP", "D"]
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

            # Extract the abilities
            weapon.abilities = [x.strip() for x in row["Abilities"].split("|")]
            if "" in weapon.abilities: weapon.abilities.remove("")

            # Add a string representing the abilities to the stats map.
            abilities_str = ", ".join(weapon.abilities)
            if len(abilities_str) == 0: abilities_str = "-"
            weapon.stats["Abilities"] = abilities_str

    # Phew, we're done.
    return weapons


def read_wargear(filename):
    """ Read all of the wargear into a table. """
    wargear = collections.OrderedDict()
    class Wargear(object):
        def __init__(self, row):
            self.name = row["Name"]
            self.cost = int(row["Cost"])
            self.abilities = [x.strip() for x in row["Abilities"].split("|")]
    with open(filename) as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            wargear[row["Name"]] = Wargear(row)
    return wargear


def read_formations(filename):
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
    with open(filename) as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            formations[row["Name"]] = Formation(row)
    return formations


def read_armies(dirname):
    """ Read the army data into dicts. """
    armies = []
    for filename in os.listdir(dirname):
        with open(os.path.join("lists", filename), "r") as infile:
            armies.append(yaml.load(infile))
    return armies


class GameData(object):
    def __init__(self, game):
        self.__game = game
        data_dir = os.path.join("data", game.lower().replace(" ", "-"))
        self.__weapons = read_weapons(os.path.join(data_dir, "weapons.csv")) 
        self.__wargear = read_wargear(os.path.join(data_dir, "wargear.csv"))
        self.__models = read_models(os.path.join(data_dir, "models.csv"))
        self.__formations = read_formations(os.path.join(data_dir, "formations.csv"))
        self.__abilities = read_abilities(os.path.join(data_dir, "abilities.csv"))
        self.__psykers = read_psykers(os.path.join(data_dir, "psykers.csv"))
        self.__costs = {}
        self.__costs.update(self.__weapons)
        self.__costs.update(self.__models)
        self.__costs.update(self.__wargear)
        self.__is_kill_team = self.__game == "Kill Team"

    def lookup_item(self, item):
        """ Lookup an item in the costs table. """
        try:
            return self.__costs[item]
        except KeyError:
            print ("No item '%s' in item table." % item)
            sys.exit(1)

    def lookup_formation(self, formation):
        """ Look up a formation in the formations table. """
        try:
            return self.__formations[formation]
        except KeyError:
            print ("No formation '%s' in formations table." % formation)
    
    def lookup_ability(self, ability):
        """ Look up an ability in the abilities table. """
        try:
            return self.__abilities[ability]
        except KeyError:
            print ("No ability '%s' in abilities table." % ability)
    
    def lookup_psyker(self, model_name):
        """ If a model is a psyker lookup its psychic powers. """
        try:
            return self.__psykers[model_name]
        except KeyError:
            print ("Model '%s' is not a psyker." % model_name)

    def army_points_cost(self, army):
        """ Calculate the total points cost of an army"""
        total = 0
        for detachment in army["Detachments"]:
            total += self.detachment_points_cost(detachment)
        return total
    
    def detachment_points_cost(self, detachment):
        """ Calculate the total points cost of a detachment. """
        total = 0
        for squad in detachment["Units"]:
            total += self.squad_points_cost(squad)
        return total

    def squad_models_cost(self, squad):
        """ Calculate the cost of a squad's models. """
        total = 0
        for item in squad["Items"]:
            if item in self.__models:
                quantity = squad["Items"][item]
                total += self.lookup_item(item).cost * quantity
        return total

    def squad_wargear_included(self, squad):
        """
        Figure out whether the cost of the wargear is included already
        in the cost of the models
        """
        include_wargear = False
        for item in squad["Items"]:
            if item in self.__models:
                if self.lookup_item(item).includes_wargear:
                    include_wargear = True
                else:
                    # Can't cope with some models in a squad including their
                    # wargear and some not!
                    assert not include_wargear
        return include_wargear

    def squad_wargear_cost(self, squad):
        """ Figure out the cost of a squad's wargear. """
        if self.squad_wargear_included(squad):
            return 0
        total = 0
        for item in squad["Items"]:
            if item in self.__weapons or item in self.__wargear:
                quantity = squad["Items"][item]
                total += self.lookup_item(item).cost * quantity
        return total
    
    def squad_points_cost(self, squad):
        """ Calculate the total points cost of a squad. """
        return self.squad_models_cost(squad) + self.squad_wargear_cost(squad)
    
    def army_cp_total(self, army):
        """ Calculate the total command points available to an army. """
        total = 3 # assume battle-forged
        for detachment in army["Detachments"]:
            formation = self.lookup_formation(detachment["Type"])
            total += formation.cp
        return total
    
    def list_army_weapons(self, army):
        """ List all of the weapons in the army."""
        weapons = []
        seen = set()
        for detachment in army["Detachments"]:
            for unit in detachment["Units"]:
                for item in unit["Items"]:
                    if item in self.__weapons and not item in seen:
                        seen.add(item)
                        weapons.append(item)
        return weapons

    def list_army_wargear(self, army):
        """ List all of the wargear in the army."""
        wargear = []
        seen = set()
        for detachment in army["Detachments"]:
            for unit in detachment["Units"]:
                for item in unit["Items"]:
                    if item in self.__wargear and not item in seen:
                        seen.add(item)
                        wargear.append(item)
        return wargear

    def list_army_models(self, army):
        """ List each distinct model in the army. """
        models = []
        seen = set()
        for detachment in army["Detachments"]:
            for unit in detachment["Units"]:
                for item in unit["Items"]:
                    if item in self.__models and not item in seen:
                        seen.add(item)
                        models.append(item)
        return models

    def list_army_abilities(self, army):
        """ List each distinct ability in the army. """
        abilities = []
        seen = set()
        for detachment in army["Detachments"]:
            for unit in detachment["Units"]:
                for name in unit["Items"]:
                    item = self.__costs[name]
                    for ability in item.abilities:
                        if not ability in seen:
                            seen.add(ability)
                            abilities.append(ability)
        return abilities

    def write_wargear_table(self, outfile, item_names, squad=None):
        if len(item_names) == 0:
            return
        wargear_included = squad is not None and self.squad_wargear_included(squad)
        outfile.write("<table class='weapons_table'>\n")
        outfile.write("<tr>\n")
        outfile.write("<th class='title'>Item</th>\n")
        if squad is None or not self.__is_kill_team:
	    outfile.write("<th class='title'>Cost</th>\n")
        if squad is None:
            outfile.write("<th class='title'>Abilities</th>\n")
        if squad is not None and not self.__is_kill_team:
            outfile.write("<th class='title'>Qty</th>\n")
        outfile.write("</tr>\n")
        for name in sorted(item_names):
            item = self.lookup_item(name)
            outfile.write("<tr>\n")
            outfile.write("<td>%s</td>\n" % name)
            if squad is None or not self.__is_kill_team:
                if wargear_included:
                    outfile.write("<td>-</td>\n")
                else:
                    outfile.write("<td>%s</td>\n" % item.cost)
            if squad is None:
                outfile.write("<td>%s</td>\n" % ", ".join(item.abilities))
            if squad is not None and not self.__is_kill_team:
                outfile.write("<td>%s</td>\n" % squad["Items"][name])
            outfile.write("</tr>\n")
        outfile.write("</table>\n")

    def write_weapons_table(self, outfile, item_names, squad=None):
        """ Write a table of weapons. """
        if len (item_names) == 0:
            return
        wargear_included = squad is not None and self.squad_wargear_included(squad)
        stats = ["Name", "Cost", "Range", "Type", "S", "AP", "D"]
        if squad is None:
            stats.append("Abilities")
        if self.__is_kill_team and squad is not None:
            stats.remove("Cost")
        outfile.write("<table class='weapons_table'>\n")
        outfile.write("<tr>\n")
        for stat in stats:
            if stat == "Name": stat = "Weapon"
            outfile.write("<th class='title'>%s</th>\n" % stat)
        if squad is not None and not self.__is_kill_team:
            outfile.write("<th class='title'>Qty</th>\n")
        outfile.write("</tr>\n")
        for name in sorted(item_names):
            item = self.lookup_item(name)
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
                        if stat == "Cost" and wargear_included:
                            value = "-"
                        else:
                            value = item.stats[stat]
                    outfile.write("<td>%s</td>\n" % value)
                if squad is not None and not self.__is_kill_team:
                    outfile.write("<td>%s</td>\n" % squad["Items"][name])
                outfile.write("</tr>\n")
    
            # Write out the stats for the weapon. If we've already written the
            # cost and quantity (because there are multiple modes) then we dont
            # want to do it again.
            for mode in modes:
                outfile.write("<tr>\n")
                for stat in stats:
                    value = mode.stats[stat]
                    if stat == "Cost" and (multiple_modes or wargear_included):
                        value = "-"
                    outfile.write("<td>%s</td>\n" % value)
                if squad is not None and not self.__is_kill_team:
                    value = "-"
                    if not multiple_modes:
                        value = squad["Items"][name]
                    outfile.write("<td>%s</td>\n" % value)
                outfile.write("</tr>\n")
        outfile.write("</table>\n")

    def write_models_table(self, outfile, item_names, squad=None):
        """ Write a table of models. """
        if len (item_names) == 0:
            return
        stats = ["Name", "Cost", "M", "WS", "BS", "S", "T", "W", "A", "Ld", "Sv"]
        if self.__is_kill_team and squad is not None:
            stats.remove("Cost")
        outfile.write("<table class='models_table'>\n")
        outfile.write("<tr>\n")
        for stat in stats:
            if stat == "Name": stat = "Model"
            outfile.write("<th class='title'>%s</th>\n" % stat)
        if squad is not None and not self.__is_kill_team:
            outfile.write("<th class='title'>Qty</th>\n")
        outfile.write("</tr>\n")
        for name in sorted(item_names):
            item = self.lookup_item(name)
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
                if squad is not None and not self.__is_kill_team:
                    value = "-"
                    if first:
                        value = squad["Items"][name]
                    outfile.write("<td>%s</td>\n" % value)
                outfile.write("</tr>\n")
                first = False
        outfile.write("</table>\n")

    def write_abilities_table(self, outfile, abilities, squad=None):
        # Write out the list of abilities.
        if len(abilities) == 0:
            return
        outfile.write("<table>\n")
        outfile.write("<tr>\n")
        outfile.write("<th class='title' colspan='2'>Abilities</th>\n")
        outfile.write("</tr>\n")
        for ability in sorted(abilities):
            outfile.write("<tr>\n")
            outfile.write("<td><span class='ability_tag'>%s: </span> %s</td>\n" % (ability, self.lookup_ability(ability).description))
            outfile.write("</tr>\n")
        outfile.write("</table>\n")

    def write_psyker_table(self, outfile, model_name, squad=None):
        """ Write out psyker info if necessary. """
    
        # If the model is not a psyker we don't need to write the table!
        if not model_name in self.__psykers:
            return
    
        # Get the psyker stats.
        psyker = self.lookup_psyker(model_name)
    
        # Write the table.
        outfile.write("<table>\n")
        outfile.write("<tr>\n")
        outfile.write("<th class='title'>Psyker</th>\n")
        outfile.write("</tr>\n")
        outfile.write("<tr>\n")
        outfile.write("<td>Can manifest %s and deny %s psychic powers per turn. Knows %s psychic powers from the %s discipline.</td>\n" % (psyker.powers_per_turn, psyker.deny_per_turn, psyker.num_known_powers, psyker.discipline))
        outfile.write("</tr>\n")
        outfile.write("</table>\n")

    def write_army_header(self, outfile, army, link=None):
        """ Write the army header. """
        army_name = army["Name"]
        if link is not None:
            army_name = "<a href='%s'>%s</a>" % (link, army_name)
        limit = army["Points"]
        total = self.army_points_cost(army)
        cp_total = self.army_cp_total(army)
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
        if not self.__is_kill_team:
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
                outfile.write("<td colspan='1'>%s</td>\n" % self.lookup_formation(detachment["Type"]).cp)
                outfile.write("<td colspan='1'>%s</td>\n" % self.detachment_points_cost(detachment))
                outfile.write("</tr>\n")
            outfile.write("</table>\n")
        outfile.write("</div>\n")

    def write_force_organisation_chart(self, outfile, detachment):
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
        outfile.write("<td colspan='1'>%s</td>\n" % self.lookup_formation(detachment["Type"]).cp)
        outfile.write("<th>Cost</th>\n")
        outfile.write("<td colspan='1'>%s</td>\n" % self.detachment_points_cost(detachment))
        outfile.write("</tr>\n")
        outfile.write("</table>\n")
    
        # Write the column header. Note that transports are handled as a special
        # case.
        outfile.write("<table class='detachment_table'>\n")
        outfile.write("<tr>\n")
        formation = self.lookup_formation(detachment["Type"])
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
            outfile.write("<td>%s</td>\n" % self.squad_points_cost(squad))
            outfile.write("</tr>\n")
        outfile.write("</table>\n")
    
        outfile.write("</div>\n")

    def write_detachment(self, outfile, detachment):
        """ Write a detachment. """
    
        # Write out the table of force organisation slots
        if not self.__is_kill_team:
            self.write_force_organisation_chart(outfile, detachment)
    
        # Write out each squad.
        outfile.write("<div class='detachment'>\n")
        for squad in detachment["Units"]:
            self.write_squad(outfile, squad)
        outfile.write("</div'>\n")

    def write_squad(self, outfile, squad):
        """ Write out the cost breakdown for a squad. """
    
        # Determine weapons and models used in the squad.
        weapons = []
        models = []
        wargear = []
        abilities = []
        num_models = 0
        for item in squad["Items"]:
            if item in self.__weapons and not item in weapons:
                weapons.append(item)
            elif item in self.__models and not item in models:
                models.append(item)
                num_models += squad["Items"][item]
            elif item in self.__wargear and not item in wargear:
                wargear.append(item)
            for ability in self.lookup_item(item).abilities:
                if not ability in abilities:
                    abilities.append(ability)
    
        # Start the squad.
        outfile.write("<div class='squad'>\n")
    
        # Squad name and total cost.
        outfile.write("<table class='unit_table'>\n")
        outfile.write("<tr>\n")
        name = squad["Name"]
        if self.__is_kill_team:
            name += " (%s)" % self.squad_points_cost(squad)
        outfile.write("<th colspan='6' class='title'>%s</th>\n" % name)
        outfile.write("</tr>\n")
        if not self.__is_kill_team:
            outfile.write("<tr>\n")
            outfile.write("<th>Slot</th>\n")
            outfile.write("<td>%s</td>\n" % squad["Slot"])
            outfile.write("<th>Models</th>\n")
            outfile.write("<td>%s</td>\n" % num_models)
            outfile.write("<th>Cost</th>\n")
            outfile.write("<td>%s</td>\n" % self.squad_points_cost(squad))
            outfile.write("</tr>\n")
        outfile.write("</table>\n")

        # Add notes.
        notes = squad.get("Notes")
        if notes is not None:
            outfile.write("<p class='notes'>%s</p>\n" % notes)

        # Save space by writing costs as a list.
        if self.__is_kill_team:
            assert len(models) == 1
            outfile.write("<p class='inline_costs'>\n")
            model = self.lookup_item(models[0])
            text = "%s (%spts) with " % (model.name, model.cost)
            items = [self.lookup_item(item_name) for item_name in (weapons + wargear)]
            items_strs = ["%s (%spts)" % (item.name, item.cost) for item in items]
            text += ", ".join(items_strs)
            outfile.write(text + "\n")
            outfile.write("</p>\n")
            
        # Write quick reference tables for the squad.
        self.write_models_table(outfile, models, squad)
        if not self.__is_kill_team:
            self.write_wargear_table(outfile, wargear, squad)
        self.write_weapons_table(outfile, weapons, squad)
        self.write_abilities_table(outfile, abilities, squad)
    
        # If the squad contains psykers, write out their info.
        for model in models:
            self.write_psyker_table(outfile, model, squad)
    
        # Done with the squad.
        outfile.write("</div>\n")

    def write_army(self, outfile, army):
        """ Write the HTML for an army to a stream. """
    
        # Start of HTML file.
        outfile.write("<html>\n")
        outfile.write("<head>\n")
        outfile.write("<link rel='stylesheet' type='text/css' href='../style.css'/>\n")
        outfile.write("</head>\n")
        outfile.write("<body>\n")
    
        # Output totals and army info.
        self.write_army_header(outfile, army)
    
        # Output breakdown for each detachment.
        outfile.write("<div class='army'>\n")
        for detachment in army["Detachments"]:
            self.write_detachment(outfile, detachment)
        outfile.write("</div>\n")
    
        # Write out stat tables for all weapons and models in army.
        self.write_models_table(outfile, self.list_army_models(army))
        self.write_wargear_table(outfile, self.list_army_wargear(army))
        self.write_weapons_table(outfile, self.list_army_weapons(army))
        self.write_abilities_table(outfile, self.list_army_abilities(army))
    
        # End of HTML file.
        outfile.write("</body>\n")
        outfile.write("</html>\n")

    def write_army_file(self, out_dir, army):
        """ Process a single army. """
    
        # Filename based on army name.
        basename = army["Name"] + ".html"
        filename = os.path.join(out_dir, basename)
    
        # File should not already exist (army name should be unique.)
        assert not os.path.isfile(filename)
    
        # Write the army.
        with open(filename, "w") as outfile:
            self.write_army(outfile, army)
    
        # Output the name of the file we wrote.
        return filename


def main():

    # Read in the data.
    forty_k = GameData("40k")
    kill_team = GameData("Kill Team")

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
            game = kill_team if army["Game"] == "Kill Team" else forty_k
            filename = game.write_army_file("lists", army)
            game.write_army_header(outfile, army, filename)
        outfile.write("</body>\n")
        outfile.write("</html>\n")

if __name__ == '__main__':
    main()
