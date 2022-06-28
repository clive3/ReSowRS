import numpy as np
from shapely import geometry


def polygon_from_kml(fn):
    """
    Extracts coordinates from a .kml file.

    KV WRL 2018

    Arguments:
    -----------
    fn: str
        file_path + filename of the kml file to be read

    Returns:
    -----------
    polygon: list
        coordinates extracted from the .kml file

    """

    # read .kml file
    with open(fn) as kmlFile:
        doc = kmlFile.read()
        # parse to find coordinates field
    str1 = '<coordinates>'
    str2 = '</coordinates>'
    subdoc = doc[doc.find(str1) + len(str1):doc.find(str2)]
    coordlist = subdoc.split('\n')

    coordlist = subdoc.split(',')
    # read coordinates
    polygon = []

    for coord_pair in range(int(len(coordlist) / 2)):
        lat = float(coordlist[coord_pair * 2].replace('0 ', ''))
        lon = float(coordlist[coord_pair * 2 + 1].replace('0 ', ''))
        polygon.append([lat, lon])

    # read coordinates
    #    polygon = []
    #    for i in range(1, len(coordlist) - 1):
    #        polygon.append([float(coordlist[i].split(',')[0]), float(coordlist[i].split(',')[1])])

    return [polygon]


def smallest_rectangle(polygon):
    """
    Converts a polygon to the smallest rectangle polygon with sides parallel
    to coordinate axes.

    KV WRL 2020

    Arguments:
    -----------
    polygon: list of coordinates
        pair of coordinates for 5 vertices, in clockwise order,
        first and last points must match

    Returns:
    -----------
    polygon: list of coordinates
        smallest rectangle polygon

    """

    multipoints = geometry.Polygon(polygon[0])
    polygon_geom = multipoints.envelope
    coords_polygon = np.array(polygon_geom.exterior.coords)
    polygon_rect = [[[_[0], _[1]] for _ in coords_polygon]]
    return polygon_rect