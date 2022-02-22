# ***********************************************************************
# * Licensed Materials - Property of IBM
# *
# * IBM SPSS Products: Statistics Common
# *
# * (C) Copyright IBM Corp. 2021
# *
# * US Government Users Restricted Rights - Use, duplication or disclosure
# * restricted by GSA ADP Schedule Contract with IBM Corp.
# ************************************************************************/


"""
Python StatJSON generation tooling for extensions.
"""


import json
from enum import Enum




class StatJSON:
    """
    Use this class to generate StatJSON documents representing Statistics
    output for a single procedure.
    """


    def __init__(self, procedure_title):
        """
        Constructor. Invoke with the user-facing procedure title
        and the OMS name for the procedure.
        """


        self._procedure_title = procedure_title
        self._document = {
            "name": procedure_title,
            "items": []
        }


    def add_table(self, table):
        """ Invoke with a table object as defined in this module. """
        self._document["items"].append({"table": table.get_table()})


    def add_chart(self, chart):
        """ Invoke with a chart object as defined in this module"""
        self._document["items"].append({"graph": chart.get_chart()})


    def add_warnings(self, warning_table):
        """ Invoke with a warning object as defined in this module"""
        self._document["items"].append({"warning": warning_table.get_warnings()})


    def add_notes(self, notes):
        """ Invoke with a note object as defined in this module"""
        if "notes" not in self._document["items"][0]:
            self._document["items"].insert(0, {"notes": [notes.get_notes()]})
        else:
            self._document["items"][0]["notes"].append(notes.get_note())


    def add_text(self, text):
        """ Invoke with a text object as defined in this module"""
        self._document["items"].append({"text": text.get_text()})


    def add_sub_heading(self, heading):
        """ Invoke with a heading object as defined in this module"""
        self._document["items"].append({"heading": heading.get_subheading()})


    def get_json(self):
        stat_json_obj = json.dumps({"procedure": self._document}, ensure_ascii=False)
        return stat_json_obj




