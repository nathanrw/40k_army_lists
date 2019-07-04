"""
Functions for reading data from tables.
"""

import csv
import collections
import os
import re
import sys
import yaml


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


def read_backgrounds(filename):
    backgrounds = collections.OrderedDict()
    class Background(object):
        def __init__(self, row):
            self.name = row["Name"]
    with open(filename) as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            backgrounds[row["Name"]] = Background(row)
    return backgrounds


def read_quirks(filename):
    quirks = collections.OrderedDict()
    class Quirk(object):
        def __init__(self, row):
            self.name = row["Name"]
    with open(filename) as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            quirks[row["Name"]] = Quirk(row)
    return quirks


def read_demeanours(filename):
    demeanours = collections.OrderedDict()
    class Demeanour(object):
        def __init__(self, row):
            self.name = row["Name"]
    with open(filename) as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            demeanours[row["Name"]] = Demeanour(row)
    return demeanours


def read_armies(dirname):
    """ Read the army data into dicts. """
    armies = []
    for filename in os.listdir(dirname):
        if not filename.lower().endswith(".yaml"): continue
        with open(os.path.join(dirname, filename), "r") as infile:
            army = yaml.load(infile)
            army["Basename"] = os.path.splitext(filename)[0]
            armies.append(army)
    return armies


class Database(object):
    def __init__(self, game, data_dir):
        self.__game = game
        data_dir = os.path.join(data_dir, game.lower().replace(" ", "-"))
        self.__weapons = read_weapons(os.path.join(data_dir, "weapons.csv"))
        self.__wargear = read_wargear(os.path.join(data_dir, "wargear.csv"))
        self.__models = read_models(os.path.join(data_dir, "models.csv"))
        self.__formations = read_formations(
            os.path.join(data_dir, "formations.csv"))
        self.__abilities = read_abilities(
            os.path.join(data_dir, "abilities.csv"))
        self.__psykers = read_psykers(os.path.join(data_dir, "psykers.csv"))
        self.__demeanours = {}
        self.__backgrounds = {}
        self.__quirks = {}
        if self.is_kill_team:
            self.__demeanours = read_demeanours(
                os.path.join(data_dir, "demeanours.csv"))
            self.__quirks = read_quirks(os.path.join(data_dir, "quirks.csv"))
            self.__backgrounds = read_backgrounds(
                os.path.join(data_dir, "backgrounds.csv"))
        self.__costs = {}
        self.__costs.update(self.__weapons)
        self.__costs.update(self.__models)
        self.__costs.update(self.__wargear)

    @property
    def is_kill_team(self):
        return self.__game == "Kill Team"

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

    def lookup_psyker(self, model_name, **kwargs):
        """ If a model is a psyker lookup its psychic powers. """
        quiet = kwargs.get("quiet", False)
        try:
            return self.__psykers[model_name]
        except KeyError:
            if not quiet:
                print ("Model '%s' is not a psyker." % model_name)

    def lookup_quirk(self, name):
        """ Lookup a quirk. """
        try:
            return self.__quirks[name]
        except KeyError:
            print ("Unknown quirk '%s'" % name)

    def lookup_background(self, name):
        """ Lookup a background. """
        try:
            return self.__backgrounds[name]
        except KeyError:
            print ("Unknown background '%s'" % name)

    def lookup_demeanour(self, name):
        """ Lookup a demeanour. """
        try:
            return self.__demeanours[name]
        except KeyError:
            print ("Unknown demeanour '%s'" % name)

    def lookup_buff(self, squad, stat_name, item):
        """ Lookup a buff for a stat. """
        if squad is None:
            return None
        if self.is_kill_team:
            abilities = self.list_squad_abilities(squad)
            if stat_name == "Range" and (
                    item.name == "Frag Grenade" or item.name == "Krak Grenade"):
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

    def army_cp_total(self, army):
        """ Calculate the total command points available to an army. """
        total = 3  # assume battle-forged
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

    def get_squad_level(self, squad):
        xp = squad.get("Experience", 0)
        if xp >= 12: return 3
        if xp >= 7: return 2
        if xp >= 3: return 1
        return 0

    def list_squad_abilities(self, squad):
        """ List each ability in a squad. """
        abilities = []
        for item in squad["Items"]:
            for ability in self.lookup_item(item).abilities:
                if not ability in abilities:
                    abilities.append(ability)
        if "Specialist" in squad and self.is_kill_team:
            specialist = squad["Specialist"]
            level = self.get_squad_level(squad)
            for i in range(1, level + 1):
                abilities.append("%s (%s)" % (specialist, i))
        return abilities