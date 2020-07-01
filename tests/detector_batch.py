# -*- coding: utf-8 -*-
"""
Created on Fri May  8 15:54:29 2020

@author: xavier.mouy
"""
import sys
sys.path.append("..")  # Adds higher directory to python modules path.
from ecosound.core.audiotools import Sound
from ecosound.core.spectrogram import Spectrogram
from ecosound.core.annotation import Annotation
from ecosound.detection.detector_builder import DetectorFactory
from ecosound.visualization.grapher_builder import GrapherFactory
from ecosound.measurements.measurer_builder import MeasurerFactory
import ecosound.core.tools
import time
import os
import platform
# from dask.distributed import Client, LocalCluster
# cluster = LocalCluster()
# client = Client(cluster,processes=False)

    
def run_detector(infile, outdir, deployment_file=None):
    ## Input paraneters ##########################################################   
    
    
    # Spectrogram parameters
    frame = 0.0625 #3000
    nfft = 0.0853 # 4096
    step = 0.01 # 5
    fmin = 0
    fmax = 1000
    window_type = 'hann'

    # start and stop time of wavfile to analyze
    #t1 = 0 # 24
    #t2 = 60 # 40
    ## ###########################################################################
    outfile = os.path.join(outdir, os.path.split(file)[1]+'.nc')
    
    if os.path.exists(outfile) is False:
        # load audio data
        sound = Sound(infile)
        #sound.read(channel=0, chunk=[t1, t2], unit='sec')
        sound.read(channel=0, unit='sec')
        # Calculates  spectrogram
        spectro = Spectrogram(frame, window_type, nfft, step, sound.waveform_sampling_frequency, unit='sec')
        spectro.compute(sound, dB=True, use_dask=True, dask_chunks=40)
        # Crop unused frequencies
        spectro.crop(frequency_min=fmin, frequency_max=fmax, inplace=True)
        # Denoise
        spectro.denoise('median_equalizer',
                        window_duration=3,
                        use_dask=True,
                        dask_chunks= 'auto',#(87,10000),
                        inplace=True)
        # Detector
        file_timestamp = ecosound.core.tools.filename_to_datetime(infile)[0]
        detector = DetectorFactory('BlobDetector',
                                   kernel_duration=0.1,
                                   kernel_bandwidth=300,
                                   threshold=10,
                                   duration_min=0.05,
                                   bandwidth_min=40)
        detections = detector.run(spectro,
                                  start_time=file_timestamp,
                                  use_dask=True,
                                  dask_chunks='auto',
                                  debug=False)
        # Maasurements
        spectro_features = MeasurerFactory('SpectrogramFeatures', resolution_time=0.001, resolution_freq=0.1, interp='linear')
        measurements = spectro_features.compute(spectro,
                                                detections,
                                                debug=False,
                                                verbose=False,
                                                use_dask=False)
        
        # Add metadata
        if deployment_file:
            measurements.insert_metadata(deployment_file)
        
        # Add file informations
        file_name = os.path.splitext(os.path.basename(infile))[0]
        file_dir = os.path.dirname(infile)
        file_ext = os.path.splitext(infile)[1]
        measurements.insert_values(operator_name=platform.uname().node,
                                   audio_file_name=file_name,
                                   audio_file_dir=file_dir,
                                   audio_file_extension=file_ext,
                                   audio_file_start_date= ecosound.core.tools.filename_to_datetime(infile)[0]
                                   )
    
        measurements.to_netcdf(outfile)
    else:
        print('Recording already processed.')


indir = r'C:\Users\xavier.mouy\Documents\PhD\Projects\Dectector\datasets\ONC_delta-node_2014\audio_data'
outdir=r'C:\Users\xavier.mouy\Documents\PhD\Projects\Dectector\results\Full_dataset_with_metadata2'
ext='.wav'
deployment_file = r'C:\Users\xavier.mouy\Documents\PhD\Projects\Dectector\datasets\ONC_delta-node_2014\deployment_info.csv'
files = ecosound.core.tools.list_files(indir,
                                        ext,
                                        recursive=False,
                                        case_sensitive=True)

for idx,  file in enumerate(files):
    print(str(idx)+r'/'+str(len(files))+': '+ file)
    # try:
    #     tic = time.perf_counter()
    #     run_detector(file, outdir, deployment_file=deployment_file)
    #     toc = time.perf_counter()
    # except:
    #     print('ERROR HERE --------------------------------------')
        
    tic = time.perf_counter()
    run_detector(file, outdir, deployment_file=deployment_file)
    toc = time.perf_counter()

            
    print(f"Executed in {toc - tic:0.4f} seconds")

