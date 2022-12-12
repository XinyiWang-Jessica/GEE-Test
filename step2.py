import ee
# Import the Image function from the IPython.display module.
# from IPython.display import Image

# Import pprint
# from pprint import pprint

# Import datetime
from datetime import datetime

thresh_val = 0.25

# add area field to fields
def addArea(feature):
    return feature.set({'area_sqm': feature.geometry().area()})

# ** Cloud masking
# Define a function to join the two collections on their 'system:index'
# property. The 'propName' parameter is the name of the property that
# references the joined image.
def indexJoin(colA, colB, propName):
    primary = colA
    secondary = colB
    condition = ee.Filter.equals(leftField = 'system:index', rightField = 'system:index')
    joined = ee.ImageCollection(ee.Join.saveFirst(propName).apply(primary,secondary,condition))

  # Merge the bands of the joined image.
    return joined.map(lambda image: image.addBands(ee.Image(image.get(propName))))


def buildMaskFunction(cloudProb):
    def applyCloudMask(img):
        # Define clouds as pixels having greater than the given cloud probability.
        cloud = img.select('probability').gt(ee.Image(cloudProb));
        # Apply the cloud mask to the image and return it.
        return img.updateMask(cloud.Not())
    return applyCloudMask

# Define a function to add a cloud probability band with constant raster = 0
# use for sentinel-2 images with no corresponding cloud-probability (s2c) image
def addNoCloudProb (image):
    image = image.addBands(ee.Image(0).rename('probability'))
    return image 

def cloud_free_function(image):
    pixels_cloudFree = image.select('probability').lte(50).rename('cloud_free_binary'); 
    pixels_all = image.select('probability').lte(100).rename('pixel_count'); 
    return image.addBands(pixels_cloudFree).addBands(pixels_all)

def mosaicByDate(imcol):
  # imcol: An image collection
  # returns: An image collection
    imlist = imcol.toList(imcol.size())
    unique_dates = imlist.map(lambda im: ee.Image(im).date().format("YYYY-MM-dd")).distinct()

    def inner_function(d):
        d = ee.Date(d)
        im = imcol.filterDate(d, d.advance(1, "day")).mosaic()
        return im.set(
            "system:time_start", d.millis(), 
            "system:id", d.format("YYYY-MM-dd"))
    mosaic_imlist = unique_dates.map(inner_function)
    
    return ee.ImageCollection(mosaic_imlist)

def addNDWIThresh(image):
    ndwi = image.normalizedDifference(['B8', 'B11']).rename('NDWI')
    thresh = ndwi.gt(thresh_val).rename('threshold')
    return image.addBands([ndwi,thresh])

# def reduceRegionsSum(image):
#     collection=checks_areaAdded
#     reducer=ee.Reducer.sum()
#     scale=10
#     sum_cloudfree = image.reduceRegions(collection, reducer, scale)
#   # add date field to each feature with image date
#     return sum_cloudfree.map(lambda feature: feature.set('Date', image.date().format('YYYY-MM-dd')))
