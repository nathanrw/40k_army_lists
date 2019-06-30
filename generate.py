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
        if not filename.lower().endswith(".yaml"): continue
        with open(os.path.join("lists", filename), "r") as infile:
            armies.append(yaml.load(infile))
    return armies


class Table(object):
    def __init__(self):
        self.__columns = []
        self.__indices = {}
        self.__names = {}
        self.__rows = []
        self.__styles = {}
        self.__table_class = None
        self.__default_column_class = None
        self.__cell_styles = {}
    def add_column(self, column_id):
        assert len(self.__rows) == 0
        assert not column_id in self.__indices
        self.__columns.append(column_id)
        self.__indices[column_id] = len(self.__columns)-1
        if self.__default_column_class is not None:
            self.__styles[column_id] = self.__default_column_class
    def set_default_column_class(self, column_class):
        self.__default_column_class = column_class
    def set_table_class(self, table_class):
        self.__table_class = table_class
    def set_column_name(self, column_id, column_name):
        self.__names[column_id] = column_name
    def set_column_class(self, column_id, column_class):
        self.__styles[column_id] = column_class
    def add_row(self):
        self.__rows.append(["-"] * len(self.__columns))
    def set_cell(self, column_id, text, style=None):
        if column_id in self.__indices:
            if style is not None:
                self.__cell_styles[(column_id, len(self.__rows)-1)] = style
            self.__rows[-1][self.__indices[column_id]] = text
    def write(self, outfile):
        if self.__table_class is not None:
            outfile.start_tag("table", "class='%s'" % self.__table_class)
        else:
            outfile.start_tag("table")
        outfile.start_tag("tr")
        for column_id in self.__columns:
            name = self.__names.get(column_id, column_id)
            outfile.content("<th class='title'>%s</th>" % name)
        outfile.end_tag() # tr
        for rowi, row in enumerate(self.__rows):
            outfile.start_tag("tr")
            for i, cell in enumerate(row):
                column_id = self.__columns[i]
                style = self.__styles.get(column_id, 'stat')
                style = self.__cell_styles.get((column_id, rowi), style)
                outfile.content("<td class='%s'>%s</td>" % (style, cell))
            outfile.end_tag() # tr
        outfile.end_tag() # table


