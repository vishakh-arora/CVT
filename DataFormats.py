import numpy as np
import os
from tqdm import tqdm
from types import SimpleNamespace
from copy import deepcopy

class AbstractDataFormatInit():
    """
    Abstract class that contains the Extractor and Writer Objects from ConversionIO.
    ---
    Methods:
    None.
    """
    def __init__(self, Extractor, Writer):
        self.Extractor = Extractor
        self.Writer = Writer


class TempHumid(AbstractDataFormatInit):
    """
    Processor for Temperature & Humidity Data Formats.
    ---
    Methods:
    process.
    """
    def process(self, datasets):
        """
        Uses parent classes to create averaged daily files.
        ---
        datasets: <dictionary {'var':['dir', 'dir', ..], ...}>
                  Dict containing variable names and the corresponding paths
                  to access the *numerical array dataset.
        ---
        Return: None.
        *Creates all the files in output directory with specified names.
        """
        # new file paths
        content_paths = []

        # create list of file paths
        files, n_files = self.Extractor.get_data_from_path()

        # extract appropriate
        for i in tqdm(range(n_files), desc=f'Processing {self.Writer.var_name}'):
            dtemp = deepcopy(datasets)

            try:
                file_current = files[i]
                path = os.path.join(self.Extractor.input_dir, file_current)

                dres = SimpleNamespace(**self.Extractor.read_nc4(dtemp, file_current))
                data_hourly = dres.data_hourly
                lats = dres.lats
                lons = dres.lons

            except OSError:
                continue

            # find average
            average_data_day = np.nanmean(data_hourly, axis=0)
            isif = average_data_day.shape

            # write out the nc4
            outfile = self.Writer.netcdf(self.Extractor.get_date(file_current).strftime("%Y%m%d"), average_data_day, lats, lons, isif)
            content_paths.append(outfile+'\n')

        # write resultant files
        self.Writer.write_file_paths(content_paths)
        print('New Files Logged.')


class Precipitation(AbstractDataFormatInit):
    """
    Processor for Precipitation Data Formats.
    ---
    Methods:
    process.
    """
    def process(self, datasets):
        """
        Uses parent classes to create averaged daily files.
        ---
        datasets: <dictionary {'var':['dir', 'dir', ..], ...}>
                  Dict containing variable names and the corresponding paths
                  to access the *numerical array dataset.
        ---
        Return: None.
        *Creates all the files in output directory with specified names.
        """
        # get date range for files, data files given for multiple parts of day
        date_range = self.Extractor.get_date_range()

        # new file paths
        content_paths = []

        # iterate through date range and create list of file paths
        for date in date_range:
            files, n_files = self.Extractor.get_data_from_path(date=date)
            data_day =  []

            # print(f'Processing Data for {date}...')

            # extract appropriate
            for i in tqdm(range(n_files), desc=f'Processing {self.Writer.var_name} | {date}'):
                dtemp = deepcopy(datasets)

                try:
                    file_current = files[i]
                    path = os.path.join(self.Extractor.input_dir, file_current)

                    dres = SimpleNamespace(**self.Extractor.read_nc4(dtemp, file_current))
                    data_sub = np.transpose(dres.data_sub.squeeze())
                    lats = dres.lats
                    lons = dres.lons

                    isif = data_sub.shape

                    data_day.append(data_sub)
                except OSError:
                    # print(f'Error: {e} when processing {file_current}.')
                    continue

            # print('Saving...')

            # calculate average
            data_day = np.array(data_day)
            average_data_day = np.nanmean(data_day, axis=0)

            # write out the nc4
            outfile = self.Writer.netcdf(date.strftime("%Y%m%d"), average_data_day, lats, lons, isif)
            content_paths.append(outfile+'\n')

        # write resultant files
        self.Writer.write_file_paths(content_paths)
        print('New Files Logged.')
