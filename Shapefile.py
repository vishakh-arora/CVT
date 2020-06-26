import os
import geopandas as geopd
import numpy as np
from rasterio.mask import mask

class Shapefile:
    def __init__(self, path, name):
        self.name = name

        # Extract the shapefiles directory name from it's filename
        # USA_admin1.shp --> USA_admin1
        shp_dir_name = name.split('.')[0]
        if ('global_basemap' in name):
            attribute = 'iso3'
        else:
            attribute = 'HASC_' + shp_dir_name[-1]

        self.path = os.path.join(path, shp_dir_name, "")
        self.attribute = attribute

    def getDirName(self):
        return self.name.split('.')[0]

    def toString(self):
        print(f'PATH: {self.path}')
        print(f'NAME: {self.name}')
        print(f'ATTRIBUTE: {self.attribute}')

    def extractStats(self, values, shp_name, data_extremes):
        out_data = []

        for i in range(len(values)):
            for j in range(len(values[i])):
                if values[i][j] >= data_extremes[0] and values[i][j] <= data_extremes[1]:
                    out_data.append(values[i][j])

        values = np.array(out_data)
        if (len(values) == 0):
            return [shp_name, 0, 0, 0]

        maxes = values.max()
        means = values.mean()
        mins = values.min()

        return [shp_name, maxes, means, mins]

    def read_shape_file(self, datatype, rasterdata, data, minVal):
        """
        Read shapefile and clean contents
        ---
        shape_filename: path to shp file
        key_field_name: column name (e.g. GID_0, NAME_0, FIPS etc.)
        dataset: Numpy Array (720, 1440) containing the grid data
        temp_tiff: Temporary tiff dataset object for Rasterio compatibility
        ---
        Output Standard Array
        """
        # read shape file and create output template
        shp_data = geopd.GeoDataFrame.from_file(self.path + self.name)
        xy_values = [[self.attribute, 'Max', 'Mean', 'Min']]

        # delete errors
        if (minVal == None):
            min_data = data[~np.isnan(data)].min()
        else:
            min_data = minVal
        max_data = data[~np.isnan(data)].max()

        # loop through the shape data
        for i in range(len(shp_data)):

            # load the polygons into variables
            geo = shp_data.geometry[i]
            feature = [geo.__geo_interface__]

            # extract the requested column using the field name
            item_index = np.argwhere(shp_data.columns == self.attribute)[0][0]
            shp_name = shp_data.iloc[i][item_index]

            # apply raster mask
            out_image, out_transform = mask(rasterdata, feature, all_touched=True, crop=True, nodata=rasterdata.nodata)

            # extract values from out_image
            values = out_image.tolist()
            values = values[0]

            # add elements to output array
            xy_values.append(self.extractStats(values, shp_name, (min_data, max_data)))

        # remove loop variables
        del feature, shp_data

        return xy_values
