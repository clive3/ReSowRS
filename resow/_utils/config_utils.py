import os
import configparser

from .print_utils import printError, printWarning

CONFIG_FILE = 'resow_config.ini'


class ReSOW_Config(object):


    def __init__(self):
        """Constructor method. Creates a blank file if file not found and
        default options as required.

        :param config_file: the configuration file name
        :type config_file: ``str``
        """

        required_sections = {'PATHS': [],}

        ## if the config file does not exist create a blank with empty required section headers
        if not os.path.exists(CONFIG_FILE):
            printWarning(f'file not found: {CONFIG_FILE} creating default')
            try:
                f = open(CONFIG_FILE, "x")
                [f.write(f'[{required_section}]\n\n') for required_section in required_sections.keys()]
            except:
                printError(f'could not create default: {CONFIG_FILE}')

        try:
            ## red in the config file
            configuration = configparser.ConfigParser()
            configuration.read(CONFIG_FILE)

            ## add any required sections that do not exist
            [configuration.add_section(required_section)
             for required_section in required_sections if
             not configuration.has_section(required_section)]

            ## for any required options that do not exist add defaults
            for required_option in required_sections['PATHS']:
                if not configuration.has_option('PATHS', required_option[0]):
                    printWarning(f'no "{required_option[0]}" in PATHS adding default')
                    configuration['PATHS'][required_option[0]] = required_option[1]

            ## add sections
            self.PATHS = configuration['PATHS']

        except:
            printError(f'badly formatted: "{os.path.abspath(CONFIG_FILE)}"')
