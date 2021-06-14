'''Unit tests for core.py.'''

from __future__ import division

from datetime import datetime
import random
import os, os.path
import shutil
import unittest

import numpy as np

from .base_test import BaseTestCase
from .. import core
from ..extraction import DataHandlerTifffile


class TestExperimentA(BaseTestCase):
    '''Test Experiment class and its methods.'''

    def __init__(self, *args, **kw):
        super(TestExperimentA, self).__init__(*args, **kw)

        self.resources_dir = os.path.join(self.test_directory, 'resources', 'a')
        self.output_dir = os.path.join(
            self.resources_dir,
            'out-{}-{:06d}'.format(
                datetime.now().strftime('%H%M%S%f'),
                random.randrange(999999)
            )
        )
        self.images_dir = os.path.join(self.resources_dir, 'images')
        self.image_names = ['AVG_A01_R1_small.tif']
        self.image_shape = (8, 17)
        self.roi_zip_path = os.path.join(self.resources_dir, 'rois.zip')
        self.roi_paths = [os.path.join('rois', r) for r in ['01.roi']]

        self.expected_00 = np.array([
           [11.25423074,  0.        ,  0.        ,  7.55432252, 19.11182766,
             0.        ,  6.37473238,  0.        ,  0.        ,  0.        ,
             0.        ,  1.58567319,  2.28185467,  0.        , 16.70204514,
            17.55112746, 17.23642459,  0.        ,  0.        ,  0.        ,
             0.        ,  0.        ,  0.        ,  0.        ,  0.        ,
             0.        ,  0.        ,  0.        , 14.75392227],
           [89.75326173, 81.33290066, 88.77502093, 80.71108594, 85.5315738 ,
            78.42423771, 80.3659251 , 84.46124736, 78.04229961, 81.48360449,
            82.12879963, 83.11862592, 83.09085808, 91.22418523, 86.42399606,
            81.05860567, 86.15497276, 81.53903092, 80.53875696, 83.41061814,
            80.59332446, 81.64495893, 86.26057223, 82.47622273, 83.28735277,
            84.00697623, 83.68517083, 83.19829805, 82.06518458],
           [ 0.        ,  0.        ,  0.        ,  0.        ,  0.        ,
             0.        ,  0.        ,  0.        ,  0.        ,  0.        ,
             0.        ,  0.        ,  0.        ,  0.        ,  0.        ,
             0.        ,  0.        ,  0.        ,  0.        ,  0.        ,
             0.        ,  0.        ,  0.        ,  0.        ,  0.        ,
             0.        ,  0.        ,  0.        ,  0.        ],
           [ 0.        ,  0.        ,  0.        ,  0.        ,  0.        ,
             0.        ,  0.        ,  0.        ,  0.        ,  0.        ,
             0.        ,  0.        ,  0.        ,  0.        ,  0.        ,
             0.        ,  0.        ,  0.        ,  0.        ,  0.        ,
             0.        ,  0.        ,  0.        ,  0.        ,  0.        ,
             0.        ,  0.        ,  0.        ,  0.        ],
           [ 0.        ,  0.        ,  0.        ,  0.        ,  0.        ,
             0.        ,  0.        ,  0.        ,  0.        ,  0.        ,
             0.        ,  0.        ,  0.        ,  0.        ,  0.        ,
             0.        ,  0.        ,  0.        ,  0.        ,  0.        ,
             0.        ,  0.        ,  0.        ,  0.        ,  0.        ,
             0.        ,  0.        ,  0.        ,  0.        ],
        ])

    def setUp(self):
        self.tearDown()

    def tearDown(self):
        if os.path.isdir(self.output_dir):
            shutil.rmtree(self.output_dir)

    def test_imagedir_roizip(self):
        exp = core.Experiment(self.images_dir, self.roi_zip_path)
        exp.separate()
        actual = exp.result
        self.assert_equal(len(actual), 1)
        self.assert_equal(len(actual[0]), 1)
        self.assert_allclose(actual[0][0], self.expected_00)
        self.assert_equal(exp.means[0].shape, self.image_shape)
        self.assert_equal(exp.means[-1].shape, self.image_shape)

    def test_imagelist_roizip(self):
        image_paths = [
            os.path.join(self.images_dir, img)
            for img in self.image_names
        ]
        exp = core.Experiment(image_paths, self.roi_zip_path)
        exp.separate()
        actual = exp.result
        self.assert_equal(len(actual), 1)
        self.assert_equal(len(actual[0]), 1)
        self.assert_allclose(actual[0][0], self.expected_00)
        self.assert_equal(len(exp.means), len(image_paths))
        self.assert_equal(exp.means[0].shape, self.image_shape)
        self.assert_equal(exp.means[-1].shape, self.image_shape)

    def test_imagelistloaded_roizip(self):
        image_paths = [
            os.path.join(self.images_dir, img)
            for img in self.image_names
        ]
        datahandler = DataHandlerTifffile()
        images = [datahandler.image2array(pth) for pth in image_paths]
        exp = core.Experiment(images, self.roi_zip_path)
        exp.separate()
        actual = exp.result
        self.assert_equal(len(actual), 1)
        self.assert_equal(len(actual[0]), 1)
        self.assert_allclose(actual[0][0], self.expected_00)
        self.assert_equal(len(exp.means), len(image_paths))
        self.assert_equal(exp.means[0].shape, self.image_shape)
        self.assert_equal(exp.means[-1].shape, self.image_shape)

    @unittest.expectedFailure
    def test_imagedir_roilistpath(self):
        roi_paths = [
            os.path.join(self.resources_dir, r)
            for r in self.roi_paths
        ]
        exp = core.Experiment(self.images_dir, roi_paths)
        exp.separate()
        actual = exp.result
        self.assert_equal(len(actual), 1)
        self.assert_equal(len(actual[0]), 1)
        self.assert_allclose(actual[0][0], self.expected_00)
        self.assert_equal(exp.means[0].shape, self.image_shape)
        self.assert_equal(exp.means[-1].shape, self.image_shape)

    @unittest.expectedFailure
    def test_imagelist_roilistpath(self):
        image_paths = [
            os.path.join(self.images_dir, img)
            for img in self.image_names
        ]
        roi_paths = [
            os.path.join(self.resources_dir, r)
            for r in self.roi_paths
        ]
        exp = core.Experiment(image_paths, roi_paths)
        exp.separate()
        actual = exp.result
        self.assert_equal(len(actual), 1)
        self.assert_equal(len(actual[0]), 1)
        self.assert_allclose(actual[0][0], self.expected_00)
        self.assert_equal(len(exp.means), len(image_paths))
        self.assert_equal(exp.means[0].shape, self.image_shape)
        self.assert_equal(exp.means[-1].shape, self.image_shape)

    def test_nocache(self):
        exp = core.Experiment(self.images_dir, self.roi_zip_path)
        exp.separate()
        actual = exp.result
        self.assert_equal(len(actual), 1)
        self.assert_equal(len(actual[0]), 1)
        self.assert_allclose(actual[0][0], self.expected_00)
        self.assert_equal(exp.means[0].shape, self.image_shape)
        self.assert_equal(exp.means[-1].shape, self.image_shape)

    def test_ncores_preparation_1(self):
        exp = core.Experiment(
            self.images_dir,
            self.roi_zip_path,
            ncores_preparation=1,
        )
        exp.separate()
        actual = exp.result
        self.assert_equal(len(actual), 1)
        self.assert_equal(len(actual[0]), 1)
        self.assert_allclose(actual[0][0], self.expected_00)
        self.assert_equal(exp.means[0].shape, self.image_shape)
        self.assert_equal(exp.means[-1].shape, self.image_shape)

    def test_ncores_preparation_2(self):
        exp = core.Experiment(
            self.images_dir,
            self.roi_zip_path,
            ncores_preparation=2,
        )
        exp.separate()
        actual = exp.result
        self.assert_equal(len(actual), 1)
        self.assert_equal(len(actual[0]), 1)
        self.assert_allclose(actual[0][0], self.expected_00)
        self.assert_equal(exp.means[0].shape, self.image_shape)
        self.assert_equal(exp.means[-1].shape, self.image_shape)

    def test_ncores_separate_1(self):
        exp = core.Experiment(
            self.images_dir,
            self.roi_zip_path,
            ncores_separation=1,
        )
        exp.separate()
        actual = exp.result
        self.assert_equal(len(actual), 1)
        self.assert_equal(len(actual[0]), 1)
        self.assert_allclose(actual[0][0], self.expected_00)
        self.assert_equal(exp.means[0].shape, self.image_shape)
        self.assert_equal(exp.means[-1].shape, self.image_shape)

    def test_ncores_separate_2(self):
        exp = core.Experiment(
            self.images_dir,
            self.roi_zip_path,
            ncores_separation=2,
        )
        exp.separate()
        actual = exp.result
        self.assert_equal(len(actual), 1)
        self.assert_equal(len(actual[0]), 1)
        self.assert_allclose(actual[0][0], self.expected_00)
        self.assert_equal(exp.means[0].shape, self.image_shape)
        self.assert_equal(exp.means[-1].shape, self.image_shape)

    def test_lowmemorymode(self):
        exp = core.Experiment(
            self.images_dir,
            self.roi_zip_path,
            lowmemory_mode=True,
        )
        exp.separate()
        actual = exp.result
        self.assert_equal(len(actual), 1)
        self.assert_equal(len(actual[0]), 1)
        self.assert_allclose(actual[0][0], self.expected_00)
        self.assert_equal(exp.means[0].shape, self.image_shape)
        self.assert_equal(exp.means[-1].shape, self.image_shape)

    def test_manualhandler(self):
        exp = core.Experiment(
            self.images_dir,
            self.roi_zip_path,
            self.output_dir,
            datahandler=DataHandlerTifffile(),
        )
        exp.separate()
        actual = exp.result
        self.assert_equal(len(actual), 1)
        self.assert_equal(len(actual[0]), 1)
        self.assert_allclose(actual[0][0], self.expected_00)
        self.assert_equal(exp.means[0].shape, self.image_shape)
        self.assert_equal(exp.means[-1].shape, self.image_shape)

    def test_caching(self):
        exp = core.Experiment(self.images_dir, self.roi_zip_path, self.output_dir)
        exp.separate()

    def test_prefolder(self):
        os.makedirs(self.output_dir)
        exp = core.Experiment(self.images_dir, self.roi_zip_path, self.output_dir)
        exp.separate()

    def test_cache_pwd_explict(self):
        """Check we can use pwd as the cache folder"""
        prevdir = os.getcwd()
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
        try:
            os.chdir(self.output_dir)
            exp = core.Experiment(self.images_dir, self.roi_zip_path, ".")
            exp.separate()
        finally:
            os.chdir(prevdir)

    def test_cache_pwd_implicit(self):
        """Check we can use pwd as the cache folder"""
        prevdir = os.getcwd()
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
        try:
            os.chdir(self.output_dir)
            exp = core.Experiment(self.images_dir, self.roi_zip_path, "")
            exp.separate()
        finally:
            os.chdir(prevdir)

    def test_subfolder(self):
        """Check we can write to a subfolder"""
        output_dir = os.path.join(self.output_dir, "a", "b", "c")
        exp = core.Experiment(self.images_dir, self.roi_zip_path, output_dir)
        exp.separate()

    def test_folder_deleted_before_call(self):
        """Check we can write to a folder that is deleted in the middle"""
        exp = core.Experiment(self.images_dir, self.roi_zip_path, self.output_dir)
        # Delete the folder between instantiating Experiment and separate()
        self.tearDown()
        exp.separate()

    def test_folder_deleted_between_prep_sep(self):
        """Check we can write to a folder that is deleted in the middle"""
        exp = core.Experiment(self.images_dir, self.roi_zip_path, self.output_dir)
        # Delete the folder between separation_prep() and separate()
        exp.separation_prep()
        self.tearDown()
        exp.separate()

    def test_prepfirst(self):
        exp = core.Experiment(self.images_dir, self.roi_zip_path, self.output_dir)
        exp.separation_prep()
        exp.separate()
        actual = exp.result
        self.assert_equal(len(actual), 1)
        self.assert_equal(len(actual[0]), 1)
        self.assert_allclose(actual[0][0], self.expected_00)
        self.assert_equal(exp.means[0].shape, self.image_shape)
        self.assert_equal(exp.means[-1].shape, self.image_shape)

    def test_redo(self):
        """Test whether experiment redoes work when requested."""
        exp = core.Experiment(self.images_dir, self.roi_zip_path, self.output_dir)
        capture_pre = self.capsys.readouterr()  # Clear stdout
        exp.separate()
        capture_post = self.recapsys(capture_pre)
        self.assert_starts_with(capture_post.out, "Doing")
        capture_pre = self.capsys.readouterr()  # Clear stdout
        exp.separate(redo_prep=True, redo_sep=True)
        capture_post = self.recapsys(capture_pre)
        self.assert_starts_with(capture_post.out, "Doing")

    def test_load_cache(self):
        """Test whether cached output is loaded during init."""
        image_path = self.images_dir
        roi_path = self.roi_zip_path
        # Run an experiment to generate the cache
        exp1 = core.Experiment(image_path, roi_path, self.output_dir)
        exp1.separate()
        # Make a new experiment we will test
        exp = core.Experiment(image_path, roi_path, self.output_dir)
        # Cache should be loaded without calling separate
        actual = exp.result
        self.assert_equal(len(actual), 1)
        self.assert_equal(len(actual[0]), 1)
        self.assert_allclose(actual[0][0], self.expected_00)
        self.assert_equal(exp.means[0].shape, self.image_shape)
        self.assert_equal(exp.means[-1].shape, self.image_shape)

    def test_load_cache_piecemeal(self):
        """
        Test whether cached output is loaded during individual method calls.
        """
        image_path = self.images_dir
        roi_path = self.roi_zip_path
        # Run an experiment to generate the cache
        exp1 = core.Experiment(image_path, roi_path, self.output_dir)
        exp1.separate()
        # Make a new experiment we will test; this should load the cache
        capture_pre = self.capsys.readouterr()  # Clear stdout
        exp = core.Experiment(image_path, roi_path, self.output_dir)
        capture_post = self.recapsys(capture_pre)  # Capture and then re-output
        self.assert_starts_with(capture_post.out, "Reloading data")
        # Ensure previous cache is loaded again when we run separation_prep
        capture_pre = self.capsys.readouterr()  # Clear stdout
        exp.separation_prep()
        capture_post = self.recapsys(capture_pre)
        self.assert_starts_with(capture_post.out, "Reloading data")
        # Ensure previous cache is loaded again when we run separate
        capture_pre = self.capsys.readouterr()  # Clear stdout
        exp.separate()
        capture_post = self.recapsys(capture_pre)
        self.assert_starts_with(capture_post.out, "Reloading data")
        # Check the contents loaded from cache
        actual = exp.result
        self.assert_equal(len(actual), 1)
        self.assert_equal(len(actual[0]), 1)
        self.assert_allclose(actual[0][0], self.expected_00)
        self.assert_equal(exp.means[0].shape, self.image_shape)
        self.assert_equal(exp.means[-1].shape, self.image_shape)

    def test_load_cached_prep(self):
        """
        With prep cached, test prep loads and separate waits for us to call it.
        """
        image_path = self.images_dir
        roi_path = self.roi_zip_path
        # Run an experiment to generate the cache
        exp1 = core.Experiment(image_path, roi_path, self.output_dir)
        exp1.separation_prep()
        # Make a new experiment we will test; this should load the cache
        capture_pre = self.capsys.readouterr()  # Clear stdout
        exp = core.Experiment(image_path, roi_path, self.output_dir)
        capture_post = self.recapsys(capture_pre)  # Capture and then re-output
        self.assert_starts_with(capture_post.out, "Reloading data")
        # Ensure previous cache is loaded again when we run separation_prep
        capture_pre = self.capsys.readouterr()  # Clear stdout
        exp.separation_prep()
        capture_post = self.recapsys(capture_pre)  # Capture and then re-output
        self.assert_starts_with(capture_post.out, "Reloading data")
        # Since we did not run and cache separate, this needs to run now
        capture_pre = self.capsys.readouterr()  # Clear stdout
        exp.separate()
        capture_post = self.recapsys(capture_pre)
        self.assert_starts_with(capture_post.out, "Doing signal separation")
        # Check the contents loaded from cache
        actual = exp.result
        self.assert_equal(len(actual), 1)
        self.assert_equal(len(actual[0]), 1)
        self.assert_allclose(actual[0][0], self.expected_00)
        self.assert_equal(exp.means[0].shape, self.image_shape)
        self.assert_equal(exp.means[-1].shape, self.image_shape)

    @unittest.expectedFailure
    def test_badprepcache_init1(self):
        """
        With a faulty prep cache, test prep hits an error during init and then stops.
        """
        image_path = self.images_dir
        roi_path = self.roi_zip_path
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
        # Make a bad cache
        with open(os.path.join(self.output_dir, "preparation.npz"), "w") as f:
            f.write("badfilecontents")

        capture_pre = self.capsys.readouterr()  # Clear stdout
        exp = core.Experiment(image_path, roi_path, self.output_dir)
        capture_post = self.recapsys(capture_pre)  # Capture and then re-output
        self.assertTrue("An error occurred" in capture_post.out)

        self.assertTrue(exp.raw is None)

    @unittest.expectedFailure
    def test_badprepcache_init2(self):
        """
        With a faulty prep cache, test prep initially errors but then runs when called.
        """
        image_path = self.images_dir
        roi_path = self.roi_zip_path
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
        # Make a bad cache
        with open(os.path.join(self.output_dir, "preparation.npz"), "w") as f:
            f.write("badfilecontents")

        capture_pre = self.capsys.readouterr()  # Clear stdout
        exp = core.Experiment(image_path, roi_path, self.output_dir)
        capture_post = self.recapsys(capture_pre)  # Capture and then re-output
        self.assertTrue("An error occurred" in capture_post.out)

        capture_pre = self.capsys.readouterr()  # Clear stdout
        exp.separation_prep()
        capture_post = self.recapsys(capture_pre)  # Capture and then re-output
        self.assert_starts_with(capture_post.out, "Doing region growing")

    def test_badprepcache(self):
        """
        With a faulty prep cache, test prep catches error and runs when called.
        """
        image_path = self.images_dir
        roi_path = self.roi_zip_path
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
        exp = core.Experiment(image_path, roi_path, self.output_dir)
        # Make a bad cache
        with open(os.path.join(self.output_dir, "preparation.npz"), "w") as f:
            f.write("badfilecontents")

        capture_pre = self.capsys.readouterr()  # Clear stdout
        exp.separation_prep()
        capture_post = self.recapsys(capture_pre)  # Capture and then re-output
        self.assertTrue("An error occurred" in capture_post.out)

        capture_pre = self.capsys.readouterr()  # Clear stdout
        exp.separate()
        capture_post = self.recapsys(capture_pre)  # Capture and then re-output
        self.assert_starts_with(capture_post.out, "Doing signal separation")

        actual = exp.result
        self.assert_equal(len(actual), 1)
        self.assert_equal(len(actual[0]), 1)
        self.assert_allclose(actual[0][0], self.expected_00)

    def test_badsepcache(self):
        """
        With a faulty separated cache, test separate catches error and runs when called.
        """
        image_path = self.images_dir
        roi_path = self.roi_zip_path
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
        exp = core.Experiment(image_path, roi_path, self.output_dir)
        exp.separation_prep()
        # Make a bad cache
        with open(os.path.join(self.output_dir, "separated.npz"), "w") as f:
            f.write("badfilecontents")

        capture_pre = self.capsys.readouterr()  # Clear stdout
        exp.separate()
        capture_post = self.recapsys(capture_pre)  # Capture and then re-output
        self.assertTrue("An error occurred" in capture_post.out)

        actual = exp.result
        self.assert_equal(len(actual), 1)
        self.assert_equal(len(actual[0]), 1)
        self.assert_allclose(actual[0][0], self.expected_00)
        self.assert_equal(exp.means[0].shape, self.image_shape)
        self.assert_equal(exp.means[-1].shape, self.image_shape)

    def test_manual_save_prep(self):
        """Saving prep results with manually specified filename."""
        destination = os.path.join(self.output_dir, "m", ".test_output.npz")
        os.makedirs(os.path.dirname(destination))
        exp = core.Experiment(self.images_dir, self.roi_zip_path)
        exp.separation_prep()
        exp.save_prep(destination=destination)
        self.assertTrue(os.path.isfile(destination))

    def test_manual_save_sep(self):
        """Saving sep results with manually specified filename."""
        destination = os.path.join(self.output_dir, "m", ".test_output.npz")
        os.makedirs(os.path.dirname(destination))
        exp = core.Experiment(self.images_dir, self.roi_zip_path)
        exp.separate()
        exp.save_separated(destination=destination)
        self.assertTrue(os.path.isfile(destination))

    def test_manual_save_sep_undefined(self):
        """Saving prep results without specifying a filename."""
        exp = core.Experiment(self.images_dir, self.roi_zip_path)
        exp.separation_prep()
        with self.assertRaises(ValueError):
            exp.save_prep()

    def test_manual_save_prep_undefined(self):
        """Saving sep results without specifying a filename."""
        exp = core.Experiment(self.images_dir, self.roi_zip_path)
        exp.separate()
        with self.assertRaises(ValueError):
            exp.save_separated()

    def test_calcdeltaf(self):
        exp = core.Experiment(self.images_dir, self.roi_zip_path)
        exp.separate()
        exp.calc_deltaf(4)
        actual = exp.deltaf_result
        self.assert_equal(len(actual), 1)
        self.assert_equal(len(actual[0]), 1)
        #TODO: Check contents of exp.deltaf_result

    def test_calcdeltaf_cache(self):
        exp = core.Experiment(self.images_dir, self.roi_zip_path, self.output_dir)
        exp.separate()
        exp.calc_deltaf(4)
        actual = exp.deltaf_result
        self.assert_equal(len(actual), 1)
        self.assert_equal(len(actual[0]), 1)
        #TODO: Check contents of exp.deltaf_result

    def test_calcdeltaf_notrawf0(self):
        exp = core.Experiment(self.images_dir, self.roi_zip_path)
        exp.separate()
        exp.calc_deltaf(4, use_raw_f0=False)
        actual = exp.deltaf_result
        self.assert_equal(len(actual), 1)
        self.assert_equal(len(actual[0]), 1)
        #TODO: Check contents of exp.deltaf_result

    def test_calcdeltaf_notacrosstrials(self):
        exp = core.Experiment(self.images_dir, self.roi_zip_path)
        exp.separate()
        exp.calc_deltaf(4, across_trials=False)
        actual = exp.deltaf_result
        self.assert_equal(len(actual), 1)
        self.assert_equal(len(actual[0]), 1)
        #TODO: Check contents of exp.deltaf_result

    def test_calcdeltaf_notrawf0_notacrosstrials(self):
        exp = core.Experiment(self.images_dir, self.roi_zip_path)
        exp.separate()
        exp.calc_deltaf(4, use_raw_f0=False, across_trials=False)
        actual = exp.deltaf_result
        self.assert_equal(len(actual), 1)
        self.assert_equal(len(actual[0]), 1)
        #TODO: Check contents of exp.deltaf_result

    def test_matlab(self):
        exp = core.Experiment(self.images_dir, self.roi_zip_path, self.output_dir)
        exp.separate()
        exp.save_to_matlab()
        expected_file = os.path.join(self.output_dir, 'matlab.mat')
        self.assertTrue(os.path.isfile(expected_file))
        #TODO: Check contents of the .mat file

    def test_matlab_custom_fname(self):
        exp = core.Experiment(self.images_dir, self.roi_zip_path, self.output_dir)
        exp.separate()
        fname = os.path.join(
            self.output_dir,
            'test_{}.mat'.format(random.randrange(999999))
        )
        exp.save_to_matlab(fname)
        self.assertTrue(os.path.isfile(fname))
        #TODO: Check contents of the .mat file

    def test_matlab_no_cache_no_fname(self):
        exp = core.Experiment(self.images_dir, self.roi_zip_path)
        exp.separate()
        self.assertRaises(ValueError, exp.save_to_matlab)

    def test_matlab_deltaf(self):
        exp = core.Experiment(self.images_dir, self.roi_zip_path, self.output_dir)
        exp.separate()
        exp.save_to_matlab()
        exp.calc_deltaf(4)
        exp.save_to_matlab()
        #TODO: Check contents of the .mat file
