"""
Write psychic powers table for a psyker.
"""

from cogitator.output import Table


class PsykerTableWriter(object):

    def __init__(self, database):
        self.database = database

    def write_psyker_table(self, outfile, model_name):
        """ Write out psyker info if necessary. """

        # If the model is not a psyker we don't need to write the table!
        if not model_name in self.database.psykers:
            return

        # Get the psyker stats.
        psyker = self.database.lookup_psyker(model_name)

        # Write the table.
        tup = (psyker.powers_per_turn, psyker.deny_per_turn,
               psyker.num_known_powers, psyker.discipline)
        text = "Can manifest %s and deny %s psychic powers per turn. Knows %s psychic powers from the %s discipline." % tup
        table = Table()
        table.add_column("Psyker")
        table.add_row()
        table.set_cell("Psyker", text)
        outfile.comment("Psyker")
        table.write(outfile)