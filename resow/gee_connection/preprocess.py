import os
import numpy as np
from osgeo import gdal

import skimage.transform as transform
import sklearn.decomposition as decomposition
from skimage.morphology import remove_small_objects, remove_small_holes, \
    disk, erosion

from resow.utils import printProgress, printWarning, printError

from resow.utils import hansenFilePath, seaMaksFilePath

from global_parameters import SMALL_OBJECT_SIZE

def preprocess_optical(file_paths, pansharpen, NIR_index):

    # read 10m bands (R,G,B,NIR)
    file_path_10 = file_paths[0]
    data = gdal.Open(file_path_10, gdal.GA_ReadOnly)

    projection = data.GetProjectionRef()
    geotransform = data.GetGeoTransform()

    bands = [data.GetRasterBand(k + 1).ReadAsArray() for k in range(data.RasterCount)]
    image_10 = np.stack(bands, 2)
    image_10 = image_10 / 1000  # TOA scaled to 10000
    (nrows, ncols, _) = image_10.shape

    # read 20m bands
    file_path_20 = file_paths[1]

    data = gdal.Open(file_path_20, gdal.GA_ReadOnly)
    bands = [data.GetRasterBand(k + 1).ReadAsArray() for k in range(data.RasterCount)]
    image_20 = np.stack(bands, 2)
    image_20 = image_20 / 1000  # TOA scaled to 10000
    image_20m = transform.resize(image_20,
                                 output_shape=(nrows, ncols),
                                 order=1,
                                 preserve_range=True,
                                 mode='constant')

    if pansharpen:

        printProgress(f'pansharpening SWIR')

        image_NIR = image_10[:,:,NIR_index]
        image_20m = pansharpen_SWIR(image_20m, image_NIR)

#    image_SWIR = image_20m[:, :, SWIR_index]
#    image_SWIR = np.expand_dims(image_SWIR, axis=2)
    image_SWIR = image_20m

    # append down-sampled SWIR band to the other 10m bands
    image_ms = np.append(image_10, image_SWIR, axis=2)

    return image_ms, (projection, geotransform)


def pansharpen_SWIR(image_20m, image_NIR):
    
    # reshape image into vector
    image_vec = image_20m.reshape(image_20m.shape[0] * image_20m.shape[1], image_20m.shape[2])

    # apply PCA to multispectral bands
    pca = decomposition.PCA()
    vec_pca = pca.fit_transform(image_vec)

    # replace 1st PC with pan band (after matching histograms)
    vec_nir = image_NIR.reshape(image_NIR.shape[0] * image_NIR.shape[1])
    vec_pca[:, 0] = hist_match(vec_nir, vec_pca[:, 0])
    vec_20m_ps = pca.inverse_transform(vec_pca)

    # reshape vector into image
    image_20m_ps = vec_20m_ps.reshape(image_20m.shape)

    return image_20m_ps


def hist_match(source, template):
    """
    Adjust the pixel values of a grayscale image such that its histogram matches
    that of a target image.

    Arguments:
    -----------
    source: np.array
        Image to transform; the histogram is computed over the flattened
        array
    template: np.array
        Template image; can have different dimensions to source

    Returns:
    -----------
    matched: np.array
        The transformed output image

    """

    oldshape = source.shape
    source = source.ravel()
    template = template.ravel()

    # get the set of unique pixel values and their corresponding indices and
    # counts
    s_values, bin_idx, s_counts = np.unique(source, return_inverse=True,
                                            return_counts=True)
    t_values, t_counts = np.unique(template, return_counts=True)

    # take the cumsum of the counts and normalize by the number of pixels to
    # get the empirical cumulative distribution functions for the source and
    # template images (maps pixel value --> quantile)
    s_quantiles = np.cumsum(s_counts).astype(np.float64)
    s_quantiles /= s_quantiles[-1]
    t_quantiles = np.cumsum(t_counts).astype(np.float64)
    t_quantiles /= t_quantiles[-1]

    # interpolate linearly to find the pixel values in the template image
    # that correspond most closely to the quantiles in the source image
    interp_t_values = np.interp(s_quantiles, t_quantiles, t_values)

    return interp_t_values[bin_idx].reshape(oldshape)


def readGeotiff(image_file_path):

    ## import the input file and its geometry
    image_dataset_gdal = gdal.Open(image_file_path, gdal.GA_ReadOnly)
    if image_dataset_gdal:

        projection = image_dataset_gdal.GetProjectionRef()
        geotransform = image_dataset_gdal.GetGeoTransform()
        image_array_np = image_dataset_gdal.ReadAsArray()

        if len(image_array_np.shape) == 2:
            image_array_np = np.expand_dims(image_array_np, axis=0)

    else:
        printWarning(f'image file could not be read: {image_file_path}')
        image_array_np = projection = geotransform = None

    return image_array_np, (projection, geotransform)


def writeGeotiff(image_array_np, output_file_path, image_geometry):

    driver = gdal.GetDriverByName('GTiff')
    # driver.QuietDelete (output_file_path)

    if len(image_array_np.shape) == 2:
        image_array_np = np.expand_dims(image_array_np, axis=0)
    (num_bands, y_size, x_size) = image_array_np.shape

    output_ds = driver.Create(output_file_path, xsize=x_size, ysize=y_size,
                              bands=num_bands, eType=gdal.GDT_Float32)

    if not output_ds:
        printError(f'driver for file : {output_file_path} cannot be created')

    else:
        output_ds.SetProjection(image_geometry[0])
        output_ds.SetGeoTransform(image_geometry[1])

        for band in range(num_bands):

            if len(image_array_np.shape) == 3:
                output_ds.GetRasterBand(band + 1).WriteArray(image_array_np[band])

            elif len(image_array_np.shape) == 2:
                output_ds.GetRasterBand(band + 1).WriteArray(image_array_np)

            else:
                printWarning(f'cannot write the file: {output_file_path}')

        output_ds.FlushCache()
        output_ds = None


def createSeaMask(median_dir_path, site_name):

    hansen_np, geometry = readGeotiff(hansenFilePath(median_dir_path, site_name))
    hansen_np = np.squeeze(hansen_np)

    water_mask_np = np.where(hansen_np == 1, 0, 1)
    water_mask_np = remove_small_holes(remove_small_objects(water_mask_np, SMALL_OBJECT_SIZE),
                                       SMALL_OBJECT_SIZE)

    land_mask_np = np.where(water_mask_np == 0, 1, 0)

    footprint = disk(100)
    water_mask_np = erosion(water_mask_np, footprint)
    sea_mask_file_path = seaMaksFilePath(median_dir_path, site_name)
    writeGeotiff(water_mask_np, sea_mask_file_path, geometry)

    land_mask_file_path = sea_mask_file_path.replace('sea', 'land')
    writeGeotiff(land_mask_np, land_mask_file_path, geometry)


def applySeaMask(median_dir_path):

    sea_mask_np, geaometry = readGeotiff(os.path.join(seaMaksFilePath(median_dir_path)))

