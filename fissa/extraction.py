"""
DataHandler classes to handle and manipulate image and ROI objects.

Authors:
    - Sander W Keemink <swkeemink@scimail.eu>
    - Scott C Lowe <scott.code.lowe@gmail.com>
"""

from past.builtins import basestring

try:
    from collections import abc
except ImportError:
    import collections as abc

import numpy as np
import tifffile
from PIL import Image, ImageSequence
import imageio

from . import roitools


class DataHandlerAbstract():
    """
    Abstract class for a data handler.

    Note
    ----
    - The `data` input into :meth:`getmean`, :meth:`rois2masks`, and
      :meth:`extracttraces` must be the same format as the output to
      :meth:`image2array`.
    - The `masks` input into :meth:`extracttraces` must be the same format
      as the output of :meth:`rois2masks`.

    See Also
    --------
    DataHandlerTifffile, DataHandlerPillow
    """
    @staticmethod
    def image2array(image):
        """
        Load data (from a path) as an array, or similar internal structure.

        Parameters
        ----------
        image : image_type
            Some handle to, or representation of, the raw imagery data.

        Returns
        -------
        data : data_type
            Internal representation of the images which will be used by all
            the other methods in this class.
        """
        raise NotImplementedError()

    @staticmethod
    def getmean(data):
        """
        Determine the mean image across all frames.

        Must return a 2D :class:`numpy.ndarray`.

        Parameters
        ----------
        data : data_type
            The same object as returned by :meth:`image2array`.

        Returns
        -------
        mean : numpy.ndarray
            Mean image as a 2D, y-by-x, array.
        """
        raise NotImplementedError()

    @staticmethod
    def rois2masks(rois, data):
        """
        Convert ROIs into a collection of binary masks.

        Parameters
        ----------
        rois : str or :term:`list` of :term:`array_like`
            Either a string containing a path to an ImageJ roi zip file,
            or a list of arrays encoding polygons, or list of binary arrays
            representing masks.
        data : data_type
            The same object as returned by :meth:`image2array`.

        Returns
        -------
        masks : mask_type
            Masks, in a format accepted by :meth:`extracttraces`.

        See Also
        --------
        fissa.roitools.getmasks, fissa.roitools.readrois
        """
        raise NotImplementedError()

    @staticmethod
    def extracttraces(data, masks):
        """
        Extract from data the average signal within each mask, across time.

        Must return a 2D :class:`numpy.ndarray`.

        Parameters
        ----------
        data : data_type
            The same object as returned by :meth:`image2array`.
        masks : mask_type
            The same object as returned by :meth:`rois2masks`.

        Returns
        -------
        traces : numpy.ndarray
            Trace for each mask, shaped ``(len(masks), n_frames)``.
        """
        raise NotImplementedError()


class DataHandlerTifffile(DataHandlerAbstract):
    """
    Extract data from TIFF images using tifffile.
    """
    @staticmethod
    def image2array(image):
        """
        Load a TIFF image from disk.

        Parameters
        ----------
        image : str or :term:`array_like`
            Either a path to a TIFF file, or :term:`array_like` data.

        Returns
        -------
        numpy.ndarray
            A 3D array containing the data, with dimensions corresponding to
            ``(frames, y_coordinate, x_coordinate)``.
        """
        if isinstance(image, basestring):
            return tifffile.imread(image)
        return np.array(image)

    @staticmethod
    def getmean(data):
        """
        Determine the mean image across all frames.

        Parameters
        ----------
        data : :term:`array_like`
            Data array as made by :meth:`image2array`, shaped ``(frames, y, x)``.

        Returns
        -------
        numpy.ndarray
            y by x array for the mean values
        """
        return data.mean(axis=0)

    @staticmethod
    def rois2masks(rois, data):
        """Take the object `rois` and returns it as a list of binary masks.

        Parameters
        ----------
        rois : str or :term:`list` of :term:`array_like`
            Either a string containing a path to an ImageJ roi zip file,
            or a list of arrays encoding polygons, or list of binary arrays
            representing masks.
        data : :term:`array_like`
            Data array as made by :meth:`image2array`. Must be shaped
            ``(frames, y, x)``.

        Returns
        -------
        masks : :term:`list` of :class:`numpy.ndarray`
            List of binary arrays.
        """
        # get the image shape
        shape = data.shape[1:]

        # if it's a list of strings
        if isinstance(rois, basestring):
            rois = roitools.readrois(rois)

        if not isinstance(rois, abc.Sequence):
            raise TypeError(
                'Wrong ROIs input format: expected a list or sequence, but got'
                ' a {}'.format(rois.__class__)
            )

        # if it's a something by 2 array (or vice versa), assume polygons
        if np.shape(rois[0])[1] == 2 or np.shape(rois[0])[0] == 2:
            return roitools.getmasks(rois, shape)
        # if it's a list of bigger arrays, assume masks
        elif np.shape(rois[0]) == shape:
            return rois

        raise ValueError('Wrong ROIs input format: unfamiliar shape.')

    @staticmethod
    def extracttraces(data, masks):
        """
        Extract a temporal trace for each spatial mask.

        Parameters
        ----------
        data : :term:`array_like`
            Data array as made by :meth:`image2array`, shaped ``(frames, y, x)``.
        masks : :class:`list` of :term:`array_like`
            List of binary arrays.

        Returns
        -------
        traces : numpy.ndarray
            Trace for each mask, shaped ``(len(masks), n_frames)``.
        """
        # get the number rois and frames
        nrois = len(masks)
        nframes = data.shape[0]

        # predefine output data
        out = np.zeros((nrois, nframes))

        # loop over masks
        for i in range(nrois):  # for masks
            # get mean data from mask
            out[i, :] = data[:, masks[i]].mean(axis=1)

        return out


