import os
import ee
import pickle
import zipfile

from urllib.request import urlretrieve

from utils.print_utils import printProgress, printSuccess
from utils.name_utils import geotifFileName, pickleDumpName, hansenFilePath

from global_parameters import EPSG, BAND_DICT, MAX_CLOUD_PROBABILITY, \
    NIR_LAND_THRESH, MASK_LAND


def getMedianS2GEEImage(site_name, roi, dates, median_dir_path):

    date_start, date_end = dates[0], dates[1]

    if not os.path.exists(median_dir_path):
        os.makedirs(median_dir_path)
    directory_path_list = makeDirectories(median_dir_path)

    ee.Initialize()
    printProgress('connected to GEE')

    region = ee.Geometry.Polygon(roi)
#    region = ee.Geometry.Point(roi).buffer(2000)

    image_median, median_number = getMedianImage(region, dates)

    local_data = os.path.join(median_dir_path, 'data.tif')

    image_filenames = {}
    for band_key in BAND_DICT.keys():
        image_filenames[band_key] = geotifFileName(site_name, date_start, date_end, band_key)

    for index, band_key in enumerate(BAND_DICT.keys()):

        band_names = BAND_DICT[band_key][0]
        band_scale = BAND_DICT[band_key][1]
        band_directory_path = directory_path_list[index + 1]
        image_file_name = image_filenames[band_key]

        local_data = band_directory_path + '\\data.tif'
        local_file_path = os.path.join(band_directory_path, image_file_name)

        printProgress(f'\t"{band_key}" bands:\t{band_names}')
        download_GEE_image(image=image_median,
                           scale=ee.Number(band_scale),
                           region=region,
                           directory_path=band_directory_path,
                           bands=band_names)

        try:
            os.rename(local_data, local_file_path)
        except:  # overwrite if already exists
            os.remove(local_file_path)
            os.rename(local_data, local_file_path)

    if not MASK_LAND:
        base_file_name = image_file_name.replace('_'+band_key+'.tif', '')
    else:
        base_file_name = image_file_name.replace('_'+band_key+'.tif', '')

    txt_file_name = base_file_name + '.txt'

    metadata_dict = {'file_name': base_file_name,
                     'epsg': EPSG,
                     'date_start': date_start,
                     'date_end': date_end,
                     'number_images': median_number}

    with open(os.path.join(directory_path_list[0], txt_file_name), 'w') as f:
        for key in metadata_dict.keys():
            f.write('%s\t%s\n' % (key, metadata_dict[key]))

    printProgress('GEE connection closed')
    printSuccess('median image downloaded')

    local_data = os.path.join(median_dir_path, 'data.tif')
    hansen_file_path = hansenFilePath(median_dir_path, site_name)
    download_GEE_image(image=ee.Image('UMD/hansen/global_forest_change_2015'),
                       scale=ee.Number(10),
                       region=region,
                       directory_path=median_dir_path,
                       bands='datamask')

    try:
        os.rename(local_data, hansen_file_path)
    except:  # overwrite if already exists
        os.remove(hansen_file_path)
        os.rename(local_data, hansen_file_path)
    printSuccess('hansen2015 downloaded')


def download_GEE_image(image, scale, region, directory_path, bands):

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


def makeDirectories(base_directory):

    directory_names = ['meta']

    for key in BAND_DICT.keys():
        directory_names.append(key)

    directory_paths = []
    for directory_name in directory_names:
        directory_path = os.path.join(base_directory, directory_name)
        directory_paths.append(directory_path)
        if not os.path.exists(directory_path):  os.makedirs(directory_path)

    return directory_paths


def getMedianImage(region, dates):

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


def load_metadata(site_name, median_dir_path, dates):

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
