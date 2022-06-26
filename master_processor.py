#!/usr/bin/env python
import os
import sys

from resow.utils import reader_utils

class RESOW(object):
    """RESOW class - includes a ``run()`` method to control workflow.
    """

    def __init__(self, config_file):
        """Constructor method.

        :param config_file: the configuration file name
        :type config_file: ``str``
        """

        self.CONFIG_FILE = config_file


    def example_method(self):
        """A simple example to show use of the ``self`` keyword by creating
        the results directory if it does not exist.

        :return: True if results directory was created else False
        :rtype: ``boolean``
        """

        results_dir_path = self.configuration['DIRECTORY PATHS']['results']
        self.results_dir = results_dir_path

        if not os.path.isdir(results_dir_path):
            os.mkdir(results_dir_path)
            return True
        else:
            return False


    def run(self):
        """The run method to control all workflow.
        """

        self.configuration = reader_utils._readConfig(self.CONFIG_FILE)

        # the example_method shows how self can use used
        # by creating the results directory if it doesn't exist
        if self.example_method():
            print(f'created directory: {self.results_dir}')


if __name__ == '__main__':

    # turn off console warnings
    if not sys.warnoptions:
        import warnings
        warnings.simplefilter('ignore')

    # make an instance of the class and implement the run method
    obj = RESOW('resow_config.ini')
    obj.run()
