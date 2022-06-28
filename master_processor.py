#!/usr/bin/env python
import os
import sys
import ast

from resow.utils import reader_utils, geometry_utils
from resow.utils.print_utils import printError, printProgress
from resow.utils.file_system_utils import saveMetadata
from resow.utils.name_utils import geotiffFileName
from resow.utils.geometry_utils import polygon_from_geojson

from resow.gee_data_fetcher import downloader


class RESOWRS(object):
    """RESOW class - includes a ``run()`` method to control workflow.
    """

    def __init__(self, config_file):
        """Constructor method.

        :param config_file: the configuration file name
        :type config_file: ``str``
        """

        self.configuration = reader_utils.readConfig(config_file)

        self.data_partition = self.configuration['PATHS']['data partition']
        self.DATES = ast.literal_eval(self.configuration['GEE']['DATES'])
        self.BANDS = ast.literal_eval(self.configuration['GEE']['BANDS'])
        self.SCALE = ast.literal_eval(self.configuration['GEE']['SCALE'])
        self.MAX_CLOUD_PROBABILITY = ast.literal_eval(self.configuration['GEE']['MAX_CLOUD_PROBABILITY'])
        self.NIR_LAND_THRESH = ast.literal_eval(self.configuration['GEE']['NIR_LAND_THRESH'])
        self.MASK_LAND = ast.literal_eval(self.configuration['GEE']['MASK_LAND'])
        self.SMALL_OBJECT_SIZE = ast.literal_eval(self.configuration['GEE']['SMALL_OBJECT_SIZE'])
        self.OUTPUT_EPSG = self.configuration['MAPPING']['OUTPUT_EPSG']

    def run(self):
        """The run method to control all workflow.
        """

        sites_dir_path = os.path.join(self.data_partition, 'sites')
        if os.path.exists(sites_dir_path):
            sites = os.listdir(sites_dir_path)
        else:
            printError(f'no sites found in {sites_dir_path}')

        for site in sites:

            site_filepah = os.path.join(sites_dir_path, site)

            roi_polygon = polygon_from_geojson(site_filepah, self.OUTPUT_EPSG)

            site_name = site[:site.find('.')]
            images_dir_path = os.path.join(self.data_partition, 'images', site_name)

            if not os.path.exists(images_dir_path):
                os.makedirs(images_dir_path)

            for date_pair in self.DATES:

                printProgress(f'processing {site_name}: {date_pair}')
                printProgress('')

                median_number, image_epsg = downloader.downloadMedianS2GEEImage(
                                    site_name, roi_polygon, date_pair, images_dir_path,
                                    self.BANDS, self.SCALE, self.MASK_LAND,
                                    self.NIR_LAND_THRESH, self.MAX_CLOUD_PROBABILITY)

                metadata_filename = geotiffFileName(site_name, date_pair[0], date_pair[1], self.SCALE)
                metadata_filename = metadata_filename.replace('tif', 'txt')
                metadata_filepath = os.path.join(images_dir_path, metadata_filename)
                saveMetadata(metadata_filepath, date_pair, image_epsg, median_number)

                printProgress('metadata saved')

            geometry_utils.createSeaMask(images_dir_path, site_name, self.SMALL_OBJECT_SIZE)

            printProgress('sea mask created')


if __name__ == '__main__':

    # turn off console warnings
    if not sys.warnoptions:
        import warnings
        warnings.simplefilter('ignore')

    # make an instance of the class and implement the run method
    obj = RESOWRS('resow_config.ini')
    obj.run()
