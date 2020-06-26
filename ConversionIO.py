import glob, os, sys
import numpy as np
from scipy.io import netcdf
from netCDF4 import Dataset
from datetime import datetime
import h5py

## TODO: Add support for reading other file types
class Extract:
    """
    Extract Content from Hierarchical Data Files.
    ---
    Methods:
    get_date,
    get_date_range,
    get_data_from_path,
    read_nc4.
    """
    def __init__(self, input_dir, in_contents_name, exp):
        """
        Sets Class Attributes.
        ---
        input_dir: <str> Directory for the data files,
        in_contents_name: <str> Name of the file containing the data file names,
        exp: <str> Expression used to extract the date from file name.
        ---
        Return: None.
        """
        self.input_dir = input_dir
        self.in_contents_name = in_contents_name
        self.dir_list = os.path.join(input_dir, in_contents_name)
        self.exp = exp
        # store all files in a class list attribute
        with open(self.dir_list, 'r') as f:
            self.files = [i.strip() for i in f.readlines()]

    def get_date(self, nc4_fname):
        """
        Extract the date from a single file name.
        ---
        nc4_fname: <str> Name of the data file containing a date in format '%Y%m%d'.
        ---
        Return: <str '%Y%m%d'> Date. ex:'202006024'
        """
        date = datetime.strptime(nc4_fname[:len(self.exp)+2], self.exp).strftime('%Y%m%d')
        return date

    def get_date_range(self):
        """
        Extract the dates from all files in the input directory.
        ---
        Return: <array ['%Y%m%d', ...]> Sorted dates. ex: ['202006024', ...]
        """
        date_range = list(set([self.get_date(i) for i in self.files]))
        return sorted(date_range)

    def get_data_from_path(self, date=None):
        """
        Get a list of all files within a subdirectory with a date filter.
        ---
        date: <str '%Y%m%d'> (optional) Filters files with provided date.
        ---
        Return: <array ['filename', ...]> Sorted list of files.
        """
        # support date specific filter
        if date is None:
            return sorted(self.files), len(self.files)
        else:
            files = []
            for i in self.files:
                if date == self.get_date(i):
                    files.append(i)
            return sorted(files), len(files)

    def read_nc4(self, datasets, nc4_fname):
        """
        Traverse depthwise through heirarchical file (nc4, HDF5).
        ---
        datasets: <dictionary {'var':['dir', 'dir', ..], ...}>
                  Dict containing variable names and the corresponding paths
                  to access the *numerical array dataset,
        nc4fnmae: <str> Name of the data file.
        ---
        Return: <dictionary {'var':np.array, ...}>
                Dict containing variable names and the correspoding requested
                datasets as a numpy array.
        """
        file = os.path.join(self.input_dir, nc4_fname)
        # open file and extract read to np array
        h4_data = Dataset(file)
        # create dictionary to store the requested data
        res = {}
        # support depth access
        for ds_name, dataset in datasets.items():
            dataset.reverse()
            ds = h4_data[dataset.pop()]
            while len(dataset) > 0:
                ds = ds[dataset.pop()]
            ds = np.array(ds)
            res.update({ds_name: ds})
        # close dataset
        h4_data.close()

        return res


class WriteFile:
    """
    Write Data to Different Types of Files
    ---
    Methods:
    netcdf
    write_file_paths
    """
    def __init__(self, output_dir, out_contents_name, var_name, long_name, units, out_file_prefix):
        """
        Sets Class Attributes.
        ---
        output_dir: <str> Directory for the converted data files,
        out_contents_name: <str> Name of the file that will contain the converted data file names,
        var_name: <str> Name used to store the data variable for extracted array,
        long_name: <str> Descriptive longer name to specify var_name,
        units: <str> Units of the data - to be stored in the output nc4 file,
        out_file_prefix: <str> Naming convention for the converted data files.
        ---
        Return: None.
        """
        self.output_dir = output_dir
        self.out_contents_name = out_contents_name
        self.var_name = var_name
        self.long_name = long_name
        self.units = units
        self.out_file_prefix = out_file_prefix

    def netcdf(self, idate, extracted_data, lats, lons, isif):
        """
        Write an array of data with spatial attributes into an nc4 file.
        ---
        idate: <str> Date used to extend naming convention,
        extracted_data: <np.array> Array containing the data that needs to be written,
        lats: <np.array> Array containing latitude data, used to create a dimension,
        lons: <np.array> Array containing longitude data, used to create a dimension,
        isif: <tuple> Size of the extracted_data.
        ---
        Return: <str> Name of outfile.
        *Creates all the files in output directory with specified names.
        """
        # define file path and open using netcdf
        outfile = os.path.join(self.output_dir, self.out_file_prefix+idate+'.nc4')
        fid = netcdf.netcdf_file(outfile, 'w')

        # creating latitude and longitude dimensions
        fid.createDimension('longitude', isif[1])
        fid.createDimension('latitude', isif[0])

        # creating the longitude variable
        nc_var = fid.createVariable('nlat', 'f4', ('latitude',))
        nc_var[:] = lats
        nc_var.long_name = 'latitude'
        nc_var.standard_name = 'latitude'
        nc_var.units = 'degrees_north'

        # creating the latitude variable
        nc_var = fid.createVariable('nlon', 'f4', ('longitude',))
        nc_var[:] = lons
        nc_var.long_name = 'longitude'
        nc_var.standard_name = 'longitude'
        nc_var.units = 'degrees_east'

        # creating the statistic variable
        nc_var = fid.createVariable(self.var_name, 'f4', ('latitude','longitude',))
        nc_var[:] = extracted_data
        nc_var.long_name = self.long_name
        nc_var.units = self.units

        fid.close()

        return outfile

    def write_file_paths(self, content_paths):
        """
        Write the names of all converted files to a file.
        ---
        Return: None.
        *Creates a file with specified out_contents_name in the output directory.
        """
        out_file_path = os.path.join(self.output_dir, self.out_contents_name)
        with open(out_file_path, 'a') as f:
            f.writelines(content_paths)
