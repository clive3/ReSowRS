import os


def geotifFileName(site_name, date_start, date_end, scale):

    file_name = site_name + '_median_' + date_start.replace('-','') \
                +'_'+ date_end.replace('-','') + '_' + str(scale) + 'm.tif'

    return file_name


def pickleDumpName(pickle_type, site_name):

    file_name =  site_name + '_' + pickle_type + '.pkl'

    return file_name


def hansenFilePath(median_dir_path, site_name):

    return os.path.join(median_dir_path, site_name + '_hansen2015.tif')

def seaMaksFilePath(median_dir_path, site_name):

    return os.path.join(median_dir_path, site_name + '_sea_mask.tif')
