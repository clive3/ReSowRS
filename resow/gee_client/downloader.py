import os
import ee
import numpy as np
from zipfile import ZipFile
from urllib.request import urlretrieve

from resow._utils.print_utils import _printProgress, _printError
from resow._utils.name_utils import _geotiffFileName, _hansenFilePath
from resow._utils.file_system_utils import _saveMetadata
from resow.gee_client.gee import GEES2Downloader

def downloadMedianS2GEEImage(site_name, roi_polygon, date_pair, images_dir_path,
                             EPSG, BANDS, SCALE, MASK_LAND, NIR_LAND_THRESH,
                             MAX_CLOUD_PROBABILITY):
    """Connects to GEE and downloads a median composite image.
    """

    ee.Initialize()
    _printProgress('... connected to GEE')

    ee_region = ee.Geometry.Polygon(coords=roi_polygon, proj='EPSG:4326')
    date_start, date_end = date_pair[0], date_pair[1]
    ee_scale = ee.Number(SCALE)

    ee_image_median, number_images = getMedianGEEImage(ee_region, date_pair,
                                                       EPSG, ee_scale,
                                                       MASK_LAND, NIR_LAND_THRESH,
                                                       MAX_CLOUD_PROBABILITY, BANDS)

    image_filename = _geotiffFileName(site_name, date_start, date_end, SCALE, MASK_LAND)
    DOWNLOAD_FILENAME = 'gee_image'
    download_filepath = os.path.join(images_dir_path, DOWNLOAD_FILENAME+'.tif')
    image_filepath = os.path.join(images_dir_path, image_filename)

    downloadGEEImage(image=ee_image_median,
                     name=DOWNLOAD_FILENAME,
                     ee_scale=ee_scale,
                     ee_region=ee_region,
                     bands=BANDS,
                     directory_path=images_dir_path,
                    )

    try:
        os.rename(download_filepath, image_filepath)
    except:
        os.remove(image_filepath)
        os.rename(download_filepath, image_filepath)

    _printProgress(f'... median S2 composite from {number_images} images downloaded')

    metadata_filepath = image_filepath.replace('tif', 'txt')
    _saveMetadata(metadata_filepath, date_pair, EPSG, number_images)
    _printProgress('... metadata saved')

    hansen_filepath = _hansenFilePath(images_dir_path, site_name)
    downloadGEEImage(image=ee.Image('UMD/hansen/global_forest_change_2015')\
                           .reproject(crs=f'EPSG:{EPSG}', scale=ee_scale),
                     name=DOWNLOAD_FILENAME,
                     ee_scale=ee_scale,
                     ee_region=ee_region,
                     bands='datamask',
                     directory_path=images_dir_path,
                    )

    try:
        os.rename(download_filepath, hansen_filepath)
    except:
        os.remove(hansen_filepath)
        os.rename(download_filepath, hansen_filepath)
    _printProgress('... hansen2015 downloaded')

    _printProgress('... GEE connection closed')


def downloadGEEImage(image, name, ee_scale, ee_region, bands, directory_path):

    path = image.getDownloadURL({
        'name': name,
        'scale': ee_scale,
        'region': ee_region,
        'filePerBand': False,
        'bands': bands
    })

    image_zip_filepath, _ = urlretrieve(path)
    with ZipFile(image_zip_filepath) as local_zipfile:
        return local_zipfile.extractall(directory_path)


def getMedianGEEImage(ee_region, dates, EPSG, ee_scale, MASK_LAND,
                      NIR_LAND_THRESH, MAX_CLOUD_PROBABILITY, BANDS):


    _printProgress(f'... calculating median image')

    def maskClouds(ee_image):
        clouds = ee.Image(ee_image.get('S2SR_joined_cloudprob')).select('probability')
        is_not_cloud = clouds.lt(MAX_CLOUD_PROBABILITY)
        return ee_image.updateMask(is_not_cloud)

    def maskLand(ee_image):
        NIR = ee.Image(ee_image.select('B8'))
        is_not_land = NIR.lt(NIR_LAND_THRESH*1000)
        return ee_image.updateMask(is_not_land)

    S2SR_col = ee.ImageCollection('COPERNICUS/S2_SR')\
                                   .filterBounds(ee_region)\
                                   .filterDate(dates[0], dates[1])

    S2_cloud_prob_col = ee.ImageCollection(
        'COPERNICUS/S2_CLOUD_PROBABILITY')\
        .filterBounds(ee_region)\
        .filterDate(dates[0], dates[1])

    S2SR_cloud_masked_col = ee.ImageCollection(
        ee.Join.saveFirst('S2SR_joined_cloudprob')\
            .apply(**{'primary': S2SR_col,
            'secondary': S2_cloud_prob_col,
            'condition': ee.Filter.equals(**{
            'leftField': 'system:index',
            'rightField': 'system:index'})})).map(maskClouds)

    image_list = S2SR_cloud_masked_col.toList(500)
    number_images = len(image_list.getInfo())

 #   if MASK_LAND:
 #       S2SR_cloud_masked_col = S2SR_cloud_masked_col.map(maskLand)

    image_median = S2SR_cloud_masked_col.median() \
        .reproject(crs=f'EPSG:{EPSG}', scale=ee_scale)


    return image_median, number_images


def test():
    """xmin = ee.Number(270000)
    ymin = ee.Number(330000)
    xmax = ee.Number(220000)
    ymax = ee.Number(380000)

    bl = ee.Geometry.Point([xmin, ymin])
    br = ee.Geometry.Point([xmax, ymin])
    tl = ee.Geometry.Point([xmin, ymax])
    tr = ee.Geometry.Point([xmax, ymax])

    bgs = ee.Projection('EPSG:27700')

    bbox_coords = ee.List([bl, br, tr, tl, bl])
    ee_region = ee.Geometry.Polygon(coords=bbox_coords, proj=bgs, evenOdd=False)

    ee_region = ee.Geometry.Rectangle(coords=[-76.5, 2.0, -74, 4.0], geodesic=False)"""

#    ee_region = ee.Geometry(roi_polygon)

    aoi = ee.Geometry.Point([-6, 49.9])
    aoi = ee.Geometry.Point([-5.09, 53.07])
    S2SR_col = ee.ImageCollection('COPERNICUS/S2_SR')\
                                   .filterBounds(aoi)\
                                   .filterDate(date_start, date_end)\
                                   .select(BANDS)

    ee_col_list = S2SR_col.toList(S2SR_col.size())
    coll_size = ee_col_list.size().getInfo()
    for band in BANDS:
        for i in range(coll_size):
#            image = ee.Image(ee_col_list.get(i)).reproject(crs=f'EPSG:{EPSG}', scale=ee_scale)
            image = ee.Image(ee_col_list.get(i))
            timedate_str = image.get('DATATAKE_IDENTIFIER').getInfo()[5:20]
            print(timedate_str)
            downloader = GEES2Downloader()
            downloader.download(img=image, band=band, scale=SCALE)
            np.save(f'd://data//resowrs//test2//{band}_{timedate_str}.npy', downloader.array)
    _printError('done')