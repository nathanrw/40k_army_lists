"""
Functions for reading data from tables.
"""

from __future__ import print_function

import csv
import collections
import os
import re
import sys
import yaml


class Record(object):
    """
    A record that can parse itself from a row and add itself to a table.
    """

    def __init__(self):
        pass

    def parse(self, row, table):
        """
        This should read data from the row into the record
        and add it to the table (which should be a dict-like object mapping
        record identifiers to records.)

        :param row: Row to parse from.
        :param table: Table to add to.
        """
        pass


class BasicRecord(Record):
    """
    A simple record identified by its name.
    """

    def __init__(self):
        Record.__init__(self)
        self.name = ""

    def parse(self, row, table):
        self.name = row["Name"]
        table[self.name] = self


class Ability(BasicRecord):

    def __init__(self):
        BasicRecord.__init__(self)
        self.description = ""

    def parse(self, row, table):
        BasicRecord.parse(self, row, table)
        self.description = row["Description"]


class Model(Record):
    """
    Model record.

    Models are special in that they can have a list of 'damage variant' records
    nested inside them. These have names like "Robot (10W)", where the trailing
    "(10W)" denotes a damage variant that kicks in at 10 wounds for the "Robot"
    model.

    Variants are not included in the table directly, they are accessible only
    through the base model, which must be read in first.
    """

    def __init__(self):
        Record.__init__(self)
        self.name = ""
        self.cost = 0
        self.stats = collections.OrderedDict()
        self.abilities = []
        self.damage_variants = []
        self.includes_wargear = False

    def parse(self, row, table):

        # Read name and cost.
        self.name = row["Name"]
        self.cost = int(row["Cost"])

        # Read in the model from the table row.
        stats = ["Name", "Cost", "M", "WS", "BS", "S", "T", "W", "A", "Ld",
                 "Sv"]
        for stat in stats:
            self.stats[stat] = row[stat]
        self.abilities = [x.strip() for x in row["Abilities"].split("|")]

        # Some models include the price of their wargear.
        includes_wargear = row["IncludesWargear"]
        if len(includes_wargear) != 0 and int(includes_wargear) != 0:
            self.includes_wargear = True

        # The model might actually be a damage variant of another model.  If
        # it is, then add it to the base model's list.
        pattern = "(.*)\\(([0-9]+)W\\)"
        match = re.match(pattern, self.name)
        if match:
            base_name = match.group(1).strip()
            threshold = int(match.group(2))
            table[base_name].damage_variants.append((threshold, self))
        else:
            table[self.name] = self


class Psyker(BasicRecord):

    def __init__(self):
        BasicRecord.__init__(self)
        self.powers_per_turn = 0
        self.deny_per_turn = 0
        self.num_known_powers = 0
        self.discipline = ""

    def parse(self, row, table):
        BasicRecord.parse(self, row, table)
        self.powers_per_turn = int(row["PowersPerTurn"])
        self.deny_per_turn = int(row["DenyPerTurn"])
        self.num_known_powers = int(row["NumKnownPowers"])
        self.discipline = row["Discipline"]


