#!/usr/bin/env python
import os
import sys
import ast
import glob
import configparser

from resow._utils import geometry_utils
from resow._utils.print_utils import _printError, _printProgress
from resow._utils.geometry_utils import polygon_from_geojson

from resow.cs_stuff import tools

from resow.gee_client import downloader


class RESOWRS(object):
    """RESOW class - includes a ``run()`` method to control workflow.
    """

    def __init__(self, config_file):
        """Constructor method.

        :param config_file: the configuration file name
        :type config_file: ``str``
        """

        configuration = configparser.ConfigParser()
        configuration.read(config_file)

        self.data_partition = configuration['PATHS']['data partition']
        self.DATES = ast.literal_eval(configuration['GEE']['DATES'])
        self.BANDS = ast.literal_eval(configuration['GEE']['BANDS'])
        self.SCALE = ast.literal_eval((configuration['GEE']['SCALE']))
        self.MAX_CLOUD_PROBABILITY = ast.literal_eval(configuration['GEE']['MAX_CLOUD_PROBABILITY'])
        self.NIR_LAND_THRESH = ast.literal_eval(configuration['GEE']['NIR_LAND_THRESH'])
        self.MASK_LAND = ast.literal_eval(configuration['GEE']['MASK_LAND'])
        self.SMALL_OBJECT_SIZE = ast.literal_eval(configuration['GEE']['SMALL_OBJECT_SIZE'])
        self.OUTPUT_EPSG = ast.literal_eval(configuration['MAPPING']['OUTPUT_EPSG'])

        self.PATHS = configuration['PATHS']


    def run(self):
        """The run method to control all workflow.
        """

        extension = 'geojson'

        sites_dir_path = os.path.join(self.data_partition, 'sites')
        if os.path.exists(sites_dir_path):
            site_file_paths = glob.glob(pathname=sites_dir_path + f'/*.{extension}',
                                         recursive=False)
        else:
            _printError(f'no sites found in {sites_dir_path}')

        for site_filepath in site_file_paths:

            if extension == 'kml':
                kml_polygon = tools.polygon_from_kml(site_filepath)
                roi_polygon = tools.smallest_rectangle(kml_polygon)
            elif extension == 'geojson':
                if 'hex' in site_filepath:
                    roi_polygon = polygon_from_geojson(site_filepath, self.OUTPUT_EPSG)
                else:
                    import json
                    f = open(site_filepath)
                    roi_polygon = json.load(f)['features'][0]['geometry']['coordinates']
                    roi_polygon = tools.smallest_rectangle(roi_polygon)

            else:
                _printError(f'geometry type not recognised: {extension}')

            _, site_name = os.path.split(site_filepath)
            site_name = site_name[:site_name.find('.')]
            images_dir_path = os.path.join(self.data_partition, 'images', site_name)

            if not os.path.exists(images_dir_path):
                os.makedirs(images_dir_path)

            for date_pair in self.DATES:

                _printProgress(f'PROCESSING {site_name}: {date_pair}')
                _printProgress('')

                downloader.downloadMedianS2GEEImage(
                                    site_name, roi_polygon, date_pair, images_dir_path,
                                    self.OUTPUT_EPSG, self.BANDS, self.SCALE, self.MASK_LAND,
                                    self.NIR_LAND_THRESH, self.MAX_CLOUD_PROBABILITY)

#                if geometry_utils.createSeaMask(images_dir_path, site_name, self.SMALL_OBJECT_SIZE):
#                    _printProgress('sea mask created')

                _printProgress('')


if __name__ == '__main__':

    # turn off console warnings
    if not sys.warnoptions:
        import warnings
        warnings.simplefilter('ignore')

    # make an instance of the class and implement the run method
    obj = RESOWRS('resow_config.ini')
    obj.run()
