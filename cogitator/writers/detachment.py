"""
Write a detachment.
"""

from cogitator.writers.squad import SquadWriter
from cogitator.writers.forceorg import ForceOrgWriter


class DetachmentWriter(object):

    def __init__(self, database):
        self.database = database

    def write_detachment(self, outfile, detachment):
        """ Write a detachment. """

        # Write out the table of force organisation slots
        if not self.database.is_kill_team:
            writer = ForceOrgWriter(self.database)
            writer.write_force_organisation_chart(outfile, detachment)

        # Write out each squad.
        outfile.start_tag("div", "class='detachment'")
        if self.database.is_kill_team:
            outfile.start_tag("div", "class='cards'")
        for squad in detachment["Units"]:
            writer = SquadWriter(self.database)
            writer.write_squad(outfile, squad)
        if self.database.is_kill_team:
            outfile.end_tag()
        outfile.end_tag()  # div