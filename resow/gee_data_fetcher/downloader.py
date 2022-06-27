import os
import ee
import pickle
import zipfile

from urllib.request import urlretrieve

from resow.utils.print_utils import printProgress, printSuccess
from resow.utils.name_utils import geotifFileName, pickleDumpName, hansenFilePath


def downloadMedianS2GEEImage(site_name, roi_polygon, date_pair,
                             images_dir_path, EPSG,
                             BANDS, SCALE, MASK_LAND, NIR_LAND_THRESH,
                             MAX_CLOUD_PROBABILITY):

    ee.Initialize()
    printProgress('connected to GEE')

    region = ee.Geometry.Polygon(roi_polygon)
    date_start, date_end = date_pair[0], date_pair[1]

    image_median, median_number = getMedianGEEImage(region, date_pair,
                                                    MASK_LAND, NIR_LAND_THRESH,
                                                    MAX_CLOUD_PROBABILITY)

    image_filename = geotifFileName(site_name, date_start, date_end, SCALE)

    local_data = os.path.join(images_dir_path, 'data.tif')
    local_file_path = os.path.join(images_dir_path, image_filename)

    printProgress(f'\t downloading median S2 image...')
    downloadGEEImage(image=image_median,
                     scale=ee.Number(SCALE),
                     region=region,
                     directory_path=images_dir_path,
                     bands=BANDS)

    try:
        os.rename(local_data, local_file_path)
    except:  # overwrite if already exists
        os.remove(local_file_path)
        os.rename(local_data, local_file_path)

    printSuccess('median image downloaded')

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
    printSuccess('hansen2015 downloaded')

    printProgress('GEE connection closed')


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


def save_metadata(site_name, median_dir_path):

    sat_name = 'S2'

    # initialize metadata dict
    metadata = {}

    meta_dir_path = os.path.join(median_dir_path, 'meta')
    metadata_files = os.listdir(meta_dir_path)
    # update the metadata dict
    metadata[sat_name] = {'file_names':[], 'epsg':[], 'date_start':[],
                          'date_end':[], 'number_images':[]}

    text_files = [file_name for file_name in metadata_files if file_name[-4:] == '.txt']

    # loop through the .txt files
    for image_meta in text_files:

        # read them and extract the metadata info
        with open(os.path.join(meta_dir_path, image_meta), 'r') as f:

            filename = f.readline().split('\t')[1].replace('\n','')
            epsg = int(f.readline().split('\t')[1].replace('\n',''))
            date_start = f.readline().split('\t')[1].replace('\n','')
            date_end = f.readline().split('\t')[1].replace('\n','')
            number_images = int(f.readline().split('\t')[1].replace('\n', ''))

        # store the information in the metadata dict
        metadata[sat_name]['file_names'].append(filename)
        metadata[sat_name]['epsg'].append(epsg)
        metadata[sat_name]['date_start'].append(date_start)
        metadata[sat_name]['date_end'].append(date_end)
        metadata[sat_name]['number_images'].append(number_images)

    # save a .pkl file containing the metadata dict
    metadata_file_name = pickleDumpName('metadata', site_name)
    with open(os.path.join(median_dir_path, metadata_file_name), 'wb') as f:
        pickle.dump(metadata, f)

    printProgress('metadata saved')


def load_metadata(site_name, median_dir_path, dates, BAND_DICT):

    sat_name='S2'
    date_start = dates[0]
    date_end = dates[1]

    metadata_file_name = pickleDumpName('metadata', site_name)
    with open(os.path.join(median_dir_path,  metadata_file_name), 'rb') as f:
        metadata_dict = pickle.load(f)

    metadata_sat = metadata_dict[sat_name]
    file_names = metadata_sat['file_names']

    # initialize metadata dict
    metadata = {}
    for file_index, file_name in enumerate(file_names):

        if date_start == metadata_sat['date_start'][file_index] and \
             date_end == metadata_sat['date_end'][file_index]:

            file_names = []

            for band_key in BAND_DICT.keys():
                file_names.append(file_name + '_' + band_key + '.tif')

            metadata['file_names'] = file_names
            metadata['epsg'] = int(metadata_sat['epsg'][file_index])
            metadata['date_start'] = date_start
            metadata['date_end'] = date_end
            metadata['number_images'] = metadata_sat['number_images'][file_index]

            break

    printProgress('metadata loaded')

    return metadata
