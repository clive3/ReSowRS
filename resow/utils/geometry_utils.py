import os
import ast
import math
import numpy as np
from osgeo import gdal
from geopandas import read_file
from pyproj import Proj
from shapely import geometry
from skimage.morphology import remove_small_objects, remove_small_holes, \
    disk, erosion

from resow.utils.print_utils import _printWarning, _printError
from resow.utils.name_utils import _hansenFilePath, _seaMaskFilePath


def readGeotiff(image_file_path):

    ## import the input file and its geometry
    image_dataset_gdal = gdal.Open(image_file_path, gdal.GA_ReadOnly)
    if image_dataset_gdal:

        projection = image_dataset_gdal.GetProjectionRef()
        geotransform = image_dataset_gdal.GetGeoTransform()
        image_array_np = image_dataset_gdal.ReadAsArray()

        if len(image_array_np.shape) == 2:
            image_array_np = np.expand_dims(image_array_np, axis=0)

    else:
        _printWarning(f'image file could not be read: {image_file_path}')
        image_array_np = projection = geotransform = None

    return image_array_np, (projection, geotransform)


def writeGeotiff(image_array_np, output_file_path, image_geometry):

    driver = gdal.GetDriverByName('GTiff')
    # driver.QuietDelete (output_file_path)

    if len(image_array_np.shape) == 2:
        image_array_np = np.expand_dims(image_array_np, axis=0)
    (num_bands, y_size, x_size) = image_array_np.shape

    output_ds = driver.Create(output_file_path, xsize=x_size, ysize=y_size,
                              bands=num_bands, eType=gdal.GDT_Float32)

    if not output_ds:
        _printError(f'driver for file : {output_file_path} cannot be created')

    else:
        output_ds.SetProjection(image_geometry[0])
        output_ds.SetGeoTransform(image_geometry[1])

        for band in range(num_bands):

            if len(image_array_np.shape) == 3:
                output_ds.GetRasterBand(band + 1).WriteArray(image_array_np[band])

            elif len(image_array_np.shape) == 2:
                output_ds.GetRasterBand(band + 1).WriteArray(image_array_np)

            else:
                _printWarning(f'cannot write the file: {output_file_path}')

        output_ds.FlushCache()
        output_ds = None


def createSeaMask(median_dir_path, site_name, SMALL_OBJECT_SIZE):

    hansen_np, geometry = readGeotiff(_hansenFilePath(median_dir_path, site_name))
    hansen_np = np.squeeze(hansen_np)

    water_mask_np = np.where(hansen_np == 1, 0, 1)
    water_mask_np = remove_small_holes(remove_small_objects(water_mask_np, SMALL_OBJECT_SIZE),
                                       SMALL_OBJECT_SIZE)

    land_mask_np = np.where(water_mask_np == 0, 1, 0)

    footprint = disk(100)
    water_mask_np = erosion(water_mask_np, footprint)
    sea_mask_file_path = _seaMaskFilePath(median_dir_path, site_name)
    writeGeotiff(water_mask_np, sea_mask_file_path, geometry)

    land_mask_file_path = sea_mask_file_path.replace('sea', 'land')
    writeGeotiff(land_mask_np, land_mask_file_path, geometry)


def applySeaMask(median_dir_path):

    sea_mask_np, geometry = readGeotiff(os.path.join(_seaMaskFilePath(median_dir_path)))


def polygon_from_geojson(hexgrid_filepath, OUTPUT_EPSG):
    """
    Extracts coordinates from a geojson file in format required
    by gee.

    :param geojson_filepath: path to the geojson file
    :type geojson_filepath: ``str``

    :return: WKT Polygon
    :rtype: ``str``

    """

    proj_image = Proj(init=f'epsg:{OUTPUT_EPSG}')

    hexgrid_df = read_file(hexgrid_filepath)
    west = int(hexgrid_df['west'].values[0])
    east = int(hexgrid_df['east'].values[0])
    north = int(hexgrid_df['north'].values[0])
    south = int(hexgrid_df['south'].values[0])

    west_4326, north_4326 = proj_image(west, north, inverse=True)
    east_4326, south_4326 = proj_image(east, south, inverse=True)

    grid_size = int((west - east)*(south - north)/100)
    print(f'grid area: {grid_size} pixels, {math.sqrt(grid_size)}')

    polygon = f'[[[{west_4326:.3f}, {south_4326:.3f}], ' + \
                f'[{east_4326:.3f}, {south_4326:.3f}], ' + \
                f'[{east_4326:.3f}, {north_4326:.3f}], ' + \
                f'[{west_4326:.3f}, {north_4326:.3f}], ' + \
                f'[{west_4326:.3f}, {south_4326:.3f}]]]'

    return ast.literal_eval(polygon)