class Table:
    """ StatJSON table output object. """


    def __init__(self, table_title, oms_title):
        """Constructor. Invoke with user-facing title and OMS title."""
        self._table = {
            "name": oms_title,
            "title": {"value": table_title},
            "default_cell_format": {
                "type": "F",
                "decimals": 0
            },
            "dimensions": {},
            "cells": []
        }


    class DimensionType(Enum):
        """ Dimension type """
        ROWS = "rows"
        COLUMNS = "columns"
        LAYERS = "layers"


    class DimensionProperty(Enum):
        """ Show property of dimension """
        SHOW_NAME = "show_dimension_name"
        SHOW_CATEGORIES = "show_dimension_categories"


    class Type(Enum):
        """ Table type """
        TABLE = "table"
        NOTE = "note"
        WARNING = "warning"


    class TitleType(Enum):
        """ Title type """
        STRING = "string"
        VARIABLE = "variable"
        VARIABLE_VALUE = "variable_value"


    class FormatType(Enum):
        NONE = "NONE"
        A = "A"
        AHEX = "AHEX"
        COMMA = "COMMA"
        DOLLAR = "DOLLAR"
        F = "F"
        IB = "IB"
        PIBHEX = "PIBHEX"
        P = "P"
        PIB = "PIB"
        PK = "PK"
        RB = "RB"
        RBHEX = "RBHEX"
        Z = "Z"
        N = "N"
        E = "E"
        DATE = "DATE"
        TIME = "TIME"
        DATETIME = "DATETIME"
        ADATE = "ADATE"
        JDATE = "JDATE"
        DTIME = "DTIME"
        WKDAY = "WKDAY"
        MONTH = "MONTH"
        MOYR = "MOYR"
        QYR = "QYR"
        WKYR = "WKYR"
        PERCENT = "PERCENT"
        DOT = "DOT"
        CCA = "CCA"
        CCB = "CCB"
        CCC = "CCC"
        CCD = "CCD"
        CCE = "CCE"
        EDATE = "EDATE"
        SDATE = "SDATE"
        G = "G"
        MTIME = "MTIME"
        YMDHMS = "YMDHMS"


    class Cell:
        """ Cell object in table output item. """


        cell_object_key = ["value", "default_cell_format", "footnote_refs"]


        def __init__(self, value):
            """ Cell Constructor. """
            self._value = None
            if self.__is_valid(value):
                self._value = value


        def __is_valid(self, value):
            """ Check value if is valid"""
            result = False
            if isinstance(value, (str, float, int)):
                result = True
            elif isinstance(value, dict) and "value" in value:
                if all(key in Table.Cell.cell_object_key for key in value):
                    result = True
            elif isinstance(value, list):
                for v in value:
                    result = self.__is_valid(v)
                    if not result:
                        break


            return result


        def set_default_cell_format(self, format_type=None, width=None, decimals=None):
            if isinstance(self._value, str):
                self._value = {"value": self._value}
                default_cell = {}


                if format_type is not None:
                    default_cell["type"] = format_type.value
                if width is not None:
                    default_cell["width"] = width
                if decimals is not None:
                    default_cell["decimals"] = decimals


                if len(default_cell) > 0:
                    self._value["default_cell_format"] = default_cell


        def get_value(self):
            """ Get cell value"""
            return self._value


    def get_table(self):
        """ Returns the dictionary version of the table."""
        return self._table


    def update_title(self, title_type=TitleType.STRING, footnote_refs=None):
        """ Set title for table"""
        title = self._table["title"]
        if isinstance(title, dict):
            if isinstance(title_type, Table.TitleType) and title_type != Table.TitleType.STRING:
                title["type"] = title_type


            if footnote_refs is not None:
                title["footnote_refs"] = footnote_refs


            self._table["title"] = title


    def set_type(self, table_type):
        """ Set table type"""
        if isinstance(table_type, Table.Type):
            self._table["type"] = table_type.value


    def set_default_cell_format(self, format_type=FormatType.F, width=10, decimals=0):
        """ Set default cell format for table."""
        if isinstance(format_type, Table.FormatType):
            default_format = {"type": format_type.value, "width": width, "decimals": decimals}
            self._table["default_cell_format"] = default_format


    def add_dimension(self, dim_type, value, is_show_label=False, descendants=None):
        """ Add dimension for table"""
        if isinstance(dim_type, Table.DimensionType):
            dimension = {"value": value, "show_label": is_show_label}
            if descendants is not None:
                dimension["descendants"] = descendants


            if dim_type.value not in self._table["dimensions"]:
                self._table["dimensions"][dim_type.value] = []
            self._table["dimensions"][dim_type.value].append(dimension)


    def set_showed_dimension_name(self, is_show):
        """ True to show the dimension name in the table (default), false to hide it."""
        if isinstance(is_show, bool):
            self._table["dimensions"][Table.DimensionProperty.SHOW_NAME.value] = is_show


    def set_showed_dimension_categories(self, is_show):
        """ True to show all of the dimension categories in the table (default), false to hide them"""
        if isinstance(is_show, bool):
            self._table["dimensions"][Table.DimensionProperty.SHOW_CATEGORIES.value] = is_show


    def add_cells(self, cells):
        """ Add the cells for table"""
        if isinstance(cells, (list, tuple)):
            cells = [(lambda x: x[0] if isinstance(x, (list, tuple)) else x)(cell) for cell in cells]
            self._table["cells"].append(cells)


    def add_footnotes(self, footnote):
        """ Add footnote for table"""
        fts = self._table.get("footnotes", [])
        if isinstance(footnote, (list, tuple)):
            fts.extend(footnote)
        else:
            fts.append(footnote)
        self._table["footnotes"] = fts


    def set_hid_title(self, is_hid):
        """ True to hide the table title"""
        if isinstance(is_hid, bool):
            self._table["hide_title"] = is_hid


    def set_min_data_column_width(self, width):
        """ Set minimum data column width, but needs to be greater than 22 """
        if 22 <= width <= 800:
            self._table["min_data_column_width"] = width


    def set_max_data_column_width(self, width):
        """ Set maximal data column width, but needs to be less than 800 """
        if 22 <= width <= 800:
            self._table["max_data_column_width"] = width




