#!/usr/bin/env python
#-*- coding: utf-8 -*-

"""Create mosaics of input images.

The module offers the possibility to create poster-alike images compound
by small tiles representing input photos. Moreover, the module could be
used both as a standalone application and as a standard python library.

Given a list of input images, the first of them will be chosen as
target, i.e. the final image. On the other hand, other images will be
chosen in turn, modified, and finally placed in the right position of
the final mosaic image.

During the creation of a mosaic, we need to arrange the images used
a tiles, inside a data structure which make it possible to extract
images by color. Image, at least for early implementations, this
structure to be a simple list of images.

Moreover, in order to avoid long waits due to indexing of very large
images, we could implement a sort of filter, or a chain of filters, that
could eventually be used to scale down input images, or either quantize
their colors.

The next step is to analyze the target image and look for needed tiles
for the final mosaic. Depending on the specified number of
tiles-per-side, we are going to divide the original image in small
tiles. Then, for each tile, we are going to compute its *fingerprint*,
which in our case corresponds to its average color.

At this point everything is ready to actually create the mosaic. For
each tile extracted from the target image, look inside the efficient
data structure and spot which of the available tiles has an average color
the most similar to the current one. Then we have to paste such found
tile in place of the original one.

Once we are done with all the tiles of the target image, we will be able
to either show the image on screen - watch out from large images ;-) - or
save it to a disk.

TODO:

    - Use a KD-Tree for the internal logic of the ``ImageList`` object.

    - Resize input if too large. Maybe we could implement an adaptive
      way to compute the target size depending on the number of
      specified tiles and zoom level.

    - In order to reduce the amount of work load, we could quantize
      target and source images.

    - While iterating over the colors of very large images, we could
      think of using the color histogram to reduce the length of output
      array.

    - While cropping an image to modify the ratio, we could probably use
      the image barycenter in order to throw away useless parts of the
      image.

GOALS OF ABSTRACT API:

* Keep the files use-case simple
  * if the images had not been processed at all, then 
    it should still be efficient to sample all the tiles down first (to the tile size),
       and then sample the colors based on that
       (rather than the reverse, which the mosaic process needs, but would be slower)
* Abstraction enough for Django/db to utilize/leverage pre-processed information like:
  * average color of a tile
  * dimensions of a tile
  * lattice_cache (of a certain wxh of colors)
* Maintain opportunity for parallelization:
  * ?should not require tiles to be all pre-loaded
* Artifacts of process should be sent-back as well for utilization/caching with
  future rounds.

INPUTS
 stage 1: source images, target images, width/height 'goals'
 stage 2: source image (source_image_id) hue/lum averages,
          target tile (target_image_id, x, y) with hue/lum averages
 stage 3: lattice matches, source image resized tiles

OUTPUTS:
 stage 1: get lattice(dims, num_tiles), get colors
 stage 2: match targets/sources
 stage 3: generate mosaic



"""

from __future__ import division
import itertools
import json
import math
import multiprocessing
import operator
import random
import time
from collections import namedtuple
from optparse import OptionParser
from optparse import OptionGroup
from functools import partial

import kdtree
from PIL import Image


def splitter(n, iterable):
    """Split `iterable` into `n` separate buckets.
    >>> list(splitter(3, range(6)))
    [[0, 1], [2, 3], [4, 5]]
    """
    items_per_bucket = len(iterable) / n
    cutoff = 1
    acc = []
    for (i, elem) in enumerate(iterable):
        if i < cutoff * items_per_bucket:
            acc += [elem]
        else:
            yield acc
            cutoff += 1
            acc = [elem]
    if acc:
        yield acc


def flatten(iterable):
    """Flatten the input iterable.
    >>> list(flatten([[0, 1], [2, 3]]))
    [0, 1, 2, 3]
    """
    return itertools.chain.from_iterable(iterable)


