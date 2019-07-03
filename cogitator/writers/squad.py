"""
Write a squad datasheet or card.
"""

from cogitator.writers.modelstable import ModelsTableWriter
from cogitator.writers.wargeartable import WargearTableWriter
from cogitator.writers.weaponstable import WeaponsTableWriter
from cogitator.writers.abilitiestable import AbilitiesTableWriter
from cogitator.writers.psykertable import PsykerTableWriter


class SquadWriter(object):

    def __init__(self, database):
        self.database = database

    def write_squad(self, outfile, squad):
        """ Write out the cost breakdown for a squad. """

        weapons, models, wargear, num_models = self.database.get_squad_items(squad)
        abilities = self.database.list_squad_abilities(squad)

        # Start the squad.
        outfile.comment(squad["Name"])
        outfile.start_tag("div", "class='squad'")

        # Squad name and total cost.
        outfile.comment("Summary")
        outfile.start_tag("table", "class='unit_table'")
        outfile.start_tag("tr")
        name = squad["Name"]
        if self.database.is_kill_team:
            name += " (%s)" % self.database.squad_points_cost(squad)
        outfile.oneliner("th", extra="colspan='6' class='title'", content=name)
        outfile.start_tag("td", "class='squad_portrait_cell' rowspan=2")
        portrait = squad.get("Portrait", "../images/default.png")
        outfile.oneliner("img",
                         extra="class='squad_portrait' src='%s'" % portrait)
        outfile.end_tag()
        outfile.end_tag()  # tr
        if not self.database.is_kill_team:
            outfile.start_tag("tr")
            outfile.oneliner("th", content="Slot")
            outfile.oneliner("td", content=squad["Slot"])
            outfile.oneliner("th", content="Models")
            outfile.oneliner("td", content=num_models)
            outfile.oneliner("th", content="Cost")
            outfile.oneliner("td", content=self.database.squad_points_cost(squad))
            outfile.end_tag()  # tr
        notes = squad.get("Notes", "")
        demeanour = squad.get("Demeanour")
        if demeanour is not None:
            if len(notes) > 0:
                notes += " "
            notes += "(%s)" % demeanour
        if len(notes) > 0:
            outfile.content("<tr><td class='notes'>%s</td></tr>" % notes)
        outfile.end_tag()  # table

        # Write the experience gauge
        if self.database.is_kill_team:
            xp = squad.get("Experience", 0)
            outfile.start_tag("table")
            outfile.start_tag("tr")
            outfile.start_tag("th class='title_nofill'")
            outfile.content("XP")
            outfile.end_tag()  # th
            outfile.start_tag("td")
            outfile.start_tag("div", "class='experience_gauge'")
            for i in xrange(12):
                cell_class = "experience_cell"
                if i == 3 or i == 7 or i == 12:
                    cell_class += "_level"
                if xp >= i:
                    cell_class += "_checked"
                outfile.oneliner("div", extra="class='%s'" % cell_class)
            outfile.end_tag()  # div
            outfile.end_tag()  # td
            outfile.end_tag()  # tr
            outfile.end_tag()  # table

        # Write quick reference tables for the squad.
        modelwriter = ModelsTableWriter(self.database)
        wargearwriter = WargearTableWriter(self.database)
        weaponswriter = WeaponsTableWriter(self.database)
        abilitieswriter = AbilitiesTableWriter(self.database)
        modelwriter.write_models_table(outfile, models, squad)
        if not self.database.is_kill_team:
            wargearwriter.write_wargear_table(outfile, wargear, squad)
        weaponswriter.write_weapons_table(outfile, weapons, squad)
        abilitieswriter.write_abilities_table(outfile, abilities, squad)

        # If the squad contains psykers, write out their info.
        for model in models:
            writer = PsykerTableWriter(self.database)
            writer.write_psyker_table(outfile, model)

        # Add some space for mid-campaign additions to avoid the need for
        # re-printing.
        if self.database.is_kill_team:
            outfile.oneliner("div", extra="class='extra_space'")

        # Done with the squad.
        outfile.end_tag()  # div