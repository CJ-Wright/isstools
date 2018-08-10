import re
import time as ttime

import numpy as np
import pkg_resources

from PyQt5 import uic, QtGui
from matplotlib.backends.backend_qt5agg import (
    FigureCanvasQTAgg as FigureCanvas,
    NavigationToolbar2QT as NavigationToolbar)
from matplotlib.figure import Figure
from matplotlib.widgets import Cursor


import datetime
import json


ui_path = pkg_resources.resource_filename('isstools', 'ui/ui_xview_db_browser.ui')


class UIDBBrowser(*uic.loadUiType(ui_path)):

    def __init__(self,
                 db,
                 parent_widget,
                 *args, **kwargs):

        super().__init__(*args, **kwargs)
        self.setupUi(self)
        # self.addCanvas()
        self.db = db
        self.pushButton_search.clicked.connect(self.search_db)
        self.parent_widget = parent_widget
        self.checkBoxes = ['checkBox_pi',
                           'checkBox_saf',
                           'checkBox_proposal',
                           'checkBox_element'
                          ]

        for checkBox in  self.checkBoxes:
            getattr(self, checkBox).stateChanged.connect(self.set_query)

        self.search_args = {'checkBox_pi':{'edit':'lineEdit_pi','arg':'PI'},
                            'checkBox_proposal': {'edit': 'lineEdit_proposal', 'arg': 'PROPOSAL'},
                            'checkBox_saf': {'edit': 'lineEdit_saf', 'arg': 'SAF'}
                            }
        self.model_datasets = QtGui.QStandardItemModel(self)
        self.listView_datasets.setModel(self.model_datasets)
        self.listView_datasets.selectionModel().selectionChanged.connect(self.display_dataset_info)

    def display_dataset_info(self):
        index = self.listView_datasets.currentIndex().row()
        dic = (self.datasets_filtered[index].start)
        print(dic)
        PI = dic['PI']
        time = datetime.datetime.fromtimestamp(dic['time']).strftime('%Y-%m-%d %H:%M:%S')
        year = dic['year']
        cycle = dic['cycle']
        proposal = dic['PROPOSAL']
        saf = dic['SAF']
        name = dic['name']
        if ('comment' in dic):
            comment = dic['comment']
        else:
            comment = ''
        dataset_info_all = json.dumps(dic)
        dataset_info_str ='Name: {}\nComment: {}\nCycle {}-{}\nPI: {}\nTime: {}\nProposal: {}\nSAF: {}\n\n\n{}'.\
            format(name,comment,year, cycle,PI,time, proposal, saf,dataset_info_all)



        self.textBrowser_dataset_info.setText(dataset_info_str)


    def set_query(self):
        self.query = ''
        for checkBox in self.checkBoxes:
            if getattr(self, checkBox).isChecked():
                arg = self.search_args[checkBox]['arg']
                edit = self.search_args[checkBox]['edit']
                value = getattr(self, edit).text()
                self.query ='{}={}'.format(arg, value)
        print(self.query)

    def search_db(self):
        self.set_query()
        if self.query!='':
            ds=self.db(self.query)
            datasets = list(ds)
            print(len(datasets))
            self.datasets_filtered = list()
            if datasets:
                for dataset in datasets:
                    dataset_info = dataset.start
                    if ('name' in dataset_info):
                        self.datasets_filtered.append(dataset)

                self.parent_widget.statusBar().showMessage('Search returned {} datasets'.format(str(len(self.datasets_filtered))))
                self.model_datasets.clear()
                parent = self.model_datasets.invisibleRootItem()
                for dataset in self.datasets_filtered:
                    dataset_info = dataset.start
                    if 'name' in dataset_info:
                        dataset_time = datetime.datetime.fromtimestamp(dataset_info['time']).strftime('%Y-%m-%d %H:%M:%S')
                        dataset_entry = '{} - {} / {}'.format(dataset_info['scan_id'],dataset_info['name'],dataset_time)
                        item = QtGui.QStandardItem(dataset_entry)
                        parent.appendRow(item)

            else:
                self.parent_widget.statusBar().showMessage("Search did not return any datasets")


    # def addCanvas(self):
    #     self.figure_gain_matching = Figure()
    #     self.figure_gain_matching.set_facecolor(color='#FcF9F6')
    #     self.canvas_gain_matching = FigureCanvas(self.figure_gain_matching)
    #     self.figure_gain_matching.add_subplot(111)
    #     self.toolbar_gain_matching = NavigationToolbar(self.canvas_gain_matching, self, coordinates=True)
    #     self.plot_gain_matching.addWidget(self.toolbar_gain_matching)
    #     self.plot_gain_matching.addWidget(self.canvas_gain_matching)
    #     self.canvas_gain_matching.draw_idle()
    #
    #     self.figure_xia_all_graphs = Figure()
    #     self.figure_xia_all_graphs.set_facecolor(color='#FcF9F6')
    #     self.canvas_xia_all_graphs = FigureCanvas(self.figure_xia_all_graphs)
    #     self.figure_xia_all_graphs.ax = self.figure_xia_all_graphs.add_subplot(111)
    #     self.toolbar_xia_all_graphs = NavigationToolbar(self.canvas_xia_all_graphs, self, coordinates=True)
    #     self.plot_xia_all_graphs.addWidget(self.toolbar_xia_all_graphs)
    #     self.plot_xia_all_graphs.addWidget(self.canvas_xia_all_graphs)
    #     self.canvas_xia_all_graphs.draw_idle()
    #     self.cursor_xia_all_graphs = Cursor(self.figure_xia_all_graphs.ax, useblit=True, color='green', linewidth=0.75)
    #     self.figure_xia_all_graphs.ax.clear()