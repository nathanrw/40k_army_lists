"""
Write a table of wargear.
"""

from cogitator.output import Table


class WargearTableWriter(object):

    def __init__(self, database):
        self.database = database

    def write_wargear_table(self, outfile, item_names, squad=None):
        if len(item_names) == 0:
            return
        outfile.comment("Wargear")
        table = Table()
        table.set_table_class("weapons_table")
        table.set_default_column_class("stat-centre")
        table.add_column("Item")
        wargear_included = squad is not None and self.database.squad_wargear_included(
            squad)
        if squad is None or not self.database.is_kill_team and not wargear_included:
            table.add_column("Cost")
        if squad is None:
            table.add_column("Abilities")
        if squad is not None and not self.database.is_kill_team:
            table.add_column("Qty")
        table.set_column_class("Item", "stat-left")
        table.set_column_class("Abilities", "stat-left")
        for name in sorted(item_names):
            item = self.database.lookup_item(name)
            table.add_row()
            table.set_cell("Item", name)
            table.set_cell("Cost", item.cost)
            table.set_cell("Abilities", ", ".join(item.abilities))
            table.set_cell("Qty",
                           "-" if squad is None else squad["Items"][name])
        table.write(outfile)