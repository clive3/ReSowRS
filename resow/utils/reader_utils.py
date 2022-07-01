#!/usr/bin/env python
import configparser


def readConfig(config_file_path):
    """Reads the configuration ini file.

    :param config_file_path: path to the configuration file
    :type config_file_path: ``str``

    :return: the configuration object read from the local configuration file
    :rtype: ``configparser``

    """

    configuration = configparser.ConfigParser()
    configuration.read(config_file_path)

    return configuration
