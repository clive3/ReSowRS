# -*- coding: utf-8 -*-
"""
Created on Tue Jul 16 09:35:46 2019coast.coast_params

@author: cneil
"""
import os

from global_parameters import MASK_LAND


def geotifFileName(site_name, date_start, date_end, band_key):

    if band_key  is None:
        file_name = site_name + '_median_' + date_start.replace('-','') +'_'+ date_end.replace('-','') + '.tif'
    else:
        file_name = site_name + '_test_' + date_start.replace('-','') +'_'+ date_end.replace('-','') + '_' + band_key + '.tif'

    return file_name


def pickleDumpName(pickle_type, site_name):

    file_name =  site_name + '_' + pickle_type + '.pkl'

    return file_name


def hansenFilePath(median_dir_path, site_name):

    return os.path.join(median_dir_path, site_name + '_hansen2015.tif')

def seaMaksFilePath(median_dir_path, site_name):

    return os.path.join(median_dir_path, site_name + '_sea_mask.tif')
