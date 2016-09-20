# Temperature-conversion program using PyQt
import numpy as np
from PyQt4 import uic
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt4agg import (
    FigureCanvasQTAgg as FigureCanvas,
    NavigationToolbar2QT as NavigationToolbar)
import pkg_resources

from isstools.trajectory.trajectory  import trajectory

ui_path = pkg_resources.resource_filename('isstools', 'ui/XLive.ui')

# def my_plan(dets, some, other, param):
#	...


def auto_redraw_factory(fnc):

    def stale_callback(fig, stale):
        if fnc is not None:
            fnc(fig, stale)
        if stale and fig.canvas:
            fig.canvas.draw_idle()

    return stale_callback

class ScanGui(*uic.loadUiType(ui_path)):
    def __init__(self, plan_func, parent=None):
        super().__init__(parent)
        self.plan_func = plan_func
        self.setupUi(self)
        self.fig = fig = self.figure_content()
        self.addCanvas(fig)
        self.run_start.clicked.connect(self.test)
        self.push_build_trajectory.clicked.connect(self.build_trajectory)
        self.push_save_trajectory.clicked.connect(self.save_trajectory)

    def addCanvas(self, fig):
        self.canvas = FigureCanvas(fig)

        self.toolbar = NavigationToolbar(self.canvas,
                                         self.tab_2, coordinates=True)
        self.toolbar.setMaximumHeight(18)
        self.plots.addWidget(self.toolbar)
        self.plots.addWidget(self.canvas)
        self.canvas.draw()

    @property
    def plot_x(self):
        return self.plot_selection_dropdown.value()

    def figure_content(self):
        fig1 = Figure()
        fig1.set_facecolor(color='0.89')
        fig1.stale_callback = auto_redraw_factory(fig1.stale_callback)
        ax1f1 = fig1.add_subplot(111)
        ax1f1.plot(np.random.rand(5))
        self.ax = ax1f1
        return fig1

    def build_trajectory(self):
        E0 = int(self.edit_E0.text())

        preedge_lo = int(self.edit_preedge_lo.text())
        preedge_hi = int(self.edit_preedge_hi.text())
        edge_lo = preedge_hi
        edge_hi = int(self.edit_edge_hi.text())
        postedge_lo = edge_hi
        postedge_hi = int(self.edit_postedge_hi.text())

        velocity_preedge = int (self.velocity_preedge.text())
        velocity_edge = int(self.velocity_edge.text())
        velocity_postedge = int(self.velocity_postedge.text())

        preedge_stitch_lo = int(self.preedge_stitch_lo.text())
        preedge_stitch_hi = int(self.preedge_stitch_hi.text())
        edge_stitch_lo =  int(self.edge_stitch_lo.text())
        edge_stitch_hi = int(self.edge_stitch_hi.text())
        postedge_stitch_lo = int(self.postedge_stitch_lo.text())
        postedge_stitch_hi = int(self.postedge_stitch_hi.text())

        padding_preedge = int(self.padding_preedge.text())
        padding_postedge = int(self.padding_postedge.text())

        traj=trajectory(edge_energy = E0, offsets = ([preedge_lo,preedge_hi,edge_hi,postedge_hi]),velocities = ([velocity_preedge, velocity_edge, velocity_postedge]),
                        stitching = ([preedge_stitch_lo, preedge_stitch_hi, edge_stitch_lo, edge_stitch_hi, postedge_stitch_lo, postedge_stitch_hi]),
                        servocycle = 16000, padding_lo = padding_preedge ,padding_hi=padding_postedge)

    def save_trajectory(selfself):
        pass

    def test(self):
        self.plan_func()


#    @property
#    def plan(self):
#        lp = LivePlot(self.plot_x,
#                      self.plot_y,
#                      fig=self.fig)

#        @subs_decorator([lp])
#        def scan_gui_plan():
#            return (yield from self.plan_func(self.dets, *self.get_args()))


#def tune_factory(motor):
#    from bluesky.plans import scan
#    from collections import ChainMap

#    def tune(md=None):
#        if md is None:
#            md = {}
#        md = ChainMap(md, {'plan_name': 'tuning {}'.format(motor)})
#        yield from scan(motor, -1, 1, 100, md=md)

#    return tune


