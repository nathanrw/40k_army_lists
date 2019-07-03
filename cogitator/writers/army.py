"""
Write an army.
"""

from cogitator.writers.armyheader import ArmyHeaderWriter
from cogitator.writers.detachment import DetachmentWriter
from cogitator.writers.killteamlist import KillTeamListWriter
from cogitator.writers.modelstable import ModelsTableWriter
from cogitator.writers.wargeartable import WargearTableWriter
from cogitator.writers.weaponstable import WeaponsTableWriter
from cogitator.writers.abilitiestable import AbilitiesTableWriter


class ArmyWriter(object):

    def __init__(self, database):
        self.database = database

    def write_army(self, outfile, army, sections=[]):
        """ Write the HTML for an army to a stream. """

        # Start of HTML file.
        outfile.start_tag("html")
        outfile.start_tag("head")
        outfile.content(
            "<link rel='stylesheet' type='text/css' href='../style/style.css'/>")
        outfile.end_tag()  # head
        outfile.start_tag("body")

        # Output totals and army info.
        if len(sections) == 0 or "header" in sections:
            writer = ArmyHeaderWriter(self.database)
            writer.write_army_header(outfile, army)

        # Output breakdown for each detachment.
        if len(sections) == 0 or "units" in sections:
            outfile.comment("Army list")
            outfile.start_tag("div", "class='army'")
            for detachment in army["Detachments"]:
                writer = DetachmentWriter(self.database)
                writer.write_detachment(outfile, detachment)
            outfile.end_tag()  # div

        # Write out stat tables for all weapons and models in army.
        if len(sections) == 0 or "appendices" in sections:
            outfile.comment("Appendices")
            if self.database.is_kill_team:
                writer = KillTeamListWriter(self.database)
                writer.write_kill_team_list(outfile, army)
            modelstable = ModelsTableWriter(self.database)
            wargeartable = WargearTableWriter(self.database)
            weaponstable = WeaponsTableWriter(self.database)
            abilitiestable = AbilitiesTableWriter(self.database)
            modelstable.write_models_table(outfile, self.database.list_army_models(army))
            wargeartable.write_wargear_table(outfile, self.database.list_army_wargear(army))
            weaponstable.write_weapons_table(outfile, self.database.list_army_weapons(army))
            abilitiestable.write_abilities_table(outfile, self.database.list_army_abilities(army))

        # End of HTML file.
        outfile.end_tag()  # body
        outfile.end_tag()  # html