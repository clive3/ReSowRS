#!/usr/bin/env python
import os
import sys

from resow.utils import reader_utils
from resow.utils.print_utils import printError, printProgress

from resow.gee_connection import downloader, preprocess,  tools



class RESOWRS(object):
    """RESOW class - includes a ``run()`` method to control workflow.
    """

    def __init__(self, config_file):
        """Constructor method.

        :param config_file: the configuration file name
        :type config_file: ``str``
        """

        self.configuration = reader_utils._readConfig(self.CONFIG_FILE)
        self.data_partition = self.configuration['DIRECTORY PATHS']['data partition']
        self.roi = self.configuration['ROI']
        self.dates = self.configuration['dates']

        self.EPSG = self.configuration['EPSG']
        self.BAND_DICT = self.configuration['BAND_DICT']
        self.MAX_CLOUD_PROBABILITY = self.configuration['MAX_CLOUD_PROBABILITY']
        self.NIR_LAND_THRESH = self.configuration['NIR_LAND_THRESH']
        self.MASK_LAND = self.configuration['MASK_LAND']

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
            median_dir_path = os.path.join(self.data_partition, site_name, 'median')

            for date_pair in self.dates:
                printProgress(f'processing {site_name}: {date_pair}')
                printProgress('')

                downloader.getMedianS2GEEImage(site_name, self.roi, self.dates,
                                               median_dir_path, self.EPSG, \
                                                self.BAND_DICT, self.MASK_LAND)

            downloader.save_metadata(site_name, median_dir_path)

            preprocess.createSeaMask(median_dir_path, site_name)





if __name__ == '__main__':

    # turn off console warnings
    if not sys.warnoptions:
        import warnings
        warnings.simplefilter('ignore')

    # make an instance of the class and implement the run method
    obj = RESOWRS('resow_config.ini')
    obj.run()
