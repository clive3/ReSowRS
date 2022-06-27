#!/usr/bin/env python
import os
import sys
import ast

from resow.utils import reader_utils
from resow.utils.print_utils import printError, printProgress
from resow.utils.file_system_utils import makeDirectories

from resow.gee_data_fetcher import downloader, preprocess,  tools


class RESOWRS(object):
    """RESOW class - includes a ``run()`` method to control workflow.
    """

    def __init__(self, config_file):
        """Constructor method.

        :param config_file: the configuration file name
        :type config_file: ``str``
        """

        self.configuration = reader_utils._readConfig(config_file)
        self.data_partition = self.configuration['DIRECTORY PATHS']['data partition']
        self.ROI = self.configuration['GEE SETTINGS']['ROI']
        self.EPSG = self.configuration['GEE SETTINGS']['EPSG']
        self.DATES = ast.literal_eval(self.configuration['GEE SETTINGS']['DATES'])
        self.BANDS = ast.literal_eval(self.configuration['GEE SETTINGS']['BANDS'])
        self.SCALE = ast.literal_eval(self.configuration['GEE SETTINGS']['SCALE'])
        self.MAX_CLOUD_PROBABILITY = ast.literal_eval(self.configuration['GEE SETTINGS']['MAX_CLOUD_PROBABILITY'])
        self.NIR_LAND_THRESH = ast.literal_eval(self.configuration['GEE SETTINGS']['NIR_LAND_THRESH'])
        self.MASK_LAND = ast.literal_eval(self.configuration['GEE SETTINGS']['MASK_LAND'])
        self.SMALL_OBJECT_SIZE = ast.literal_eval(self.configuration['GEE SETTINGS']['SMALL_OBJECT_SIZE'])

    def run(self):
        """The run method to control all workflow.
        """

        sites_dir_path = os.path.join(self.data_partition, 'sites')
        if os.path.exists(sites_dir_path):
            sites = os.listdir(sites_dir_path)
        else:
            printError(f'no sites found in {sites_dir_path}')

        for site in sites:

            kml_filepath = os.path.join(sites_dir_path, site)
            kml_polygon = tools.polygon_from_kml(kml_filepath)
            roi_polygon = tools.smallest_rectangle(kml_polygon)

            site_name = site[:site.find('.')]
            images_dir_path = os.path.join(self.data_partition, site_name, 'images')

            if not os.path.exists(images_dir_path):
                os.makedirs(images_dir_path)

            for date_pair in self.DATES:

                printProgress(f'processing {site_name}: {date_pair}')
                printProgress('')

                downloader.downloadMedianS2GEEImage(site_name, roi_polygon,
                                                    date_pair, images_dir_path,
                                                    self.EPSG, self.BANDS, self.SCALE,
                                                    self.MASK_LAND, self.NIR_LAND_THRESH,
                                                    self.MAX_CLOUD_PROBABILITY)

#            downloader.save_metadata(site_name, median_dir_path)

            preprocess.createSeaMask(images_dir_path, site_name, self.SMALL_OBJECT_SIZE)


if __name__ == '__main__':

    # turn off console warnings
    if not sys.warnoptions:
        import warnings
        warnings.simplefilter('ignore')

    # make an instance of the class and implement the run method
    obj = RESOWRS('resow_config.ini')
    obj.run()
