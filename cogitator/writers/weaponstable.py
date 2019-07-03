"""
Write a table of weapons.
"""

from cogitator.output import Table


class WeaponsTableWriter(object):

    def __init__(self, database):
        self.database = database

    def write_weapons_table(self, outfile, item_names, squad=None):
        """ Write a table of weapons. """
        if len(item_names) == 0:
            return
        outfile.comment("Weapons")
        wargear_included = squad is not None and self.database.squad_wargear_included(squad)
        stats = ["Name", "Cost", "Range", "Type", "S", "AP", "D", "Abilities"]

        table = Table()
        table.set_table_class("weapons_table")
        table.set_default_column_class("stat-centre")
        for stat in stats:
            if squad is not None and stat == "Abilities":
                continue
            if self.database.is_kill_team and squad is not None and stat == "Cost":
                continue
            table.add_column(stat)
        if squad is not None and not self.database.is_kill_team:
            table.add_column("Qty")
        table.set_column_name("Name", "Weapon")
        table.set_column_class("Name", "stat-left")
        table.set_column_class("Abilities", "stat-left")

        for name in sorted(item_names):
            item = self.database.lookup_item(name)
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
                table.set_cell("Qty",
                               "-" if squad is None else squad["Items"][name])

            # Write out the stats for the weapon. If we've already written the
            # cost and quantity (because there are multiple modes) then we dont
            # want to do it again.
            for mode in modes:
                table.add_row()
                for stat in stats:
                    style = None
                    value = mode.stats[stat]
                    buffed_value = self.database.lookup_buff(squad, stat, mode)
                    if buffed_value is not None:
                        value = buffed_value
                        style = "stat-buffed"
                    if stat == "Cost" and (multiple_modes or wargear_included):
                        value = "-"
                    table.set_cell(stat, value, style)
                table.set_cell("Qty",
                               "-" if (multiple_modes or squad is None) else
                               squad["Items"][name])
        table.write(outfile)