import os
import pickle

from resow.utils.print_utils import printProgress


def saveMetadata(metadata_filepath, date_pair, image_epsg, median_number):

    metadata_dict = {'file_name': metadata_filepath,
                     'epsg': image_epsg,
                     'date_start': date_pair[0],
                     'date_end': date_pair[1],
                     'number_images': median_number}

    with open(metadata_filepath, 'w') as f:
        for key in metadata_dict.keys():
            f.write('%s\t%s\n' % (key, metadata_dict[key]))


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