class Weapon(Record):
    """
    Weapon record.

    Weapons are a bit like models in that there can be a number of alternate
    profiles associated with a weapon name, but they are subtly different and a
    little more complicated.

    Assuming we encounter the weapon 'Missile Launcher [Krak]' in a row, and we
    have not yet encountered a missile launcher variant, then the following
    will end up in the table

    {
        ...,
        "Missile Launcher" : Weapon("Missile Launcher", <cost>)
    }

    and that weapon, in its 'modes' field, will have

    [
        Weapon("Missile Launcher [Krak]", <cost>)
    ]

    and that (child) weapon will have the actual weapon profile. Subsequently
    if we encounter "Missile Launcher [Frag]" in a row, nothing is added to the
    table but we lookup the "Missile Launcher" record and add a new profile to
    it:

    [
        Weapon("Missile Launcher [Krak]", <cost>),
        Weapon("Missile Launcher [Frag]", <cost>)
    ]

    On the other hand, a Weapon without multiple modes will appear in the table
    as a normal record.

    {
        "Bolt Pistol": Weapon(...),   # this is the real record
    }

    When looking up a weapon, one should always call get_modes() on it to
    ensure you're looking at the real record(s) and not a dummy base weapon.
    """

    def __init__(self, name="", cost=0):
        Record.__init__(self)
        self.name = name
        self.cost = cost
        self.stats = collections.OrderedDict()
        self.stats["Name"] = self.name
        self.stats["Cost"] = self.cost
        self.modes = []
        self.abilities = []

    def parse(self, row, table):

        # Read name and cost.
        self.name = row["Name"]
        self.cost = int(row["Cost"])

        # Read stats
        stats = ["Name", "Cost", "Range", "Type", "S", "AP", "D"]
        for stat in stats:
            self.stats[stat] = row[stat]

        # Extract the abilities
        self.abilities = [x.strip() for x in row["Abilities"].split("|")]
        if "" in self.abilities: self.abilities.remove("")

        # Add a string representing the abilities to the stats map.
        abilities_str = ", ".join(self.abilities)
        if len(abilities_str) == 0: abilities_str = "-"
        self.stats["Abilities"] = abilities_str

        # Weapons with different firing modes have the modes grouped
        # together as separate 'weapons' under a dummy base weapon entry.
        pattern = "(.*)\\[.*\\]"
        match = re.match(pattern, self.name)
        if match:
            base_name = match.group(1).strip()
            if not base_name in table:
                table[base_name] = Weapon(base_name, self.cost)
            table[base_name].modes.append(self)
        else:
            table[self.name] = self

    def get_modes(self):
        if len(self.modes) > 0:
            return self.modes
        else:
            return [self]


class Wargear(BasicRecord):

    def __init__(self):
        BasicRecord.__init__(self)
        self.cost = 0
        self.abilities = []

    def parse(self, row, table):
        BasicRecord.parse(self, row, table)
        self.cost = int(row["Cost"])
        self.abilities = [x.strip() for x in row["Abilities"].split("|")]


class Formation(BasicRecord):

    def __init__(self):
        BasicRecord.__init__(self)
        self.cp = 0
        self.slots = collections.OrderedDict()
        self.transports_ratio = ""

    def parse(self, row, table):
        BasicRecord.parse(self, row, table)
        self.cp = int(row["CP"])
        for slot in ("HQ", "Troops", "Fast Attack", "Elites", "Heavy Support"):
            min, max = row[slot].split("-")
            self.slots[slot] = (int(min), int(max))
        self.transports_ratio = row["Transports"]


class Background(BasicRecord):
    pass


class Quirk(BasicRecord):
    pass


class Demeanour(BasicRecord):
    pass


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


def read_table(data_dir, basename, create_record):
    """
    Read a table of records and return it.
    :param data_dir: Path to data directory.
    :param basename: Basename of .csv file to read.
    :param create_record: Record creation function. This should return an empty
                          record of an appropriate type for parsing a row of
                          this table.
    :return: The table of records.
    """
    filename = os.path.join(data_dir, basename+".csv")
    table = collections.OrderedDict()
    with open(filename) as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            record = create_record()
            record.parse(row, table)
    return table


class Database(object):
    def __init__(self, game, data_dir):
        self.__game = game
        data_dir = os.path.join(data_dir, game.lower().replace(" ", "-"))
        self.__weapons = read_table(data_dir, "weapons", Weapon)
        self.__wargear = read_table(data_dir, "wargear", Wargear)
        self.__models = read_table(data_dir, "models", Model)
        self.__formations = read_table(data_dir, "formations", Formation)
        self.__abilities = read_table(data_dir, "abilities", Ability)
        self.__psykers = read_table(data_dir, "psykers", Psyker)
        self.__demeanours = {}
        self.__backgrounds = {}
        self.__quirks = {}
        if self.is_kill_team:
            self.__demeanours = read_table(data_dir, "demeanours", Demeanour)
            self.__quirks = read_table(data_dir, "quirks", Quirk)
            self.__backgrounds = read_table(data_dir, "backgrounds", Background)
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