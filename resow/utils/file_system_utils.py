import os


def makeDirectories(base_directory, BAND_DICT):

    directory_names = ['meta']

    for key in BAND_DICT.keys():
        directory_names.append(key)

    directory_paths = []
    for directory_name in directory_names:
        directory_path = os.path.join(base_directory, directory_name)
        directory_paths.append(directory_path)
        if not os.path.exists(directory_path):  os.makedirs(directory_path)

    return directory_paths