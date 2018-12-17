from rapidz import Stream
from shed.translation import ToEventStream, FromEventStream
import numpy as np
import operator as op


def interpolate_dataframes(ground_truth, *dataframes):
    # Interpolate the dataframes onto the ground truth timetable
    pass


def bin_spectra(df):
    # rebin the dataframe
    pass


def bg_subs(df):
    # subtract the background
    pass


def derivative(df):
    # derivative
    pass


def det_correction(x):
    pass


def normalize(x):
    pass


def to_k(e):
    pass


def Retrieve(x):
    pass


pre_edge = np.zeros(10)

post_edge = np.zeros(10)

window = np.ones(10)

handler_reg = {}  # Fill in later
raw_source = Stream()
filled = raw_source.map(Retrieve(handler_reg))

# This should pass out pandas dataframes now?
a = FromEventStream('event', ('data', 'I0'), filled, stream_name='I0')
# This should pass out pandas dataframes now?
b = FromEventStream('event', ('data', 'It'), filled, stream_name='It')

interp_data = a.zip(b).map(interpolate_dataframes)
bin_data = interp_data.map(bin_spectra,
                           energy_string='energy')
mu = bin_data.pluck('i')
e = bin_data.pluck('e')
corrected_mu = mu.map(det_correction).map(op.sub, pre_edge)
e0 = (corrected_mu
      .map(derivative)
      .map(np.argmax)
      .zip(e)
      .starmap(lambda x, y: y[x]))
norm_mu = corrected_mu.map(normalize)
k = e.map(to_k)

pe_corrected_mu = norm_mu.map(op.sub, post_edge)
k_weight_mu = pe_corrected_mu.zip(k.map(lambda x: x ** 2)).map(op.mul)
window_mu = k_weight_mu.map(op.mul, window)

xafs_real_space = window_mu.map(np.fft.fft)

raw_source.visualize(source_node=True)
