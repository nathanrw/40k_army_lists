"""
Write a table of models.
"""

from cogitator.output import Table


class ModelsTableWriter(object):

    def __init__(self, database):
        self.database = database

    def write_models_table(self, outfile, item_names, squad=None):
        """ Write a table of models. """
        if len(item_names) == 0:
            return
        outfile.comment("Models")
        table = Table()
        table.set_table_class("models_table")
        table.set_default_column_class("stat-centre")
        stats = ["Name", "Cost", "M", "WS", "BS", "S", "T", "W", "A", "Ld",
                 "Sv"]
        for stat in stats:
            if stat == "Cost" and (
                    self.database.is_kill_team and squad is not None): continue
            table.add_column(stat)
        table.set_column_name("Name", "Model")
        if squad is not None and not self.database.is_kill_team:
            table.add_column("Qty")
        table.set_column_class("Name", "stat-left")
        table.set_column_class("Abilities", "stat-left")
        for name in sorted(item_names):
            item = self.database.lookup_item(name)
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
                table.set_cell("Qty", "-" if (first or squad is None) else
                squad["Items"][name])
                first = False
        table.write(outfile)