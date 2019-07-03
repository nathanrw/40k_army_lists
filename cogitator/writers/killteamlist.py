"""
Write a summary of kill team members with points cost breakdown.
"""


class KillTeamListWriter(object):

    def __init__(self, database):
        self.database = database

    def write_kill_team_list(self, outfile, army):
        """ Write the kill team army summary. """
        if not self.database.is_kill_team: return
        outfile.start_tag("table")
        outfile.content("<tr><th class='title' colspan=2>Army List</th></tr>")
        for detachment in army["Detachments"]:
            for squad in detachment["Units"]:
                weapons, models, wargear, num_models = self.database.get_squad_items(squad)
                assert len(models) == 1
                model = self.database.lookup_item(models[0])
                text = "%s (%spts) with " % (model.name, model.cost)
                items = [self.database.lookup_item(item_name) for item_name in
                         (weapons + wargear)]
                items_strs = ["%s (%spts)" % (item.name, item.cost) for item in
                              items]
                text += ", ".join(items_strs)
                outfile.content("<tr><td class='stat-left'><span class='ability_tag'>%s: </span> %s</td></tr>" % (squad["Name"], text))
        outfile.end_tag()