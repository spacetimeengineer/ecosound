# -*- coding: utf-8 -*-
"""
Created on Fri Feb  7 15:27:39 2020

@author: xavier.mouy
"""

from .measurer_builder import BaseClass
from ecosound.core.annotation import Annotation
from ecosound.core.spectrogram import Spectrogram
from ecosound.core.measurement import Measurement
from ecosound.visualization.grapher_builder import GrapherFactory
import ecosound.core.tools
import numpy as np
from scipy.stats import kurtosis, skew
from scipy.stats.mstats import gmean
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle


class SpectrogramFeatures(BaseClass):
    measurer_parameters = ()

    def __init__(self, *args, **kwargs):
        # Initialize all measurer parameters to None
        self.__dict__.update(dict(zip(self.measurer_parameters,
                                      [None]*len(self.measurer_parameters))))
        # Unpack kwargs as measurer parameters if provided on instantiation
        self.__dict__.update(**kwargs)

    @property
    def name(self):
        """Return name of the measurer."""
        measurer_name = 'SpectrogramFeatures'
        return measurer_name

    @property
    def version(self):
        """Return version of the measurer."""
        version = '0.1'
        return version

    def _prerun_check(self, spectrogram, annotations):
        # check that all required arguments are defined
        if True in [self.__dict__.get(keys) is None for keys in self.measurer_parameters]:
            raise ValueError('Not all measurer parameters have been defined.'
                             + ' Required parameters: '
                             + str(self.measurer_parameters))
        # check that spectrogram is a spectrogram class
        if not isinstance(spectrogram, Spectrogram):
            raise ValueError('Input must be an ecosound Spectrogram object'
                             + '(ecosound.core.spectrogram).')
        # check that annotations is an Annotation class
        if not isinstance(annotations, Annotation):
            raise ValueError('Input must be an ecosound Annotation object'
                             + '(ecosound.core.annotation).')

    def compute(self, spectro, annotations, resolution_freq=0.1, resolution_time=0.001, interp='linear', debug=False, verbose=False):
        self._prerun_check(spectro, annotations)
        # loop through each annotation
        for index, annot in annotations.data.iterrows():
            if verbose:
                print('processing annotation ', index)
            tmin = annot['time_min_offset']
            tmax = annot['time_max_offset']
            fmin = annot['frequency_min']
            fmax = annot['frequency_max']
            # extract minmgram for that detection
            minigram = spectro.crop(frequency_min=fmin,
                                    frequency_max=fmax,
                                    time_min=tmin,
                                    time_max=tmax)
            # extract time and frequency envelops
            envelop_time, envelop_freq = self._get_envelops(minigram,
                                                            normalize=True)
            # interpolate each envelop
            axis_t, envelop_time2 = ecosound.core.tools.resample_1D_array(
                minigram.axis_times,
                envelop_time,
                resolution=resolution_time,
                kind=interp)
            axis_f, envelop_freq2 = ecosound.core.tools.resample_1D_array(
                minigram.axis_frequencies,
                envelop_freq,
                resolution=resolution_freq,
                kind=interp)
            # Frequency envelop features
            features_envelop_freq = self.envelop_features(axis_f, envelop_freq2)
            if debug:
                axis_orig = minigram.axis_frequencies
                envelop_orig = envelop_freq
                axis_interp = axis_f
                envelop_interp = envelop_freq2
                features = features_envelop_freq
                title = 'Frequency envelop'
                self.plot_envelop_features(axis_orig,
                                           envelop_orig,
                                           axis_interp,
                                           envelop_interp,
                                           features,
                                           title=title)
            # Time envelop features
            features_envelop_time = self.envelop_features(axis_t, envelop_time2)
            if debug:
                axis_orig = minigram.axis_times
                envelop_orig = envelop_time
                axis_interp = axis_t
                envelop_interp = envelop_time2
                features = features_envelop_time
                title = 'Time envelop'
                self.plot_envelop_features(axis_orig,
                                           envelop_orig,
                                           axis_interp,
                                           envelop_interp,
                                           features,
                                           title=title)
            # Amplitude modulation features
            # TO DO
            # Full spectrogram matrix features
            adjusted_bounds = [features_envelop_time['pct5_location'].values[0],
                               features_envelop_time['pct95_location'].values[0],
                               features_envelop_freq['pct5_location'].values[0],
                               features_envelop_freq['pct95_location'].values[0],
                               ]
            features_spectrogram, frequency_points = self.spectrogram_features(minigram, resolution_freq=resolution_freq, resolution_time=resolution_time,adjusted_bounds=adjusted_bounds, interp=interp)
            if debug:
                self.plot_spectrogram_features(minigram,
                                               features_spectrogram,
                                               adjusted_bounds,
                                               frequency_points,
                                               title='spectrogram features')
            # stack all features
            tmp = pd.DataFrame({
                'uuid': [annot['uuid']],
                # from frequency envelop
                'freq_peak': features_envelop_freq['peak_location'],
                'freq_bandwidth': features_envelop_freq['length'],
                'freq_bandwidth90': features_envelop_freq['length_90'],
                'freq_pct5': features_envelop_freq['pct5_location'],
                'freq_pct25': features_envelop_freq['pct25_location'],
                'freq_pct50': features_envelop_freq['pct50_location'],
                'freq_pct75': features_envelop_freq['pct75_location'],
                'freq_pct95': features_envelop_freq['pct95_location'],
                'freq_iqr': features_envelop_freq['IQR'],
                'freq_asymmetry': features_envelop_freq['asymmetry'],
                'freq_concentration': features_envelop_freq['concentration'],
                'freq_std': features_envelop_freq['std'],
                'freq_kurtosis': features_envelop_freq['kurtosis'],
                'freq_skewness': features_envelop_freq['skewness'],
                'freq_entropy': features_envelop_freq['entropy'],
                'freq_flatness': features_envelop_freq['flatness'],
                'freq_roughness': features_envelop_freq['roughness'],
                'freq_centroid': features_envelop_freq['centroid'],
                # from full spectrogram
                'freq_overall_peak': features_spectrogram['freq_peak'],
                'freq_median_mean': features_spectrogram['freq_median_mean'],
                'freq_median_std': features_spectrogram['freq_median_std'],
                'freq_entropy_mean': features_spectrogram['freq_entropy_mean'],
                'freq_entropy_std': features_spectrogram['freq_entropy_std'],
                'freq_upsweep_mean': features_spectrogram['freq_upsweep_mean'],
                'freq_upsweep_fraction': features_spectrogram['freq_upsweep_fraction'],
                'snr': features_spectrogram['snr'],
                # from time envelop
                'time_peak_sec': features_envelop_time['peak_location'],
                'time_peak_perc': features_envelop_time['peak_location_relative'],
                'time_duration': features_envelop_time['length'],
                'time_duration90': features_envelop_time['length_90'],
                'time_pct5': features_envelop_time['pct5_location'],
                'time_pct25': features_envelop_time['pct25_location'],
                'time_pct50': features_envelop_time['pct50_location'],
                'time_pct75': features_envelop_time['pct75_location'],
                'time_pct95': features_envelop_time['pct95_location'],
                'time_iqr': features_envelop_time['IQR'],
                'time_asymmetry': features_envelop_time['asymmetry'],
                'time_concentration': features_envelop_time['concentration'],
                'time_std': features_envelop_time['std'],
                'time_kurtosis': features_envelop_time['kurtosis'],
                'time_skewness': features_envelop_time['skewness'],
                'time_entropy': features_envelop_time['entropy'],
                'time_flatness': features_envelop_time['flatness'],
                'time_roughness': features_envelop_time['roughness'],
                'time_centroid_sec': features_envelop_time['centroid'],
                'time_centroid_perc': features_envelop_time['centroid_relative'],
                })
            # stack features for each annotation
            if index == 0:
                features = tmp
                features_name = list(features.columns)
                features_name.remove('uuid')
            else:
                features = pd.concat([features, tmp], ignore_index=False)
        # merge with annotation fields
        annotations.data.set_index('uuid', inplace=True, drop=False)
        features.set_index('uuid', inplace=True, drop=True)
        meas = pd.concat([annotations.data, features], axis=1, join='inner')
        meas.reset_index(drop=True, inplace=True)
        # create Measurement object
        measurements = Measurement(measurer_name=self.name,
                                   measurer_version=self.version,
                                   measurements_name=features_name)
        measurements.data = meas
        return measurements

    def spectrogram_features(self, minigram1, resolution_freq, resolution_time, adjusted_bounds=None, interp='linear'):
        if adjusted_bounds:
            minigram = minigram1.crop(time_min=adjusted_bounds[0],
                                      time_max=adjusted_bounds[1],
                                      frequency_min=adjusted_bounds[2],
                                      frequency_max=adjusted_bounds[3],
                                      inplace=False,
                                      )
        else:
            minigram = minigram1
        spectro = minigram.spectrogram.transpose()
        # Spectrum for each time framee
        peak_f = []
        peak_amp = []
        median_f = []
        entropy_agg = []
        root4_magnitude = []
        for spectrum in spectro:
            axis_f, spectrum2 = ecosound.core.tools.resample_1D_array(
                minigram.axis_frequencies,
                spectrum,
                resolution=resolution_freq,
                kind=interp)
            peak_amp.append(max(spectrum2))
            peak_f.append(axis_f[np.where(spectrum2 == peak_amp[-1])[0][0]])
            # median
            values_sum = np.sum(spectrum2)
            pct50 = 0.5 * values_sum
            values_cumsum = np.cumsum(spectrum2)
            pct50_location_idx = np.where(values_cumsum > pct50)[0][0]
            pct50_location_unit = axis_f[pct50_location_idx]  # feat
            median_f.append(pct50_location_unit)
            # entropy
            entropy_agg.append(ecosound.core.tools.entropy(spectrum))
            root4_magnitude.append(np.power(np.sum(spectrum2), 1/4))
        freq_peak = peak_f[np.where(peak_amp == max(peak_amp))[0][0]]  # feat
        freq_median_mean = np.mean(median_f)  # feat
        freq_median_std = np.std(median_f)  # feat
        freq_entropy_mean = np.mean(entropy_agg)  # feat
        freq_entropy_std = np.std(entropy_agg)  # feat
        # Upsweep mean/fraction
        freq_median_delta = np.subtract(median_f[1:], median_f[0:-1])
        upsweep_mean = np.mean(freq_median_delta)  # feat
        upsweep_fraction = len(np.where(freq_median_delta >= 0)[0]) / len(freq_median_delta)  # feat
        # SNR
        sig = np.amax(spectro)
        noise = np.percentile(spectro, 25)
        if noise > 0:
            snr = 10*np.log10(sig/noise)
        else:
            snr = 10*np.log10(sig) #feat
        # FM features
        # med_freq_offset = np.dot((median_f -  np.mean(median_f)),root4_magnitude)
        # gather all feature into DataFrame
        features = pd.DataFrame({
            'freq_peak': [freq_peak],
            'freq_median_mean': [freq_median_mean],
            'freq_median_std': [freq_median_std],
            'freq_entropy_mean': [freq_entropy_mean],
            'freq_entropy_std': [freq_entropy_std],
            'freq_upsweep_mean': [upsweep_mean],
            'freq_upsweep_fraction': [upsweep_fraction],
            'snr': [snr],
            })
        frequency_points = pd.DataFrame({
            'axis_times': [minigram.axis_times+adjusted_bounds[0]],
            'freq_median': [median_f],
            'freq_peak': [peak_f],
            })
        return features, frequency_points

    def _get_envelops(self, minigram, normalize=False):
        envelop_freq = np.sum(minigram.spectrogram, axis=1)
        envelop_time = np.sum(minigram.spectrogram, axis=0)
        if normalize:
            envelop_freq = envelop_freq/sum(envelop_freq)
            envelop_time = envelop_time/sum(envelop_time)
        return envelop_time, envelop_freq

    def plot_envelop_features(self, axis_orig, envelop_orig, axis_interp, envelop_interp, features, title):
        # plot - for debuging
        fig, ax = plt.subplots(1, 2, constrained_layout=True)
        ax[0].plot(axis_interp, envelop_interp, '.r')
        ax[0].plot(axis_orig, envelop_orig, '.g')
        ax[0].legend(['Interpolated', 'Original'])
        ax[0].grid()
        table = ax[1].table(cellText=features.values.T,
                            rowLabels=features.columns,
                            loc='center',
                            colWidths=[0.8,0.4])
        table.set_fontsize(20)
        ax[1].axis('off')
        fig.suptitle(title)
        fig.patch.set_visible(False)

    def plot_spectrogram_features(self, minigram, features, adjusted_bounds, frequency_points, title=''):
        # plot - for debuging
        fig, ax = plt.subplots(1, 2, constrained_layout=True)
        ax[0].pcolormesh(minigram.axis_times,
                         minigram.axis_frequencies,
                         minigram.spectrogram,
                         cmap = 'jet',
                         vmin = np.percentile(minigram.spectrogram,50),
                         vmax= np.percentile(minigram.spectrogram,99.9)
                         )
        # ax[0].grid()
        ax[0].add_patch(Rectangle((adjusted_bounds[0], adjusted_bounds[2]),
                                  adjusted_bounds[1]-adjusted_bounds[0],
                                  adjusted_bounds[3]-adjusted_bounds[2],
                                  linewidth=2,
                                  edgecolor='white',
                                  facecolor='white',
                                  fill=False,
                                  alpha=0.8,
                                  )
                        )
        ax[0].plot(frequency_points['axis_times'].values[0],
                   frequency_points['freq_median'].values[0],
                   'xr')
        ax[0].plot(frequency_points['axis_times'].values[0],
                   frequency_points['freq_peak'].values[0],
                   'xk')
        ax[0].legend(['Median frequency', 'Peak frequency'])
        table = ax[1].table(cellText=features.values.T,
                            rowLabels=features.columns,
                            loc='center',
                            colWidths=[0.8,0.4]
                            )
        table.set_fontsize(20)
        ax[1].axis('off')
        fig.suptitle(title)
        fig.patch.set_visible(False)

    def envelop_features(self, axis, values):
        # duration/width
        length = axis[-1] # feat
        # peak
        peak_value = np.amax(values)
        peak_location_unit = axis[np.where(values == peak_value)][0]  # feat
        peak_location_relative = (peak_location_unit/length)*100  # feat
        # quartiles
        values_sum = np.sum(values)
        pct25 = 0.25 * values_sum
        pct50 = 0.5 * values_sum
        pct5 = 0.05 * values_sum
        pct95 = 0.95 * values_sum
        values_cumsum = np.cumsum(values)
        pct50_location_idx = np.where(values_cumsum > pct50)[0][0]
        pct50_location_unit = axis[pct50_location_idx] # feat
        pct75_location_unit = axis[np.where(values_cumsum > values_cumsum[pct50_location_idx]+pct25)][0] # feat
        pct25_location_unit = axis[np.where(values_cumsum > values_cumsum[pct50_location_idx]-pct25)][0] # feat
        inter_quart_range = pct75_location_unit - pct25_location_unit # feat
        asymmetry = (pct25_location_unit + pct75_location_unit-(2*pct50_location_unit))/(pct25_location_unit+pct75_location_unit) # feat
        pct5_location_unit = axis[np.where(values_cumsum > pct5)][0]  # feat
        pct95_location_unit = axis[np.where(values_cumsum > pct95)][0]  # feat
        length_90 = pct95_location_unit - pct5_location_unit  # feat
        # concentration
        sort_idx = np.argsort(-values)
        values_sorted = values[sort_idx]
        axis_sorted = axis[sort_idx]
        values_sorted_cumsum = np.cumsum(values_sorted)
        idx_pct50 = np.where(values_sorted_cumsum > pct50)[0][0]
        unit_min = np.min(axis_sorted[0:idx_pct50])
        unit_max = np.max(axis_sorted[0:idx_pct50])
        concentration_unit = unit_max - unit_min  # feat
        # other stats
        std = np.std(values)  # feat
        kurt = kurtosis(values)  # feat
        skewness = skew(values)  # feat
        # entropy
        aggregate_entropy = ecosound.core.tools.entropy(values)
        # flatness - spectral flatness (0: tone, 1: white noise) (see seewave)
        flatness = gmean(values+1)/np.mean(values+1)
        # roughness or total curvature of a curve
        values_norm = values/max(values)
        deriv2 = ecosound.core.tools.derivative_1d(values_norm,order=2)
        roughness = np.sum(np.power(deriv2, 2))
        # Centroid
        centroid_unit = np.dot(axis, values) / np.sum(values)  # feat
        centroid_relative = (centroid_unit / length)*100  # feat
        # gather all feature into DataFrame
        features = pd.DataFrame({
            'peak_location': [peak_location_unit],
            'peak_location_relative': [peak_location_relative],
            'length': [length],
            'length_90': [length_90],
            'pct5_location': [pct5_location_unit],
            'pct25_location': [pct25_location_unit],
            'pct50_location': [pct50_location_unit],
            'pct75_location': [pct75_location_unit],
            'pct95_location': [pct95_location_unit],
            'IQR': [inter_quart_range],
            'asymmetry': [asymmetry],
            'concentration': [concentration_unit],
            'std': [std],
            'kurtosis': [kurt],
            'skewness': [skewness],
            'entropy': [aggregate_entropy],
            'flatness': [flatness],
            'roughness': [roughness],
            'centroid': [centroid_unit],
            'centroid_relative': [centroid_relative],
            })
        return features