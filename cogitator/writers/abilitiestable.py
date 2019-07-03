"""
Table of abilities.
"""


class AbilitiesTableWriter(object):

    def __init__(self, database):
        self.database = database

    def write_abilities_table(self, outfile, abilities, squad=None):
        # Write out the list of abilities.
        if len(abilities) == 0:
            return
        outfile.comment("Abilities")
        outfile.start_tag("table")
        outfile.content("<tr><th class='title' colspan='2'>Abilities</th></tr>")
        for ability in sorted(abilities):
            outfile.content(
                "<tr><td class='stat-left'><span class='ability_tag'>%s: </span> %s</td></tr>" % (
                ability, self.database.lookup_ability(ability).description))
        outfile.end_tag()  # table