class Outfile(object):
    def __init__(self, f):
        self.f = f
        self.stack = []
        self.tabsize = 4

    def pad(self):
        return " " * len(self.stack) * self.tabsize

    def write(self, *args, **kwargs):
        self.f.write(*args, **kwargs)

    def start_tag(self, tag, rest=""):
        self.write(self.pad())
        self.write("<%s %s>\n" % (tag, rest))
        self.stack.append(tag)

    def content(self, content):
        lines = content.split("\n")
        for line in lines:
            self.write(self.pad())
            self.write(line)
            self.write("\n")

    def end_tag(self):
        tag = self.stack.pop(len(self.stack)-1)
        self.write(self.pad())
        self.write("</%s>\n" % tag)

    def oneliner(self, tag, **kwargs):
        extra = kwargs.get("extra", "")
        content = kwargs.get("content", "")
        text = "<%s %s>%s</%s>" % (tag, extra, content, tag)
        self.content(text)

    def comment(self, comment):
        self.write("\n")
        self.content("<!-- %s -->" % comment)


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

    def lookup_buff(self, squad, stat_name, item):
        """ Lookup a buff for a stat. """
        if squad is None:
            return None
        if self.__is_kill_team:
            abilities = self.list_squad_abilities(squad)
            if stat_name == "Range" and (item.name == "Frag Grenade" or item.name == "Krak Grenade"):
                if "Auxiliary Grenade Launcher" in abilities:
                    return 30
        return None

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
                squad_abilities = self.list_squad_abilities(unit)
                for ability in squad_abilities:
                    if not ability in seen:
                        seen.add(ability)
                        abilities.append(ability)
        return abilities

    def list_squad_abilities(self, squad):
        """ List each ability in a squad. """
        abilities = []
        for item in squad["Items"]:
            for ability in self.lookup_item(item).abilities:
                if not ability in abilities:
                    abilities.append(ability)
        if "Specialist" in squad and self.__is_kill_team:
            specialist = squad["Specialist"]
            level = squad.get("Level", 1)
            for i in range(1, level+1):
                abilities.append("%s (%s)" % (specialist, i))
        return abilities

    def write_wargear_table(self, outfile, item_names, squad=None):
        if len(item_names) == 0:
            return
        outfile.comment("Wargear")
        table = Table()
        table.set_table_class("weapons_table")
        table.set_default_column_class("stat-centre")
        table.add_column("Item")
        wargear_included = squad is not None and self.squad_wargear_included(squad)
        if squad is None or not self.__is_kill_team and not wargear_included:
            table.add_column("Cost")
        if squad is None:
            table.add_column("Abilities")
        if squad is not None and not self.__is_kill_team:
            table.add_column("Qty")
        table.set_column_class("Item", "stat-left")
        table.set_column_class("Abilities", "stat-left")
        for name in sorted(item_names):
            item = self.lookup_item(name)
            table.add_row()
            table.set_cell("Item", name)
            table.set_cell("Cost", item.cost)
            table.set_cell("Abilities", ", ".join(item.abilities))
            table.set_cell("Qty", "-" if squad is None else squad["Items"][name])
        table.write(outfile)

    def write_weapons_table(self, outfile, item_names, squad=None):
        """ Write a table of weapons. """
        if len (item_names) == 0:
            return
        outfile.comment("Weapons")
        wargear_included = squad is not None and self.squad_wargear_included(squad)
        stats = ["Name", "Cost", "Range", "Type", "S", "AP", "D", "Abilities"]

        table = Table()
        table.set_table_class("weapons_table")
        table.set_default_column_class("stat-centre")
        for stat in stats:
            if squad is not None and stat == "Abilities": 
                continue
            if self.__is_kill_team and squad is not None and stat == "Cost": 
                continue
            table.add_column(stat)
        if squad is not None and not self.__is_kill_team:
            table.add_column("Qty")
        table.set_column_name("Name", "Weapon")
        table.set_column_class("Name", "stat-left")
        table.set_column_class("Abilities", "stat-left")

        for name in sorted(item_names):
            item = self.lookup_item(name)
            modes = item.get_modes()
    
            # If the item has multiple firing modes, write an extra line to display
            # the cost and quantity.
            multiple_modes = len(modes) > 1
            if multiple_modes:
                table.add_row()
                for stat in stats:
                    value = ""
                    if stat != "Cost" and stat != "Name":
                        value = "-"
                    else:
                        if stat == "Cost" and wargear_included:
                            value = "-"
                        else:
                            value = item.stats[stat]
                    table.set_cell(stat, value)
                table.set_cell("Qty", "-" if squad is None else squad["Items"][name])
    
            # Write out the stats for the weapon. If we've already written the
            # cost and quantity (because there are multiple modes) then we dont
            # want to do it again.
            for mode in modes:
                table.add_row()
                for stat in stats:
                    style=None
                    value = mode.stats[stat]
                    buffed_value = self.lookup_buff(squad, stat, mode)
                    if buffed_value is not None:
                        value = buffed_value
                        style = "stat-buffed"
                    if stat == "Cost" and (multiple_modes or wargear_included):
                        value = "-"
                    table.set_cell(stat, value, style)
                table.set_cell("Qty", "-" if (multiple_modes or squad is None) else squad["Items"][name])
        table.write(outfile)

    def write_models_table(self, outfile, item_names, squad=None):
        """ Write a table of models. """
        if len (item_names) == 0:
            return
        outfile.comment("Models")
        table = Table()
        table.set_table_class("models_table")
        table.set_default_column_class("stat-centre")
        stats = ["Name", "Cost", "M", "WS", "BS", "S", "T", "W", "A", "Ld", "Sv"]
        for stat in stats:
            if stat == "Cost" and (self.__is_kill_team and squad is not None): continue
            table.add_column(stat)
        table.set_column_name("Name", "Model")
        if squad is not None and not self.__is_kill_team:
            table.add_column("Qty")
        table.set_column_class("Name", "stat-left")
        table.set_column_class("Abilities", "stat-left")
        for name in sorted(item_names):
            item = self.lookup_item(name)
            variants = [item]
            for (threshold, variant) in item.damage_variants:
                variants.append(variant)
            first = True
            for variant in variants:
                table.add_row()
                for stat in stats:
                    value = variant.stats[stat]
                    if stat in ("WS", "BS", "Sv"):
                        value += "+"
                    elif stat == "M":
                        value += "''"
                    elif stat == "Cost" and not first:
                        value = "-"
                    table.set_cell(stat, value)
                table.set_cell("Qty", "-" if (first or squad is None) else squad["Items"][name])
                first = False
        table.write(outfile)

    def write_abilities_table(self, outfile, abilities, squad=None):
        # Write out the list of abilities.
        if len(abilities) == 0:
            return
        outfile.comment("Abilities")
        outfile.start_tag("table")
        outfile.content("<tr><th class='title' colspan='2'>Abilities</th></tr>")
        for ability in sorted(abilities):
            outfile.content("<tr><td class='stat-left'><span class='ability_tag'>%s: </span> %s</td></tr>" % (ability, self.lookup_ability(ability).description))
        outfile.end_tag() # table

    def write_psyker_table(self, outfile, model_name, squad=None):
        """ Write out psyker info if necessary. """
    
        # If the model is not a psyker we don't need to write the table!
        if not model_name in self.__psykers:
            return
    
        # Get the psyker stats.
        psyker = self.lookup_psyker(model_name)
    
        # Write the table.
        text = "Can manifest %s and deny %s psychic powers per turn. Knows %s psychic powers from the %s discipline." % (psyker.powers_per_turn, psyker.deny_per_turn, psyker.num_known_powers, psyker.discipline)
        table = Table()
        table.add_column("Psyker")
        table.add_row()
        table.set_cell("Psyker", text)
        outfile.comment("Psyker")
        table.write(outfile)

    def write_kill_team_list(self, outfile, army):
        """ Write the kill team army summary. """
        if not self.__is_kill_team: return
        outfile.start_tag("table")
        outfile.content("<tr><th class='title' colspan=2>Army List</th></tr>")
        for detachment in army["Detachments"]:
            for squad in detachment["Units"]:
                weapons, models, wargear, num_models = self.get_squad_items(squad)
                assert len(models) == 1
                model = self.lookup_item(models[0])
                text = "%s (%spts) with " % (model.name, model.cost)
                items = [self.lookup_item(item_name) for item_name in (weapons + wargear)]
                items_strs = ["%s (%spts)" % (item.name, item.cost) for item in items]
                text += ", ".join(items_strs)
                outfile.content("<tr><td class='stat-left'><span class='ability_tag'>%s: </span> %s</td></tr>" % (squad["Name"], text))
        outfile.end_tag()

    def write_army_header(self, outfile, army, files=None):
        """ Write the army header. """
        army_name = army["Name"]
        outfile.comment(army_name)
        if files is not None:
            army_name = "<a href='%s'>%s</a>" % (files["full"]["filename"], army_name)
        limit = army["Points"]
        total = self.army_points_cost(army)
        cp_total = self.army_cp_total(army)
        warlord = army["Warlord"]
        outfile.start_tag("div", "class='army_header'")
        outfile.start_tag("table", "class='army_table'")
        outfile.content("<tr><th colspan='2' class='title'>%s</th></tr>" % army_name)
        outfile.content("<tr><th>Warlord</th><td>%s</td></tr>" % warlord)
        outfile.content("<tr><th>Points limit</th><td>%s</td></tr>" % limit)
        outfile.content("<tr><th>Points total</th><td>%s</td></tr>" % total)
        outfile.content("<tr><th>Points to spare</th><td>%s</td></tr>" % (limit - total))
        outfile.content("<tr><th>CP</td><td>%s</th></tr>" % cp_total)
        outfile.end_tag() # table
        if not self.__is_kill_team:
            outfile.start_tag("table")
            outfile.start_tag("tr")
            outfile.content("<th class='title'>Detachment</th>")
            outfile.content("<th class='title'>Type</th>")
            outfile.content("<th class='title'>CP</th>")
            outfile.content("<th class='title'>Cost</th>")
            outfile.end_tag() # tr
            for detachment in army["Detachments"]:
                outfile.start_tag("tr")
                outfile.content("<td colspan='1'>%s</td>" % detachment["Name"])
                outfile.content("<td colspan='1'>%s</td>" % detachment["Type"])
                outfile.content("<td colspan='1'>%s</td>" % self.lookup_formation(detachment["Type"]).cp)
                outfile.content("<td colspan='1'>%s</td>" % self.detachment_points_cost(detachment))
                outfile.end_tag() # tr
            outfile.end_tag() # table
        outfile.end_tag() # div

    def write_force_organisation_chart(self, outfile, detachment):
        """ Write the force organisation chart for the detachment. """
    
        outfile.start_tag("div", "class='detachment_header'")

        outfile.comment(detachment["Name"])
        outfile.start_tag("table", "class='detachment_table'")
        outfile.start_tag("tr")
        outfile.oneliner("th", extra="colspan='6' class='title'", content=detachment["Name"])
        outfile.end_tag() # tr
        outfile.start_tag("tr")
        outfile.oneliner("th", content="Type")
        outfile.oneliner("td", extra="colspan='1'", content = detachment["Type"])
        outfile.oneliner("th", content="CP")
        outfile.oneliner("td", extra="colspan='1'", content=self.lookup_formation(detachment["Type"]).cp)
        outfile.oneliner("th", content="Cost")
        outfile.oneliner("td", extra="colspan='1'", content = self.detachment_points_cost(detachment))
        outfile.end_tag() # tr
        outfile.end_tag() # table
    
        # Write the column header. Note that transports are handled as a special
        # case.
        outfile.comment("Formation")
        outfile.start_tag("table", "class='detachment_table'")
        outfile.start_tag("tr")
        formation = self.lookup_formation(detachment["Type"])
        for slot in formation.slots:
            outfile.oneliner("th", extra="class='title'", content=slot)
        outfile.oneliner("th", extra="class='title'", content="Transports")
        outfile.end_tag() # tr
    
        # Write the slot totals and limits.
        outfile.start_tag("tr")
        for slot in formation.slots:
            min, max = formation.slots[slot]
            count = 0
            for squad in detachment["Units"]:
                if squad["Slot"] == slot:
                    count += 1
            outfile.oneliner("td", content="%s/%s" % (count, max))
    
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
        outfile.oneliner("td", content="%s/%s" % (transport_count, transport_limit))
        outfile.end_tag() # tr
        outfile.end_tag() # table
    
        # Write a summary of all units in detachment.
        outfile.comment("Unit summary")
        outfile.start_tag("table")
        outfile.start_tag("tr")
        outfile.oneliner("th", extra="class='title'", content="Unit")
        outfile.oneliner("th", extra="class='title'", content="Slot")
        outfile.oneliner("th", extra="class='title'", content="Cost")
        outfile.end_tag() # tr
        for squad in detachment["Units"]:
            outfile.start_tag("tr")
            outfile.oneliner("td", content=squad["Name"])
            outfile.oneliner("td", content=squad["Slot"])
            outfile.oneliner("td", content=self.squad_points_cost(squad))
            outfile.end_tag() # tr
        outfile.end_tag() # table
    
        outfile.end_tag() # div

    def write_detachment(self, outfile, detachment):
        """ Write a detachment. """
    
        # Write out the table of force organisation slots
        if not self.__is_kill_team:
            self.write_force_organisation_chart(outfile, detachment)
    
        # Write out each squad.
        outfile.start_tag("div", "class='detachment'")
        if self.__is_kill_team:
            outfile.start_tag("div", "class='cards'")
        for squad in detachment["Units"]:
            self.write_squad(outfile, squad)
        if self.__is_kill_team:
            outfile.end_tag()
        outfile.end_tag() # div

    def get_squad_items(self, squad):
        """ Determine weapons and models used in the squad. """
        weapons = []
        models = []
        wargear = []
        num_models = 0
        for item in squad["Items"]:
            if item in self.__weapons and not item in weapons:
                weapons.append(item)
            elif item in self.__models and not item in models:
                models.append(item)
                num_models += squad["Items"][item]
            elif item in self.__wargear and not item in wargear:
                wargear.append(item)
        return (weapons, models, wargear, num_models)

    def write_squad(self, outfile, squad):
        """ Write out the cost breakdown for a squad. """

        weapons, models, wargear, num_models = self.get_squad_items(squad)
        abilities = self.list_squad_abilities(squad)
    
        # Start the squad.
        outfile.comment(squad["Name"])
        outfile.start_tag("div", "class='squad'")
    
        # Squad name and total cost.
        outfile.comment("Summary")
        outfile.start_tag("table", "class='unit_table'")
        outfile.start_tag("tr")
        name = squad["Name"]
        if self.__is_kill_team:
            name += " (%s)" % self.squad_points_cost(squad)
        outfile.oneliner("th", extra="colspan='6' class='title'", content=name)
        outfile.start_tag("td", "class='squad_portrait_cell' rowspan=3")
        portrait = squad.get("Portrait", "../images/default.png")
        outfile.oneliner("img",
                         extra = "class='squad_portrait' src='%s'" % portrait)
        outfile.end_tag()
        outfile.end_tag() # tr
        if not self.__is_kill_team:
            outfile.start_tag("tr")
            outfile.oneliner("th", content="Slot")
            outfile.oneliner("td", content=squad["Slot"])
            outfile.oneliner("th", content="Models")
            outfile.oneliner("td", content=num_models)
            outfile.oneliner("th", content="Cost")
            outfile.oneliner("td", content=self.squad_points_cost(squad))
            outfile.end_tag() # tr
        notes = squad.get("Notes")
        if notes is not None:
            outfile.content("<tr><td class='notes'>%s</td></tr>" % notes)
        outfile.end_tag() # table
            
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
        outfile.end_tag() # div

    def write_army(self, outfile, army, sections=[]):
        """ Write the HTML for an army to a stream. """
    
        # Start of HTML file.
        outfile.start_tag("html")
        outfile.start_tag("head")
        outfile.content("<link rel='stylesheet' type='text/css' href='../style/style.css'/>")
        outfile.end_tag() # head
        outfile.start_tag("body")
    
        # Output totals and army info.
        if len(sections) == 0 or "header" in sections:
            self.write_army_header(outfile, army)
    
        # Output breakdown for each detachment.
        if len(sections) == 0 or "units" in sections:
            outfile.comment("Army list")
            outfile.start_tag("div", "class='army'")
            for detachment in army["Detachments"]:
                self.write_detachment(outfile, detachment)
            outfile.end_tag() # div
    
        # Write out stat tables for all weapons and models in army.
        if len(sections) == 0 or "appendices" in sections:
            outfile.comment("Appendices")
            if self.__is_kill_team:
                self.write_kill_team_list(outfile, army)
            self.write_models_table(outfile, self.list_army_models(army))
            self.write_wargear_table(outfile, self.list_army_wargear(army))
            self.write_weapons_table(outfile, self.list_army_weapons(army))
            self.write_abilities_table(outfile, self.list_army_abilities(army))
    
        # End of HTML file.
        outfile.end_tag() # body
        outfile.end_tag() # html

    def write_army_file(self, out_dir, army):
        """ Process a single army. """

        files = {
            "full": {
                "filename": os.path.join(out_dir, army["Name"] + ".html"),
                "sections": []
            },
            "cards": {
                "filename": os.path.join(out_dir, army["Name"] + "_cards.html"),
                "sections": ["units"]
            },
            "appendices": {
                "filename": os.path.join(out_dir, army["Name"] + "_appendices.html"),
                "sections": ["header", "appendices"]
            }
        }
    
        # Write the army.
        for name in files:
            filename = files[name]["filename"]
            sections = files[name]["sections"]
            assert not os.path.exists(filename)
            with open(filename, "w") as f:
                outfile = Outfile(f)
                self.write_army(outfile, army, sections)
    
        # Output the name of the file we wrote.
        return files


def main():

    # Read in the data.
    forty_k = GameData("40k")
    kill_team = GameData("Kill Team")

    # The army lists.
    armies = read_armies("lists")

    # Make sure we're in the right place.
    directory = os.path.dirname(__file__)
    if len(directory) > 0:
        os.chdir(directory)

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
            game = kill_team if army["Game"] == "Kill Team" else forty_k
            files = game.write_army_file("lists", army)
            game.write_army_header(outfile, army, files)
        outfile.end_tag() # body
        outfile.end_tag() # html

if __name__ == '__main__':
    main()
