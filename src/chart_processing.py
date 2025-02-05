from abc import ABC, abstractmethod
import ast
import io
import logging
import re

from bs4 import BeautifulSoup
import matplotlib.pyplot as pyplot
import pandas as pd

import config
from helper_functions import add_strong_between_tags
from sn_attachment import ChartStringNSAttachment, ChartImageNSAttachment


def what_module_is_this():
    return __name__


class ChartProcessor(ABC):
    """
    Abstract class for processing chart content in html that can not be converted by pandoc.

    Extraction of chart data in CSS or other code formatting from a html string and the generation of an image,
    csv file and data table of the data and placing these into the html content in place of the original chart format.

    If multiple charts exist in the provided html they will all be processed.

    Attributes
    ----------
    note : Note object
    html : str
        string containing html code to be parsed for charts and modified with replacement chart content
    create_image : bool
        If True will create a pbg image of the chart and add to html
    create_csv : bool
        If True will create a csv file and place link to file in the html.
    create_data_table : bool
        If True will add a data table of the chart data to the html

    Methods
    -------
    process_charts()
        Process the html content and generate the required html content and attachments.

    """
    def __init__(self, note, html, create_image=True, create_csv=True, create_data_table=True):
        self.logger = logging.getLogger(f'{config.yanom_globals.app_name}.'
                                        f'{what_module_is_this()}.'
                                        f'{self.__class__.__name__}'
                                        )
        self.logger.setLevel(config.yanom_globals.logger_level)
        self._note = note
        self._raw_html = html
        self._create_image = create_image
        self._create_csv = create_csv
        self._create_data_table = create_data_table
        self._processed_html = self._raw_html
        self._soup = BeautifulSoup(self._raw_html, 'html.parser')
        self._attachments = {}
        self._charts = []  # used for regression testing
        self._chart_config = {}
        self.process_charts()

    @property
    def processed_html(self):
        return self._processed_html

    @abstractmethod
    def _find_all_charts(self):  # pragma: no cover
        pass

    def process_charts(self):
        """
        Process the provided html content and generate replacement chart elements.

        Html is parsed for charts, charts are analysed for formatting and data. Replacement chart elements are
        created.  Replace the original chart html with new elements

        """
        chart_tags = self._find_all_charts()

        for tag in chart_tags:
            self._fetch_chart_config_from_html(tag)
            chart = self._create_chart_object()
            self._charts.append(chart)
            self._set_chart_config(chart)
            self._retrieve_chart_data(tag, chart)
            self._create_required_replacement_chart_elements(chart)
            self._add_new_chart_elements_to_html(tag, chart)

    def _add_new_chart_elements_to_html(self, tag, chart):
        search_for = str(tag)
        replace_with = self._new_chart_elements_html(chart)
        self._processed_html = self._processed_html.replace(search_for, replace_with)

    def _new_chart_elements_html(self, chart):
        elements_to_add = ''
        if self._create_image:
            elements_to_add = elements_to_add + f"<p>{self._note.attachments[f'{id(chart)}.png'].html_link}</p>"
        if self._create_csv:
            elements_to_add = elements_to_add + f"<p>{self._note.attachments[f'{id(chart)}.csv'].html_link}</p>"
        if self._create_data_table:
            elements_to_add = elements_to_add + f"<p>{chart.html_chart_data_table}</p>"

        return elements_to_add

    def _create_required_replacement_chart_elements(self, chart):
        if self._create_image:
            chart.plot_chart()
            self._generate_png_attachment(chart)

        if self._create_csv:
            chart.make_csv_chart_data_string()
            self._generate_csv_attachment(chart)

        if self._create_data_table:
            chart.make_html_chart_data_table()

    @abstractmethod
    def _create_chart_object(self):  # pragma: no cover
        pass

    @abstractmethod
    def _fetch_chart_config_from_html(self, tag):  # pragma: no cover
        pass

    @staticmethod
    @abstractmethod
    def _retrieve_chart_data(tag, chart):  # pragma: no cover
        pass

    @abstractmethod
    def _set_chart_config(self, chart):  # pragma: no cover
        pass

    def _generate_csv_attachment(self, chart):
        self.logger.debug("Generate chart csv file")
        self._note.attachments[f"{id(chart)}.csv"] = ChartStringNSAttachment(self._note, f"{id(chart)}.csv",
                                                                             chart.csv_chart_data_string)
        self._note.attachments[f"{id(chart)}.csv"].process_attachment()
        self._note.attachment_count += 1

    def _generate_png_attachment(self, chart):
        self.logger.debug("Generate chart image attachment")

        self._note.attachments[f"{id(chart)}.png"] = ChartImageNSAttachment(self._note, f"{id(chart)}.png",
                                                                            chart.png_img_buffer)
        self._note.attachments[f"{id(chart)}.png"].process_attachment()
        self._note.image_count += 1

    @property
    def charts(self):
        return self._charts

    class Chart(ABC):
        def __init__(self):
            self.logger = logging.getLogger(f'{config.yanom_globals.app_name}.'
                                            f'{what_module_is_this()}.'
                                            f'{self.__class__.__name__}')

            self.logger.setLevel(config.yanom_globals.logger_level)
            self._chart_type = str
            self._title = str
            self._df = None
            self._x_axis_title = str
            self._y_axis_title = str
            self.x_category_labels = []
            self.y_category_labels = []
            self._csv_chart_data_string = str
            self._html_chart_data_table = str
            self._chart_fig = None
            self._png_img_buffer = None

        @abstractmethod
        def plot_chart(self):  # pragma: no cover
            pass

        @staticmethod
        def fig_to_img_buf(fig):
            """Convert a Matplotlib figure to png format in an io.Bytes buffer and return it"""
            buf = io.BytesIO()
            fig.savefig(buf, format='png')  # png is often smaller than jpeg for plots
            buf.seek(0)
            return buf

        @staticmethod
        def remove_chart_frame(ax):
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.spines['bottom'].set_visible(False)
            ax.spines['left'].set_visible(False)
            return ax

        def set_title_and_axes(self, ax):
            ax.set_title(self._x_axis_title, y=-0.15, fontdict=None)
            ax.set_ylabel(self._y_axis_title)
            ax.set_ylim(self._df.min().min() * 0.9, self._df.max().max() * 1.1)
            return ax

        def make_html_chart_data_table(self):
            self._html_chart_data_table = self._df.to_html(formatters={'percent': '{:,.2f}'.format})
            self._html_chart_data_table = self._html_chart_data_table.replace('\n', '')
            self._html_chart_data_table = re.sub(r">\s*<", '><', self._html_chart_data_table)
            self._html_chart_data_table = add_strong_between_tags('<th>', '</th>', self._html_chart_data_table)

        def make_csv_chart_data_string(self):
            self._csv_chart_data_string = self._df.to_csv()

        def set_x_axis_title(self, value):
            self._x_axis_title = value

        def set_y_axis_title(self, value):
            self._y_axis_title = value

        def set_title(self, value):
            self._title = value

        def set_df(self, value):
            self._df = value

        @property
        def csv_chart_data_string(self):
            return self._csv_chart_data_string

        @property
        def png_img_buffer(self):
            return self._png_img_buffer

        @property
        def html_chart_data_table(self):
            return self._html_chart_data_table

    class PieChart(Chart):
        def __format_data_for_pie_chart(self):
            self._df["sum"] = self._df.sum(axis=1)
            self._df["percent"] = self._df["sum"] / self._df["sum"].sum() * 100

        def plot_chart(self):
            self.logger.debug("Creating pie chart")
            self.__format_data_for_pie_chart()
            explode = [0.02 for _ in range(len(self._df.index))]
            fig, ax = pyplot.subplots()
            pyplot.title(self._title)
            pyplot.gca().axis("equal")
            pie = pyplot.pie(self._df['sum'], autopct='%1.2f%%', pctdistance=1.2, explode=explode)
            labels = self.y_category_labels
            pyplot.legend(pie[0], labels, bbox_to_anchor=(1, 1), loc="upper right",
                          bbox_transform=pyplot.gcf().transFigure)
            self._png_img_buffer = self.fig_to_img_buf(fig)

    class LineChart(Chart):
        def plot_chart(self):
            self.logger.debug("Creating line chart")
            df_transposed = self._df.copy().T
            fig2, ax = pyplot.subplots()
            ax = self.set_title_and_axes(ax)
            ax = self.remove_chart_frame(ax)
            x_ticks = [x for x in range(len(df_transposed.index))]
            plot = df_transposed.plot(kind='line', grid=True, ax=ax, rot=0, xticks=x_ticks, title=self._title)
            fig = plot.get_figure()
            self._png_img_buffer = self.fig_to_img_buf(fig)

    class BarChart(Chart):
        def plot_chart(self):
            self.logger.debug("Creating bar chart")
            df_transposed = self._df.copy().T
            fig2, ax = pyplot.subplots()
            ax = self.set_title_and_axes(ax)
            ax = self.remove_chart_frame(ax)
            plot = df_transposed.plot(kind='bar', grid=True, ax=ax, rot=0, title=self._title)
            fig = plot.get_figure()
            self._png_img_buffer = self.fig_to_img_buf(fig)


