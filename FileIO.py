from netCDF4 import Dataset
import tempfile
import os
import numpy as np
from osgeo import gdal, osr
import rasterio
import h5py

class InputFile:
    def __init__(self, data_path, name):
        self.filename = os.path.join(data_path, name)
        self.N_lon = None
        self.N_lat = None
        self.x_min = None
        self.y_min = None

    def read(self):
        pass

    def genTif(self, data, resolution):
        assert self.N_lon != None
        tf = tempfile.NamedTemporaryFile()
        spei_ds = gdal.GetDriverByName('Gtiff').Create(tf.name, self.N_lon, self.N_lat, 1, gdal.GDT_Float32)
        # create a temporary TIFF file
        spei_ds.FlushCache()

        # 3.4 set the range of image visualization
        geotransform = (self.x_min, resolution[0], 0, self.y_min, 0, resolution[1])
        spei_ds.SetGeoTransform(geotransform)

        # coordinates information
        srs = osr.SpatialReference()
        srs.ImportFromEPSG(4326)
        spei_ds.SetProjection(srs.ExportToWkt())

        # 3.6 output data
        spei_ds.GetRasterBand(1).WriteArray(data)
        spei_ds.FlushCache()
        spei_ds = None

        rasterdata = rasterio.open(tf.name)
        return rasterdata


class HE5(InputFile):
    def __init__(self, data_path, name):
        super().__init__(data_path, name)
        self.N_lon = 1440
        self.N_lat = 720
        self.y_min = -90
        self.x_min = -180

    def read(self, dataset):
        """
        Returns a (720, 1440) Matrix containing requested data
        ---
        he5_filename: path to he5 file
        dataset: requested data
        options: ColumnAmountNO2, ColumnAmountNO2CloudScreened,
                 ColumnAmountNO2Trop, ColumnAmountNO2TropCloudScreened,
                 Weight
        ---
        Output Numpy Array
        """
        print(self.filename)
        with h5py.File(self.filename, "r") as f:
            ds = np.array(f['HDFEOS']['GRIDS']['ColumnAmountNO2']['Data Fields'][dataset])
        return ds


class NC4(InputFile):
    def read(self, dataset):
        h4_data = Dataset(self.filename)
        ds = np.array(h4_data[dataset][:])
        lats = np.array(h4_data['nlat'][:])
        lons = np.array(h4_data['nlon'][:])
        self.x_min = lons.min()
        self.y_min = lats.min()
        self.N_lat = len(lats)
        self.N_lon = len(lons)

        h4_data.close()
        return ds


class OutputFile:
    def __init__(self, csvs_dir, shp_dir_name, env_name, datatype, observation_date):
        env_fname = datatype.name if datatype.name != '' else env_name
        self.save_path = os.path.join(csvs_dir, shp_dir_name, env_name, datatype.name, "")
        self.fname = observation_date + '_' + env_fname + '.csv'
        print(f'Making directories: {self.save_path}')
        os.makedirs(self.save_path, exist_ok=True)

    def save(self, data):
        path = os.path.join(self.save_path, self.fname)
        print(path)
        print(' CSVFile is saving  ', path)
        np.savetxt(path, data, delimiter=',', fmt='%s')