class Chart:
    """ StatJSON chart/graph output object. """


    def __init__(self, chart_title, oms_title):
        """Constructor. Invoke with user-facing title and OMS title."""
        self._graph = {
            "name": oms_title,
            "title": chart_title,
            "type": "",
            "X": {
                "data": [],
                "label": ""
            },
            "Y": {
                "data": [],
                "label": ""
            }
        }


    class Type(Enum):
        """ Chart type"""
        Area = "Area"
        Bar = "Bar"
        Boxplot = "Boxplot"
        Histogram = "Histogram"
        Line = "Line"
        Pie = "Pie"
        Scatterplot = "Scatterplot"


    class Axis(Enum):
        """ Axis type"""
        X = "X"
        Y = "Y"


    class ShowItem(Enum):
        """ Show item"""
        LEGEND = "show_legend"
        X_LABEL = "show_x_label"
        Y_LABEL = "show_y_label"
        DATA_LABELS = "show_data_labels"


    class SplitAttribute(Enum):
        """ Split attribute"""
        COLOR = "color"
        PATTERN = "pattern"
        SIZE = "size"
        PANEL = "panel"
        MARKER = "marker"


    def get_chart(self):
        """ Returns the dictionary version of the chart."""
        return self._graph


    def set_type(self, chart_type):
        """ Set chart type """
        if isinstance(chart_type, Chart.Type):
            self._graph["type"] = chart_type.value


    def set_axis_data(self, axis, data):
        """ Set data for the specified axis """
        if isinstance(axis, Chart.Axis):
            if isinstance(data, (str, float, int, bool)):
                self._graph[axis.value]["data"].append(data)
            elif isinstance(data, (list, tuple)):
                self._graph[axis.value]["data"].extend(data)


    def set_axis_label(self, axis, label):
        """ Set label for the specified axis """
        if isinstance(axis, Chart.Axis):
            self._graph[axis.value]["label"] = label


    def set_showed_item(self, item, is_show):
        """ True to show, false to hide the specified item """
        if isinstance(item, Chart.ShowItem) and isinstance(is_show, bool):
            self._graph[item.value] = is_show


    def set_split(self, data, label="", split_attr=None):
        """ Categorical split variable """
        split_data = []
        if isinstance(data, str):
            split_data.append(data)
        elif isinstance(data, (list, tuple)):
            split_data.extend(data)


        split = {"data": split_data}


        if label:
            split["label"] = label


        if isinstance(split_attr, Chart.SplitAttribute):
            split["split_by"] = split_attr.value


        self._graph["split"] = split




class Warnings:
    """ StatJSON warning output object"""


    def __init__(self, text):
        """Constructor. Invoke with text"""
        self._warning = {
            "text": text
        }


    def get_warnings(self):
        """ Return the dictionary of warning item"""
        return self._warning




class Notes:
    """ StatJSON notes table output object"""


    def __init__(self, header, value):
        """Constructor. Invoke with header and value"""
        self._notes = {
            "row_header": header,
            "cell_value": value
        }


    def get_notes(self):
        """ Return the dictionary of note item"""
        return self._notes




class Text:
    """ StatJSON text output object. """


    def __init__(self, text_title):
        """Constructor. Invoke with text title."""
        self._text = {
            "name": text_title,
            "content": ""
        }


    def get_text(self):
        """ Returns the dictionary version of the text."""
        return self._text


    def set_content(self, content):
        """ Set text content """
        if isinstance(content, str):
            self._text["content"] = content




class SubHeading:
    """ An intermediate sub-heading. """


    def __init__(self, heading_title):
        """Constructor. Invoke with heading title."""
        self._heading = {
            "label": heading_title,
            "items": []
        }


    def get_subheading(self):
        """ Returns the dictionary version of the subheading."""
        return self._heading


    def add_output_item(self, item):
        """ Add an output sub-item for this heading branch"""
        if isinstance(item, (Table, Chart, Text, SubHeading)):
            self._heading["items"].append(item)