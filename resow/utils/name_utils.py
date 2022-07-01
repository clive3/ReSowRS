#!/usr/bin/env python
import os


def _geotiffFileName(site_name, date_start, date_end, scale, MASK_LAND):

    file_name = site_name + '_median_' + date_start.replace('-','') \
                +'_'+ date_end.replace('-','') + '_' + str(scale) + 'm.tif'

    if MASK_LAND:
        file_name = file_name.replace('.tif', '_lm.tif')

    return file_name


def _hansenFilePath(median_dir_path, site_name):

    return os.path.join(median_dir_path, site_name + '_hansen2015.tif')


def _seaMaskFilePath(median_dir_path, site_name):

    return os.path.join(median_dir_path, site_name + '_sea_mask.tif')