class DataHandlerPillow(DataHandlerAbstract):
    """
    Extract data from TIFF images frame-by-frame using Pillow (:class:`PIL.Image`).

    Slower, but less memory-intensive than :class:`DataHandlerTifffile`.
    """
    @staticmethod
    def image2array(image):
        """
        Open an image file as a :class:`PIL.Image` instance.

        Parameters
        ----------
        image : str or file
            A filename (string) of a TIFF image file, a :class:`pathlib.Path`
            object, or a file object.

        Returns
        -------
        data : PIL.Image
            Handle from which frames can be loaded.
        """
        return Image.open(image)

    @staticmethod
    def getmean(data):
        """
        Determine the mean image across all frames.

        Parameters
        ----------
        data : PIL.Image
            An open :class:`PIL.Image` handle to a multi-frame TIFF image.

        Returns
        -------
        mean : numpy.ndarray
            y-by-x array for the mean values.
        """
        # We don't load the entire image into memory at once, because
        # it is likely to be rather large.
        # Initialise holding array with zeros
        avg = np.zeros(data.size[::-1])

        # Make sure we seek to the first frame before iterating. This is
        # because the Iterator outputs the value for the current frame for
        # `img` first, due to a bug in Pillow<=3.1.
        data.seek(0)

        # Loop over all frames and sum the pixel intensities together
        for frame in ImageSequence.Iterator(data):
            avg += np.asarray(frame)

        # Divide by number of frames to find the average
        avg /= data.n_frames
        return avg

    @staticmethod
    def rois2masks(rois, data):
        """
        Take the object `rois` and returns it as a list of binary masks.

        Parameters
        ----------
        rois : str or :term:`list` of :term:`array_like`
            Either a string containing a path to an ImageJ roi zip file,
            or a list of arrays encoding polygons, or list of binary arrays
            representing masks.
        data : PIL.Image
            An open :class:`PIL.Image` handle to a multi-frame TIFF image.

        Returns
        -------
        masks : list of numpy.ndarray
            List of binary arrays.
        """
        # get the image shape
        shape = data.size[::-1]

        # If rois is string, we first need to read the contents of the file
        if isinstance(rois, basestring):
            rois = roitools.readrois(rois)

        if not isinstance(rois, abc.Sequence):
            raise TypeError(
                'Wrong ROIs input format: expected a list or sequence, but got'
                ' a {}'.format(rois.__class__)
            )

        # if it's a something by 2 array (or vice versa), assume polygons
        if np.shape(rois[0])[1] == 2 or np.shape(rois[0])[0] == 2:
            return roitools.getmasks(rois, shape)
        # if it's a list of bigger arrays, assume masks
        elif np.shape(rois[0]) == shape:
            return rois

        raise ValueError('Wrong ROIs input format: unfamiliar shape.')

    @staticmethod
    def extracttraces(data, masks):
        """
        Extract the average signal within each mask across the data.

        Parameters
        ----------
        data : PIL.Image
            An open :class:`PIL.Image` handle to a multi-frame TIFF image.
        masks : list of :term:`array_like`
            List of binary arrays.

        Returns
        -------
        traces : numpy.ndarray
            Trace for each mask, shaped ``(len(masks), n_frames)``.
        """
        # get the number rois
        nrois = len(masks)

        # get number of frames, and start at zeros
        data.seek(0)
        nframes = data.n_frames

        # predefine array with the data
        out = np.zeros((nrois, nframes))

        # for each frame, get the data
        for f in range(nframes):
            # set frame
            data.seek(f)

            # make numpy array
            curframe = np.asarray(data)

            # loop over masks
            for i in range(nrois):
                # get mean data from mask
                out[i, f] = np.mean(curframe[masks[i]])

        return out
