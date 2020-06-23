import os
import numpy as np
from datetime import datetime
from pathlib import Path
from Shapefile import *
from FileIO import *

class EnvironmentFactor:
    def __init__(self, name, data_directory, date_format, arr_data_types):
        self.name = name
        self.data_directory = data_directory
        self.date_format = date_format
        self.data_types = arr_data_types

    def process(self, file_list, shapefiles_dir, output_dir):
        """
        Creates CSV file with requested data
        ---
        datatype: The DataType object to be used
        shapefiles_dir: Directory containing all shape files
        ---
        Returns None
        """
        for datatype in self.data_types:
            for data_file in file_list:
                data_file = str(data_file)
                original_filename = os.path.basename(data_file)
                cut_fname = original_filename[:len(self.date_format)+2]
                observation_date = datetime.strptime(cut_fname, self.date_format).strftime('%Y%m%d')
                try:
                    input_file = HE5(self.data_directory, original_filename)
                    if ('nc4' in data_file):
                        input_file = NC4(self.data_directory, original_filename)
                    data = input_file.read(datatype.ds_name)
                except Exception as e:
                    print(e)
                    continue

                rasterdata = input_file.genTif(data, datatype.resolution)

                for shpfile in Path(shapefiles_dir).rglob('*.shp'):
                    shapefile = Shapefile(shapefiles_dir, shpfile.name)
                    csvfile = shapefile.read_shape_file(datatype, rasterdata, data)
                    csvfile = np.array(csvfile)

                    output = OutputFile(output_dir, shapefile.getDirName(), self.name, datatype, observation_date)
                    output.save(csvfile)

                del rasterdata


class DataType:
    def __init__(self, ds_name, resolution=(0.25, 0.25), name=''):
        self.name = name
        self.ds_name = ds_name
        self.resolution = resolution

    def toString(self):
        print(f'NAME: {self.name}')
        print(f'DATASET NAME: {self.ds_name}')
        print(f'RESOLUTION: {self.resolution}')
