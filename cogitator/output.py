"""
Utilities for writing html.
"""

class Table(object):
    def __init__(self):
        self.__columns = []
        self.__indices = {}
        self.__names = {}
        self.__rows = []
        self.__styles = {}
        self.__table_class = None
        self.__default_column_class = None
        self.__cell_styles = {}
    def add_column(self, column_id):
        assert len(self.__rows) == 0
        assert not column_id in self.__indices
        self.__columns.append(column_id)
        self.__indices[column_id] = len(self.__columns)-1
        if self.__default_column_class is not None:
            self.__styles[column_id] = self.__default_column_class
    def set_default_column_class(self, column_class):
        self.__default_column_class = column_class
    def set_table_class(self, table_class):
        self.__table_class = table_class
    def set_column_name(self, column_id, column_name):
        self.__names[column_id] = column_name
    def set_column_class(self, column_id, column_class):
        self.__styles[column_id] = column_class
    def add_row(self):
        self.__rows.append(["-"] * len(self.__columns))
    def set_cell(self, column_id, text, style=None):
        if column_id in self.__indices:
            if style is not None:
                self.__cell_styles[(column_id, len(self.__rows)-1)] = style
            self.__rows[-1][self.__indices[column_id]] = text
    def write(self, outfile):
        if self.__table_class is not None:
            outfile.start_tag("table", "class='%s'" % self.__table_class)
        else:
            outfile.start_tag("table")
        outfile.start_tag("tr")
        for column_id in self.__columns:
            name = self.__names.get(column_id, column_id)
            outfile.content("<th class='title'>%s</th>" % name)
        outfile.end_tag() # tr
        for rowi, row in enumerate(self.__rows):
            outfile.start_tag("tr")
            for i, cell in enumerate(row):
                column_id = self.__columns[i]
                style = self.__styles.get(column_id, 'stat')
                style = self.__cell_styles.get((column_id, rowi), style)
                outfile.content("<td class='%s'>%s</td>" % (style, cell))
            outfile.end_tag() # tr
        outfile.end_tag() # table


class Outfile(object):
    def __init__(self, f):
        self.f = f
        self.stack = []
        self.tabsize = 4

    def pad(self):
        return " " * len(self.stack) * self.tabsize

    def write(self, *args, **kwargs):
        self.f.write(*args, **kwargs)

    def start_tag(self, tag, rest=""):
        self.write(self.pad())
        self.write("<%s %s>\n" % (tag, rest))
        self.stack.append(tag)

    def content(self, content):
        lines = content.split("\n")
        for line in lines:
            self.write(self.pad())
            self.write(line)
            self.write("\n")

    def end_tag(self):
        tag = self.stack.pop(len(self.stack)-1)
        self.write(self.pad())
        self.write("</%s>\n" % tag)

    def oneliner(self, tag, **kwargs):
        extra = kwargs.get("extra", "")
        content = kwargs.get("content", "")
        text = "<%s %s>%s</%s>" % (tag, extra, content, tag)
        self.content(text)

    def comment(self, comment):
        self.write("\n")
        self.content("<!-- %s -->" % comment)