def average_color(img):
    """Return the average color of the given image.

    The calculus of the average color has been implemented by looking at
    each pixel of the image and accumulate each rgb component inside
    separate counters.

    """
    # this is slower, but cool
    # https://github.com/cortesi/scurve/tree/master/scurve
    # return img.blob.resize((1,1)).getcolors(1)[0][1]
    # print(img)
    # print(img.__dict__)
    (width, height) = img.size
    num_pixels = width * height
    (total_red, total_green, total_blue) = (0, 0, 0)
    for (occurrences, (red, green, blue)) in img.colors:
        total_red += occurrences * red
        total_green += occurrences * green
        total_blue += occurrences * blue
    return (total_red // num_pixels,
            total_green // num_pixels,
            total_blue // num_pixels)


SerializableImage = namedtuple('SerializableImage',
                               'filename size mode data avg_color'.split())

class ImageWrapper(object):
    """Wrapper around the ``Image`` object from the PIL library.

    We need to create our own image api and abstract, to the whole
    module layer, the underlaying image processing library.

    """

    def __init__(self, **kwargs):
        """Initialize a new image object.

        It is possible both to open a new image from scratch, i.e. using
        its filename, or import raw data from another in-memory object.
        If both the ``filename`` and ``blob`` fields are specified, then
        the in-memory data associated to the image, will be taken from
        the blob.

        """
        self.filename = kwargs.pop('filename')
        self.blob = kwargs.pop('blob', None)
        _average_color = kwargs.pop('average_color', True)
        if self.blob is None:
            try:
                if self.filename.startswith("http://") or self.filename.startswith("https://"):
                    import urllib, cStringIO
                    file = cStringIO.StringIO(urllib.urlopen(self.filename).read())
                    self.blob = Image.open(file)
                else:
                    self.blob = Image.open(self.filename)
                #convert to RGB or getcolors can return all sorts of things
                #is this slow?
                self.blob = self.blob.convert("RGB")
            except IOError:
                raise
        if _average_color:
            self._average_color = average_color(self)

    @property
    def avg_color(self):
        return self._average_color

    def average_color(self, rect=None):
        if rect is None:
            if self._average_color:
                return self._average_color
            elif self.blob:
                self._average_color = BaseColorReader.average_color(self)
        else:
            return self.crop(rect).avg_color

    def __getitem__(self, i):
        #indexable for kd-tree against RGB vals
        return self._average_color[i]

    def __len__(self):
        return 3 #dimensions

    @property
    def colors(self):
        """Get all the colors of the image."""
        (width, height) = self.size
        return iter(self.blob.getcolors(width * height))

    @property
    def size(self):
        """Return a tuple representing the size of the image."""
        return self.blob.size

    def resize(self, size):
        """Set the size of the image."""
        if any(v < 0 for v in size):
            raise ValueError("Size could not contain negative values.")

        self.blob = self.blob.resize(size)

    @property
    def ratio(self):
        """Get the ratio (width / height) of the image."""
        (width, height) = self.blob.size
        return (width / height)

    def reratio(self, ratio):
        """Set the ratio (width / height) of the image.

        A consequence of the ratio modification, is image shrink; the
        size of the result image need to be modified to match desired
        ratio; consequently, part of the image will be thrown away.
        """
        if ratio < 0:
            raise ValueError("Ratio could not assume negative values.")

        (width, height) = self.size
        if (width / height) > ratio:
            (new_width, new_height) = (int(ratio * height), height)
        else:
            (new_width, new_height) = (width, int(width / ratio))
        (x, y) = ((width - new_width) / 2, (height - new_height) / 2)
        rect = (x, y, x + new_width, y + new_height)
        self.blob = self.blob.crop([int(v) for v in rect])

    def crop(self, rect):
        """Crop the image matching the given rectangle.

        The rectangle is a tuple containing top-left and bottom-right
        points: (x1, y1, x2, y2)

        """
        if any(v < 0 for v in rect):
            raise ValueError("Rectangle could not contain negative values.")
        return ImageWrapper(filename=self.filename, blob=self.blob.crop(rect))

    def paste(self, image, rect):
        """Paste given image over the current one."""
        self.blob.paste(image.blob, rect)

    def serialize(self):
        """Convert the image wrapper into a `SerializableImage`."""
        return SerializableImage(self.filename, self.size, self.blob.mode,
                                 self.blob.tobytes(), self.avg_color)

    @staticmethod
    def deserialize(raw):
        """Create a new image wrapper from the given `SerializableImage`."""
        return ImageWrapper(filename=raw.filename,
                            blob=Image.frombytes(raw.mode,
                                                 raw.size,
                                                 raw.data))


class ImageList(object):
    """List of images, optimized for color similarity searches.

    The class should be though as the implementation of a database of
    images; in particular, its implementation will be optimized for
    queries asking for similar images, where the similarity metric is
    based on the average color.

    """

    def __init__(self, tile_image_list):
        """Initialize the internal list of images."""
        self._used = []
        self._img_kd_tree = kdtree.create(
            tile_image_list, dimensions=3)

    def _reset(self):
        #for when we have to re-use images (sparingly)
        if len(self._used):
            self._img_kd_tree = kdtree.create(self._used, dimensions=3)
            self._used = []

    stime = 0.0
    rtime = 0.0
            
    def search(self, color, whenskip=0, skip_list=[]):
        """Search the most similar image in terms of average color."""
        if len(self._used) and \
           (self._img_kd_tree.data is None or len(self._img_kd_tree.data) == 0):
            self._reset()

        
        #t = time.time()
        #this is superslow
        found_tileimages = self._img_kd_tree.search_nn(color)
        #TODO: switch the approach here to matching tiles to the best placement rather than the reverse
        #self.stime = self.stime + time.time() - t
        if len(found_tileimages) > 0:
            tileimage = found_tileimages[0]
            imagewrapper = tileimage.data
            #t= time.time()
            self._img_kd_tree.remove(imagewrapper, tileimage)
            #self.rtime = self.rtime + time.time() - t
            self._used.append(imagewrapper)

            return imagewrapper.filename


def _load_raw_tiles(filenames, ratio, size):
    def func(filename):
        img = ImageWrapper(filename=filename)
        img.reratio(ratio)
        img.resize(size)
        return img.serialize()
    return [func(filename) for filename in filenames]


def load_raw_tiles(filenames, ratio, size, pool, workers):
    raws = flatten(pool.map(partial(_load_raw_tiles, ratio=ratio, size=size),
                            splitter(workers, filenames)))
    return [ImageWrapper.deserialize(raw) for raw in raws]


def _extract_average_colors(filename, rectangles):
    """Extract from `img` multiple tiles covering areas described by
    `rectangles`"""
    img = ImageWrapper(filename=filename)
    return [img.crop(rect).avg_color for rect in rectangles]


def extract_average_colors(img, rectangles, pool, workers):
    """Convert input image into a matrix of tiles_per_size.

    Return a matrix composed by tile-objects, i.e. dictionaries,
    containing useful information for the final mosaic.

    In our particular case we are in need of the average color of the
    region representing a specific tile. For compatibility with the
    objects used for the ``ImageList`` we set the filename and blob
    fields either.

    """
    return flatten(pool.map(partial(_extract_average_colors, img.filename),
                            splitter(workers, rectangles)))

def _search_matching_images(image_list, whenskip, avg_colors):
    """Gets the name of tiles that best match the given list of colors."""
    x = [image_list.search(color, whenskip) for color in avg_colors]
    #print ('time searching', image_list.stime, image_list.rtime)
    return x


def search_matching_images(image_list, avg_colors, pool, workers, whenskip=0):
    smi = partial(_search_matching_images, image_list, whenskip)
    return flatten(pool.map(smi,
                            splitter(workers, avg_colors)))


class Mosaic(object):
    def __init__(self, mosaic, tiles):
        self._mosaic = mosaic
        self._tiles = tiles
        self._initialized = False

    def _initialize(self):
        if not self._initialized:
            for (rect, img) in self._tiles:
                self._mosaic.paste(img, rect)
            self._initialized = True

    def show(self):
        self._initialize()
        self._mosaic.blob.show()

    def save(self, destination):
        self._initialize()
        self._mosaic.blob.save(destination)

class MaximizeFillSizer:

    lattice = None

    def __init__(self, zoom=1, tiles_across=None):
        self.zoom = zoom
        self.tiles_width = tiles_across

    def get_lattice(self, width, height, source_count):
        tiles_height = None
        if self.tiles_width is None:
            #max width with # tiles used
            tiles_width = int(width * math.sqrt(source_count) / math.sqrt(width * height))
            tiles_height = int(height * tiles / original_width)
        else:
            tiles_width = int(self.tiles_width)
        return list(self.make_lattice(width, height, tiles_width, tiles_height))

    def make_lattice(self, width, height, rects_width, rects_height=None):
        """Creates a lattice width height big and containing `rectangles_per_size`
        rectangles per size.

        The lattice is returned as a list of rectangle definitions, which are
        tuples containing:
        - top-left point x offset
        - top-left point y offset
        - bottom-right point x offset
        - bottom-right point y offset

        >>> list(lattice(10, 10, 2))
        [(0, 0, 5, 5), (5, 0, 10, 5), (0, 5, 5, 10), (5, 5, 10, 10)]
        """
        if not rects_height:
            rects_height = rects_width
        (tile_width, tile_height) = (width // rects_width,
                                     height // rects_height)
        for i in range(rects_height):
            for j in range(rects_width):
                (x_offset, y_offset) = (j * tile_width, i * tile_height)
                yield (x_offset, y_offset,
                       x_offset + tile_width, y_offset + tile_height)


class BaseColorReader:
    """
    assumes target, source have the following attributes:
     .average_color(rect=None)
    """
    def target_mapper(self, target, lattice):
        return [target.average_color(rect=rect) for rect in lattice]

    def getcolors(sources):
        return [s.average_color() for s in sources]

<<<<<<< HEAD
    @classmethod
    def average_color(cls, img):
        """Return the average color of the given image.
        
        The calculus of the average color has been implemented by looking at
        each pixel of the image and accumulate each rgb component inside
        separate counters.
        
        """
        # print(img)
        # print(img.__dict__)
        (width, height) = img.size
        num_pixels = width * height
        (total_red, total_green, total_blue) = (0, 0, 0)
        for (occurrences, (red, green, blue)) in img.colors:
            total_red += occurrences * red
            total_green += occurrences * green
            total_blue += occurrences * blue
        return (total_red // num_pixels,
                total_green // num_pixels,
                total_blue // num_pixels)


def skymosaic(target, sources,
              sizer=MaximizeFillSizer(zoom=1),
              color_reader=BaseColorReader,
              chooser=kd_tree_chooser,
              renderer=BaseMosaicRenderer(zoom=1)):
    #def skymosaic(targets, sources, strategy, writer):
    """
    targets
    target.width
    target.height
    target.getfile/blob

    sources.getfile/blob(sourcekey, width=None, height=None)
    sources.getcolor(sourcekey)
    sources.initialize(target_width, target_height, 
      #note will target_width/height ever be effected by sources?
      #  quantity of sources will determine that
    
    strategy.calculate_lattice
    strategy.match_colors(source_colors_list, lattice)

    writer(target, sources, strategy, final_mosaic_lattice)
    """
    #Step 0. lattice = strategy.build_lattice(target.width, target.height, source.count, zoom)
    #Step 1. needs file access (or db memory):
    #  determine source average colors, determine target-lattice colors
    #Step 2. map sources to lattice
    #   strategy.match_colors(source_list_colors, lattice)
    #Step 3. needs file access read/write
    #  generate based on lattice map
    # API should be able to skip pre-done steps
    #assumed API for source, target for defaults
    # source.average_color(rect=None) -> rgb color
    # source.get_image(width, height) -> image #resized, if necessary

    lattice = sizer.lattice or sizer.get_lattice(target.width, target.height, len(sources))

    #color_data.source_colors (order corresponds to sources[])
    #          .target_color_lattice (order corresponds to lattice[])
    #(optional).sources_resized (order corresponds to sources[])
    #    this can be a by product so can be done in this step
    color_data = color_reader.target_mapper(target, sources, lattice)

    #->indexes for sources
    source2lattice_mapping = chooser(color_data.source_colors,
                                     color_data.target_color_lattice,
                                     lattice)


    #DB version
    # source image colors should be calculated upon download -- so not in this loop
    # - but for other use-cases, should you be able to get the color calculations?
    # when same tiles_x, tiles_y request is made, then use x,y positions from db with average colors
    return renderer.mosaic(target, lattice, source2lattice_mapping,
                           sources, color_data)



def mosaicify(target, sources, tiles=None, zoom=1, jsonfile=None):
    """Create mosaic of photos.

    The function wraps all process of the creation of a mosaic, given
    the target, the list of source images, the number of tiles to use
    per side, the zoom level (a.k.a.  how large the mosaic will be), and
    finally if we want to display the output on screen or dump it on
    a file.

    First, open the target image, divide it into the specified number of
    tiles, and store information about the tiles average color. In
    order to reduce the amount of used memory, we will free the *blobs*
    associated to each processed image, as soon as possible, aka inside
    the ``postfunc`` function.

    Then, index all the source images by color. Given that we are aware
    about the size and the ratio of the tiles of the target, we can use
    the ``prefunc`` to reduce the dimension of the image; consequently
    the amount of computations needed to compute the average color will
    smaller. Moreover, as in the previous paragraph, there is no need to
    keep into processed images, hence we are going to use the
    ``postfunc`` method to delete them.

    Finally, for each tile extracted from the target image, we need to
    find the most similar contained inside the list of source images,
    and paste it in the right position inside the mosaic image.

    When done, show the result on screen or dump it on the disk.

    """
    # Load the target image into memory

    mosaic = ImageWrapper(filename=target)
            
    # Generate the list of rectangles identifying mosaic tiles
    (original_width, original_height) = mosaic.size

    tiles_height = None
    if tiles is None:
        #max width with # tiles used
        tiles = int(original_width * math.sqrt(len(sources)) / math.sqrt(original_width * original_height))
        tiles_height = int(original_height * tiles / original_width)
        print('tile dims:', tiles, tiles_height)
    else:
        tiles = int(tiles)
    rectangles = list(lattice(original_width, original_height, tiles, tiles_height))

    # Compute the size of the tiles after the zoom factor has been applied
    (zoomed_tile_width, zoomed_tile_height) = (zoom * original_width // tiles,
                                               zoom * original_height // tiles_height)

    # Initialize the pool of workers
    workers = multiprocessing.cpu_count()
    pool = multiprocessing.Pool(workers)

    # Load tiles into memory and resize them accordingly
    #slowish
    # this is only important here, because we don't have the average color
    #   otoh, if you *are* loading the tiles from files and will do the
    #   conversion in the same write/process, then this is good/useful
    #   so, 'sources' should cache this
    source_tiles = dict(zip(sources,
                            load_raw_tiles(sources,
                                           mosaic.ratio,
                                           (zoomed_tile_width,
                                            zoomed_tile_height),
                                           pool,
                                           workers)))

    # TODO: source_objects tracked to position (and not indexed by filename)
    
    # Indicize all the source images by their average color
    source_list = ImageList(list(source_tiles.values()))
    #t.append(time.time())
    #print('4time ', t[-1]-t[-2], t[-1]-t[0])
            

    #ratio of how many tiles we need vs how many we want
    # if >1, then the primary challenge is finding the sorted match
    # if <1 then the primary challenge is to use what we have, and then repeat
    avail2needed = float(len(source_tiles)) / len(rectangles)

    print('amt', len(source_tiles), len(rectangles))

    # Compute the target's average color of each mosaic tile-section
    mosaic_avg_colors = list(extract_average_colors(mosaic, rectangles, pool,
                                                    workers))

    # Shut down the pool of workers
    pool.close()
    pool.join()

    # Find which source image best fits each mosaic tile
    #slowslow 62sec for 5000 images
    best_matching_imgs = list(_search_matching_images(source_list,
                                                      avail2needed,
                                                      mosaic_avg_colors,
                                                      ))

    # Apply the zoom factor
    (zoomed_width, zoomed_height) = (tiles * zoomed_tile_width,
                                     tiles_height * zoomed_tile_height)
    # why do we do this?  for the outputted image?!?
    #   otherwise, we don't care -- we can do that client-side or whatever
    mosaic.resize((zoomed_width, zoomed_height))
    rectangles = list(lattice(zoomed_width, zoomed_height, tiles))

    #TODO: move this out
    #possible artifacts:
    #  * tile-square: source mapping (with metadata, e.g. author, tweet)
    #  * final height/width, tile, count
    #  * which sources were used
    #  * rectangles
    #  * obviously -- final mosaic image
    if jsonfile:
        with open(jsonfile, 'w') as jf:
            jf.write(json.dumps({
                'rectangles':rectangles,
                'best_matching': best_matching_imgs,
                'width': zoomed_width,
                'height': zoomed_height,
            }))

    m = Mosaic(mosaic, zip(rectangles,
                           map(source_tiles.get,
                               best_matching_imgs)))
            
    return m


def _build_parser():
    """Return a command-line arguments parser."""
    usage = "Usage: %prog [-t TILES] [-z ZOOM] [-o OUTPUT] IMAGE1 ..."
    parser = OptionParser(usage=usage)

    config = OptionGroup(parser, "Configuration Options")
    config.add_option("-t", "--tiles", dest="tiles", default=None,
                      help="Number of tiles per side -- defaults to maxing # by sources.", metavar="TILES")
    config.add_option("-z", "--zoom", dest="zoom", default="1",
                      help="Zoom level of the mosaic.", metavar="ZOOM")
    config.add_option("-o", "--output", dest="output", default=None,
                      help="Save output instead of showing it.",
                      metavar="OUTPUT")
    config.add_option("-j", "--json", dest="jsonfile", default=None,
                      help="output file for json data on rectangles",
                      metavar="JSON")
    parser.add_option_group(config)

    return parser


def _main():
    """Run the command-line interface."""
    parser = _build_parser()
    (options, args) = parser.parse_args()

    if not args:
        parser.print_help()
        exit(1)

    mosaic = mosaicify(
        target=args[0],
        sources=set(args[1:] or args),
        tiles=options.tiles,
        zoom=int(options.zoom),
        jsonfile=options.jsonfile
    )

    if options.output is None:
        mosaic.show()
    else:
        mosaic.save(options.output)


if __name__ == '__main__':
    _main()
