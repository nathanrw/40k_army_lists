"""
Write a force organisation chart for a detachment.
"""


class ForceOrgWriter(object):
    
    def __init__(self, database):
        self.database = database

    def write_force_organisation_chart(self, outfile, detachment):
        """ Write the force organisation chart for the detachment. """

        outfile.start_tag("div", "class='detachment_header'")

        outfile.comment(detachment["Name"])
        outfile.start_tag("table", "class='detachment_table'")
        outfile.start_tag("tr")
        outfile.oneliner("th", extra="colspan='6' class='title'",
                         content=detachment["Name"])
        outfile.end_tag()  # tr
        outfile.start_tag("tr")
        outfile.oneliner("th", content="Type")
        outfile.oneliner("td", extra="colspan='1'", content=detachment["Type"])
        outfile.oneliner("th", content="CP")
        outfile.oneliner("td", extra="colspan='1'",
                         content=self.database.lookup_formation(
                             detachment["Type"]).cp)
        outfile.oneliner("th", content="Cost")
        outfile.oneliner("td", extra="colspan='1'",
                         content=self.database.detachment_points_cost(detachment))
        outfile.end_tag()  # tr
        outfile.end_tag()  # table

        # Write the column header. Note that transports are handled as a special
        # case.
        outfile.comment("Formation")
        outfile.start_tag("table", "class='detachment_table'")
        outfile.start_tag("tr")
        formation = self.database.lookup_formation(detachment["Type"])
        for slot in formation.slots:
            outfile.oneliner("th", extra="class='title'", content=slot)
        outfile.oneliner("th", extra="class='title'", content="Transports")
        outfile.end_tag()  # tr

        # Write the slot totals and limits.
        outfile.start_tag("tr")
        for slot in formation.slots:
            min, max = formation.slots[slot]
            count = 0
            for squad in detachment["Units"]:
                if squad["Slot"] == slot:
                    count += 1
            outfile.oneliner("td", content="%s/%s" % (count, max))

        # Again handle transports as a special case since their limit depends
        # on everything else.
        assert formation.transports_ratio == "1:1"
        transport_count = 0
        transport_limit = 0
        for squad in detachment["Units"]:
            if squad["Slot"] == "Transports":
                transport_count += 1
            else:
                transport_limit += 1
        outfile.oneliner("td",
                         content="%s/%s" % (transport_count, transport_limit))
        outfile.end_tag()  # tr
        outfile.end_tag()  # table

        # Write a summary of all units in detachment.
        outfile.comment("Unit summary")
        outfile.start_tag("table")
        outfile.start_tag("tr")
        outfile.oneliner("th", extra="class='title'", content="Unit")
        outfile.oneliner("th", extra="class='title'", content="Slot")
        outfile.oneliner("th", extra="class='title'", content="Cost")
        outfile.end_tag()  # tr
        for squad in detachment["Units"]:
            outfile.start_tag("tr")
            outfile.oneliner("td", content=squad["Name"])
            outfile.oneliner("td", content=squad["Slot"])
            outfile.oneliner("td", content=self.database.squad_points_cost(squad))
            outfile.end_tag()  # tr
        outfile.end_tag()  # table

        outfile.end_tag()  # div