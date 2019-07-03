"""
Write an army header, with optional links to files.
"""


class ArmyHeaderWriter(object):

    def __init__(self, database):
        self.database = database

    def write_army_header(self, outfile, army, variants=None):
        """ Write the army header. """
        army_name = army["Name"]
        outfile.comment(army_name)
        if variants is not None:
            army_name += " ("
            for variant in variants:
                army_name += " <a href='%s'>%s</a>" % (
                variant["filename"], variant["name"])
            army_name += ")"
        limit = army["Points"]
        total = self.database.army_points_cost(army)
        cp_total = self.database.army_cp_total(army)
        warlord = army["Warlord"]
        outfile.start_tag("div", "class='army_header'")
        outfile.start_tag("table", "class='army_table'")
        outfile.content(
            "<tr><th colspan='2' class='title'>%s</th></tr>" % army_name)
        outfile.content("<tr><th>Warlord</th><td>%s</td></tr>" % warlord)
        outfile.content("<tr><th>Points limit</th><td>%s</td></tr>" % limit)
        outfile.content("<tr><th>Points total</th><td>%s</td></tr>" % total)
        outfile.content(
            "<tr><th>Points to spare</th><td>%s</td></tr>" % (limit - total))
        outfile.content("<tr><th>CP</td><td>%s</th></tr>" % cp_total)
        outfile.end_tag()  # table
        if not self.database.is_kill_team:
            outfile.start_tag("table")
            outfile.start_tag("tr")
            outfile.content("<th class='title'>Detachment</th>")
            outfile.content("<th class='title'>Type</th>")
            outfile.content("<th class='title'>CP</th>")
            outfile.content("<th class='title'>Cost</th>")
            outfile.end_tag()  # tr
            for detachment in army["Detachments"]:
                outfile.start_tag("tr")
                outfile.content("<td colspan='1'>%s</td>" % detachment["Name"])
                outfile.content("<td colspan='1'>%s</td>" % detachment["Type"])
                outfile.content(
                    "<td colspan='1'>%s</td>" % self.database.lookup_formation(
                        detachment["Type"]).cp)
                outfile.content(
                    "<td colspan='1'>%s</td>" % self.database.detachment_points_cost(
                        detachment))
                outfile.end_tag()  # tr
            outfile.end_tag()  # table
        else:
            kt = army["Detachments"][0] if len(army["Detachments"]) > 0 else {}
            outfile.start_tag("table")
            outfile.start_tag("tr")
            outfile.content("<th class='title'>Background</th>")
            outfile.content("<th class='title'>Quirk</th>")
            outfile.end_tag()  # tr
            outfile.start_tag("tr")
            outfile.content(
                "<td colspan='1'>%s</td>" % kt.get("Background", "None"))
            outfile.content("<td colspan='1'>%s</td>" % kt.get("Quirk", "None"))
            outfile.end_tag()  # tr
            outfile.end_tag()  # table
        outfile.end_tag()  # div