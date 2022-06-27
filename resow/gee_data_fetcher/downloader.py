import os
import ee
import zipfile

from urllib.request import urlretrieve

from resow.utils.print_utils import printProgress
from resow.utils.name_utils import geotiffFileName, hansenFilePath


def downloadMedianS2GEEImage(site_name, roi_polygon, date_pair, images_dir_path,
                             BANDS, SCALE, MASK_LAND, NIR_LAND_THRESH,
                             MAX_CLOUD_PROBABILITY):

    ee.Initialize()
    printProgress('connected to GEE')

    region = ee.Geometry.Polygon(roi_polygon)
    date_start, date_end = date_pair[0], date_pair[1]

    image_median, median_number = getMedianGEEImage(region, date_pair,
                                                    MASK_LAND, NIR_LAND_THRESH,
                                                    MAX_CLOUD_PROBABILITY)

    image_metadata = image_median.getInfo()
    image_epsg = image_metadata['bands'][0]['crs'][5:]

    image_filename = geotiffFileName(site_name, date_start, date_end, SCALE)

    local_data = os.path.join(images_dir_path, 'data.tif')
    local_file_path = os.path.join(images_dir_path, image_filename)

    downloadGEEImage(image=image_median,
                     scale=ee.Number(SCALE),
                     region=region,
                     directory_path=images_dir_path,
                     bands=BANDS)

    try:
        os.rename(local_data, local_file_path)
    except:
        os.remove(local_file_path)
        os.rename(local_data, local_file_path)

    printProgress(f'median S2 downloaded from {median_number} images')

    local_data = os.path.join(images_dir_path, 'data.tif')
    hansen_file_path = hansenFilePath(images_dir_path, site_name)
    downloadGEEImage(image=ee.Image('UMD/hansen/global_forest_change_2015'),
                     scale=ee.Number(SCALE),
                     region=region,
                     directory_path=images_dir_path,
                     bands='datamask')

    try:
        os.rename(local_data, hansen_file_path)
    except:  # overwrite if already exists
        os.remove(hansen_file_path)
        os.rename(local_data, hansen_file_path)
    printProgress('hansen2015 downloaded')

    printProgress('GEE connection closed')

    return  median_number, image_epsg


def downloadGEEImage(image, scale, region, directory_path, bands):

    path = image.getDownloadURL({
        'name': 'data',
        'scale': scale,
        'region': region,
        'filePerBand': False,
        'bands': bands
    })

    local_zip, headers = urlretrieve(path)
    with zipfile.ZipFile(local_zip) as local_zipfile:
        return local_zipfile.extractall(path=str(directory_path))


def getMedianGEEImage(region, dates, MASK_LAND, NIR_LAND_THRESH, MAX_CLOUD_PROBABILITY):

    def maskClouds(img):

        clouds = ee.Image(img.get('cloud_mask')).select('probability')
        isNotCloud = clouds.lt(MAX_CLOUD_PROBABILITY)

        return img.updateMask(isNotCloud)

    def maskLand(img):

        NIR = ee.Image(img.select('B8'))
        isNotLand = NIR.lt(NIR_LAND_THRESH*1000)

        return img.updateMask(isNotLand)


    S2SR_col = ee.ImageCollection('COPERNICUS/S2_SR')\
                                    .filterBounds(region)\
                                    .filterDate(dates[0], dates[1])

    S2_cloudprob_col = ee.ImageCollection('COPERNICUS/S2_CLOUD_PROBABILITY')\
                                    .filterBounds(region)\
                                    .filterDate(dates[0], dates[1])

    S2SRwithCloudMask = ee.ImageCollection(ee.Join.saveFirst('cloud_mask')\
                                                  .apply(**{'primary': S2SR_col,
                                                            'secondary': S2_cloudprob_col,
                                                            'condition': ee.Filter.equals(**{
                                                            'leftField': 'system:index',
                                                            'rightField': 'system:index'})}))

    image_list = S2SRwithCloudMask.toList(500)
    number_images = len(image_list.getInfo())

    if MASK_LAND:
        image_median = S2SRwithCloudMask.map(maskClouds).map(maskLand).median()
    else:
        image_median = S2SRwithCloudMask.map(maskClouds).median()

    return image_median, number_images
