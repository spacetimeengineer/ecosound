# -*- coding: utf-8 -*-
"""
Created on Wed May  6 10:56:38 2020

@author: xavier.mouy
"""

import pandas as pd
import os

class DeploymentInfo():
    """
    A class to handle acoustic deployment metadadata .

    Object carrying deployment metadata that can be used for example to populate
    metadata fields in Annotation or Measurement objects.

    Attributes
    ----------
    data : pandas DataFrame
        DataFranme with deploymnent information.

    Methods
    -------
    write_template(filepath)
        Create an empty template csv file with the proper headers.
    read(filepath)
        Populates the DeploymentInfo object with the information from a csv
        file. The csv file must follow the samestructure as the one created by
        the method write_template.

    """

    def __init__(self):
        """
        Initialize object with empty .data attribute.

        Returns
        -------
        None.

        """
        self.data =[]

    def write_template(self, filepath):
        """
        Create a blank deployment file.

        Create an empty template csv file with the proper headers. The created
        csv file has only the headers and an operator must fill in all the
        deployment information manually. Once filled in, this file can be used
        by the DeploymentInfo.read method

        Parameters
        ----------
        filepath : str
            path and name of the deployment csv file to create.

        Returns
        -------
        None. Write a blank csv deployment file that an operator can fill in.

        """
        if os.path.isfile(filepath):
            raise ValueError('File already exists.')
        metadata = pd.DataFrame({
            'audio_channel_number': [],
            'UTC_offset': [],
            'sampling_frequency': [],
            'bit_depth': [],
            'mooring_platform_name': [],
            'recorder_type': [],
            'recorder_SN': [],
            'hydrophone_model': [],
            'hydrophone_SN': [],
            'hydrophone_depth': [],
            'location_name': [],
            'location_lat': [],
            'location_lon': [],
            'location_water_depth': [],
            'deployment_ID': [],
            'deployment_date':[],
            'recovery_date':[],
            })
        metadata.to_csv(filepath,
                        sep=',',
                        encoding='utf-8',
                        header=True,
                        index=False,
                        )

    def read(self, filepath):
        """
        Read metadata information from csv file.

        Load data from a csv file containing the deployment metadat information
        and populated the data attribute of the DeploymentInfo object. The csv
        file must follow the same headers and data format as the csv file
        template generated by DeploymentInfo.write_template.

        Parameters
        ----------
        filepath : str
            Path of the csv file to read.

        Returns
        -------
        None. Populates the pandas dataframe in teh .data attribute of the
        DeploymentInfo object.

        """
        df = pd.read_csv(filepath,
                         delimiter=',',
                         #header=None,
                         skiprows=0,
                         na_values=None,
                         )
        self.data = df
        return df

