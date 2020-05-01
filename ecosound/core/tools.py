# -*- coding: utf-8 -*-
"""
Created on Wed Jan 29 21:21:40 2020

@author: xavier.mouy
"""
import json
import re
from datetime import datetime
import ecosound.core.decorators
import numpy as np
from scipy import interpolate
import os, sys


def read_json(file):
    """Load JSON file as dict."""
    with open(file, "r") as read_file:
        data = json.load(read_file)
    return data


@ecosound.core.decorators.listinput
def filename_to_datetime(files):
    """Extract date from a list of str of filenames."""
    current_dir = os.path.dirname(os.path.realpath(__file__))
    patterns = read_json(os.path.join(current_dir, r'timestamp_formats.json'))
    regex_string = '|'.join([pattern['string_pattern'] for pattern in patterns])
    time_formats = [pattern['time_format'] for pattern in patterns]
    timestamps = [None] * len(files)
    p = re.compile(regex_string)
    for idx, file in enumerate(files):
        datestr = p.search(file)
        for time_format in time_formats:
            ok_flag = False
            try:
                timestamps[idx] = datetime.strptime(datestr[0], time_format)
                ok_flag = True
            except:
                ok_flag = False
            if ok_flag is True:
                break
        if ok_flag is False:
            raise ValueError('Time format not recognized:' + file)
    return timestamps


def normalize_vector(vec):
    """ 
    Normalize amplitude of vector.
    """
    # vec = vec+abs(min(vec))
    # normVec = vec/max(vec)
    # normVec = (normVec - 0.5)*2
    vec = vec - np.mean(vec)
    normVec = vec/max(vec)
    return normVec


def tighten_signal_limits(signal, energy_percentage):
    """
    Tighten signal limits

    Redefine start and stop samples to have "energy_percentage" of the original
    signal. Returns a list with the new start and stop sample indices.

    """
    cumul_energy = np.cumsum(np.square(signal))
    cumul_energy = cumul_energy/max(cumul_energy)
    percentage_begining = (1-(energy_percentage/100))/2
    percentage_end = 1 - percentage_begining
    chunk = [np.nonzero(cumul_energy > percentage_begining)[0][0], 
             np.nonzero(cumul_energy > percentage_end)[0][0]]
    return chunk


def resample_1D_array(x, y, resolution, kind='linear'):
    """
    Interpolate values of coordinates x and y with a given resolution.
    Default uisn linear interpolation.
    """
    f = interpolate.interp1d(x, y, kind=kind, fill_value='extrapolate')
    xnew = np.arange(x[0], x[-1]+resolution, resolution)
    ynew = f(xnew)
    return xnew, ynew 


def entropy(array_1d, apply_square=False):
        """ 
        Aggregate (SHannon's) entropy as defined in the Raven manual
        apply_square = True, suqares the array value before calculation.
        """
        if apply_square:
            array_1d = np.square(array_1d)
        values_sum = np.sum(array_1d)
        H = 0
        for value in array_1d:
            ratio = (value/values_sum)
            if ratio <= 0:
                H += 0
            else:
                H += ratio*np.log2(ratio)
        return H

def derivative_1d(array, order=1):
    """
    Derivative of order "order" of a 1D array. Subtract the element i+1 to i.
    If order > 1, the process is repeated iteratively "order" times. Note that
    the resulting array is shorter than the original array by "order" elements.

    """
    for n in range(0, order, 1):
        array = np.subtract(array[1:], array[0:-1])
    return array
