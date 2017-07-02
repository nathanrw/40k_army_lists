#!/bin/env python

import sys

COSTS = {
    "Tactical Marine": 13,
    "Flamer": 9,
    "Missile Launcher": 25,
    "Rhino": 70,
    "Storm Bolter": 2,
    "Death Company (Jump Pack)": 20,
    "Librarian (Terminator Armour)": 145,
    "Chaplain (Jump Pack)": 90,
    "Force Axe": 16,
    "Terminator": 26,
    "Power Sword": 4,
    "Power Fist": 20,
    "Baal Predator": 107,
    "Twin Assault Cannon": 35,
    "Heavy Flamer": 17,
    "Furioso Dreadnaught": 122,
    "Furioso Fist (Single)": 40,
    "Furioso Fist (Pair)": 50,
    "Meltagun": 17,
    "Death Company Dreadnought": 128,
    "Scout Marine": 11,
    "Captain Tycho": 95,
    "Sniper Rifle": 4
}

FORMATIONS = {
    "Patrol": {
        "CP": 0
    },
    "Battalion": {
        "CP": 3
    }
}

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
        return COSTS[item]
    except KeyError:
        print "No cost for '%s' in cost table." % item
        sys.exit(1)

def lookup_cp(formation):
    try:
        return FORMATIONS[formation]["CP"]
    except KeyError:
        print "No formation '%s' in formations table." % formation

def main():
    armies = [AL_1000PT, AL_1500PT, AL_2000PT]
    for army in armies:
        print army["Name"]
        print "=" * len(army["Name"])
        print "Warlord:", army["Warlord"]
        limit = army["Points"]
        print "Limit:", limit
        print 
        total = 0
        cp_total = 0
        for detachment in army["Detachments"]:
            cp = lookup_cp(detachment["Type"])
            title = "%s (%s) (%sCP)" % (detachment["Name"], detachment["Type"], cp)
            print title
            print "-" * len(title)
            cp_total += cp
            for squad in detachment["Units"]:
                squad_total = 0
                name = squad[0]
                for item in squad[1]:
                    squad_total += lookup_cost(item[0]) * item[1]
                total += squad_total
        print
        print "Totals"
        print "------"
        print "Total Points:", total, "->", limit - total, "to spare."
        print "Total CP:", cp_total
        print 

if __name__ == '__main__':
    main()
