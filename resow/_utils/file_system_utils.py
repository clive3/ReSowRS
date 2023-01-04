def _saveMetadata(metadata_filepath, date_pair, image_epsg, median_number):
    """Saves metadata for the median composite image that has
     been downloaded from GEE in a .txt file.

    :param metadata_filepath: path to the metadata file to be written
    :type metadata_filepath: ``str``

    :param date_pair: start and end date of the image composite in a list
    :type date_pair: ``list``

    :param image_epsg: epsg code for the image
    :type image_epsg: ``int``

    :param median_number: number of images forming the composite
    :type median_number: ``int``
    """

    metadata_dict = {'file_name': metadata_filepath,
                     'epsg': image_epsg,
                     'date_start': date_pair[0],
                     'date_end': date_pair[1],
                     'number_images': median_number}

    with open(metadata_filepath, 'w') as f:
        for key in metadata_dict.keys():
            f.write('%s\t%s\n' % (key, metadata_dict[key]))
