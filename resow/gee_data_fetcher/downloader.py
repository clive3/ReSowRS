import os
import ee
import zipfile
from urllib.request import urlretrieve

from resow.utils.print_utils import _printProgress
from resow.utils.name_utils import _geotiffFileName, _hansenFilePath
from resow.utils.file_system_utils import _saveMetadata


def downloadMedianS2GEEImage(site_name, roi_polygon, date_pair, images_dir_path,
                             EPSG, BANDS, SCALE, MASK_LAND, NIR_LAND_THRESH,
                             MAX_CLOUD_PROBABILITY):
    """Connects to GEE and downloads a median composite image based on the
    parameters.
    """

    ee.Initialize()
    _printProgress('... connected to GEE')

# # ee.Geometry.Rectangle({coords: [-76.5, 2.0, -74, 4.0], geodesic: false})
#    ee_region = ee.Geometry(roi_polygon)
    ee_region = ee.Geometry.Polygon(coords=roi_polygon, proj='EPSG:4326')
    date_start, date_end = date_pair[0], date_pair[1]
    ee_scale = ee.Number(SCALE)

    ee_image_median, number_images = getMedianGEEImage(ee_region, date_pair,
                                                       EPSG, ee_scale,
                                                       MASK_LAND, NIR_LAND_THRESH,
                                                       MAX_CLOUD_PROBABILITY)

    image_metadata = ee_image_median.getInfo()
    image_epsg = image_metadata['bands'][0]['crs'][5:]

    image_filename = _geotiffFileName(site_name, date_start, date_end, SCALE, MASK_LAND)
    DOWNLOAD_FILENAME = 'gee_image'
    download_filepath = os.path.join(images_dir_path, DOWNLOAD_FILENAME+'.tif')
    image_filepath = os.path.join(images_dir_path, image_filename)

    downloadGEEImage(image=ee_image_median,
                     name=DOWNLOAD_FILENAME,
                     ee_scale=ee_scale,
                     ee_region=ee_region,
                     directory_path=images_dir_path,
                     bands=BANDS)

    try:
        os.rename(download_filepath, image_filepath)
    except:
        os.remove(image_filepath)
        os.rename(download_filepath, image_filepath)

    _printProgress(f'... median S2 composite from {number_images} images downloaded')

    metadata_filepath = image_filepath.replace('tif', 'txt')
    _saveMetadata(metadata_filepath, date_pair, image_epsg, number_images)
    _printProgress('... metadata saved')

    hansen_filepath = _hansenFilePath(images_dir_path, site_name)
    downloadGEEImage(image=ee.Image('UMD/hansen/global_forest_change_2015')\
                           .reproject(crs=f'EPSG:{EPSG}', scale=ee_scale),
                     name=DOWNLOAD_FILENAME,
                     ee_scale=ee_scale,
                     ee_region=ee_region,
                     directory_path=images_dir_path,
                     bands='datamask')

    try:
        os.rename(download_filepath, hansen_filepath)
    except:  # overwrite if already exists
        os.remove(hansen_filepath)
        os.rename(download_filepath, hansen_filepath)
    _printProgress('... hansen2015 downloaded')

    _printProgress('... GEE connection closed')

    return number_images, image_epsg


def downloadGEEImage(image, name, ee_scale, ee_region, directory_path, bands):

    path = image.getDownloadURL({
        'name': name,
        'scale': ee_scale,
        'region': ee_region,
        'filePerBand': False,
        'bands': bands
    })

    local_zip, headers = urlretrieve(path)
    with zipfile.ZipFile(local_zip) as local_zipfile:
        return local_zipfile.extractall(path=str(directory_path))


def getMedianGEEImage(ee_region, dates, EPSG, ee_scale, MASK_LAND,
                      NIR_LAND_THRESH, MAX_CLOUD_PROBABILITY):


    _printProgress(f'... calculating median image')

    def maskClouds(ee_image_col):
        clouds = ee.Image(ee_image_col.get('S2SR_joined_cloudprob')).select('probability')
        is_not_cloud = clouds.lt(MAX_CLOUD_PROBABILITY)
        return ee_image_col.updateMask(is_not_cloud)

    def maskLand(ee_image_col):
        NIR = ee.Image(ee_image_col.select('B8'))
        is_not_land = NIR.lt(NIR_LAND_THRESH*1000)
        return ee_image_col.updateMask(is_not_land)

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

    if MASK_LAND:
        S2SR_cloud_masked_col = S2SR_cloud_masked_col.map(maskLand)

    image_median = S2SR_cloud_masked_col.median() \
        .reproject(crs=f'EPSG:{EPSG}', scale=ee_scale)

    return image_median, number_images
