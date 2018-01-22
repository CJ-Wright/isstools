from PyQt5 import QtCore
import pandas as pd
from larch import Group as xafsgroup


class XASDataSet:
    _md = {}
    _data = pd.DataFrame()
    _mu = pd.DataFrame()
    _filename = ''

    def __init__(self, data=None, md=None, mu=None, filename=None, *args, **kwargs):
        self.larch = xafsgroup()

        if data is not None:
            self._data = pd.DataFrame(data)

        if md is not None:
            self._md = md
            if 'e0' in md:
                self.larch.e0 = int(md['e0'])
            elif 'edge' in md:
                edge = md['edge']
                self.larch.e0 = int(edge[edge.find('(') + 1: edge.find(')')])

        if mu is not None:
            if hasattr(mu, 'values'):
                values = mu.values
            else:
                values = mu
            self._mu = pd.DataFrame(values, columns=['mu'])
            self.larch.mu = self._mu

        if filename is not None:
            self._filename = filename

    @property
    def data(self):
        return self._data

    @data.setter
    def data(self, data):
        self._data = pd.DataFrame(data)
        self.larch.energy = self._data['energy']

    @property
    def md(self):
        return self._md

    @md.setter
    def md(self, md):
        self._md = md
        if 'e0' in md:
            self.larch.e0 = int(md['e0'])
        elif 'edge' in md:
            edge = md['edge']
            self.larch.e0 = int(edge[edge.find('(') + 1: edge.find(')')])

    @property
    def mu(self):
        return self._mu

    @mu.setter
    def mu(self, mu):
        if hasattr(mu, 'values'):
            values = mu.values
        else:
            values = mu
        self._mu = pd.DataFrame(values, columns=['mu'])
        self.larch.mu = self._mu

    @property
    def filename(self):
        return self._filename

    @filename.setter
    def filename(self, filename):
        self._filename = filename


class XASProject(QtCore.QObject):
    datasets_changed = QtCore.pyqtSignal(object)
    _datasets = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._datasets = []

    @property
    def datasets(self):
        return self._datasets

    def insert(self, dataset, index=None):
        if index is None:
            index = len(self._datasets)
        self._datasets.insert(index, dataset)
        self.datasets_changed.emit(self._datasets)

    def append(self, dataset):
        self._datasets.append(dataset)
        self.datasets_changed.emit(self._datasets)

    def removeDatasetIndex(self, index):
        del self._datasets[index]
        self.datasets_changed.emit(self._datasets)

    def removeDataset(self, dataset):
        self._datasets.remove(dataset)
        self.datasets_changed.emit(self._datasets)

    def __repr__(self):
        return f'{self._datasets}'.replace(', ', ',\n ')

    def __iter__(self):
        self._iterator = 0
        return self

    def __next__(self):
        if self._iterator < len(self.datasets):
            curr_iter = self._iterator
            self._iterator += 1
            return self.datasets[curr_iter]
        else:
            raise StopIteration

    def __getitem__(self, item):
        return self.datasets[item]