class NSXChartProcessor(ChartProcessor):

    def _find_all_charts(self):
        self.logger.debug("Searching for charts")
        return self._soup.select('div.syno-ns-chart-object')

    def _fetch_chart_config_from_html(self, tag):
        self.logger.debug("Reading chart configuration")
        chart_config = tag.attrs['chart-config']
        chart_config = chart_config.replace('true', 'True')
        chart_config = chart_config.replace('false', 'False')
        self._chart_config = ast.literal_eval(chart_config)

    def _retrieve_chart_data(self, tag, chart):
        self.logger.debug("Retrieving chart data")
        raw_data = tag.attrs['chart-data']
        raw_data = ast.literal_eval(raw_data)
        chart.x_category_labels = raw_data.pop(0)[1:]
        chart.y_category_labels = [item.pop(0) for item in raw_data]
        chart.set_df(pd.DataFrame(raw_data, columns=chart.x_category_labels, index=chart.y_category_labels))

    def _set_chart_config(self, chart):
        chart.set_title(self._chart_config['title'])
        chart.set_x_axis_title(self._chart_config['xAxisTitle'])
        chart.set_y_axis_title(self._chart_config['yAxisTitle'])

    def _create_chart_object(self):
        if self._chart_config['chartType'] == 'pie':
            return self.PieChart()

        if self._chart_config['chartType'] == 'line':
            return self.LineChart()

        return self.BarChart()
