# -*- coding: UTF-8 -*-

""" Setup script for building jaraco.media distribution

Copyright © 2009 Jason R. Coombs
"""

from ez_setup import use_setuptools
use_setuptools()
from setuptools import setup, find_packages

__author__ = 'Jason R. Coombs <jaraco@jaraco.com>'
__version__ = '$Rev$'[6:-2]
__svnauthor__ = '$Author$'[9:-2]
__date__ = '$Date$'[7:-2]

setup (name = 'jaraco.media',
		version = '1.0',
		description = 'DVD and other multimedia tools',
		author = 'Jason R. Coombs',
		author_email = 'jaraco@jaraco.com',
		url = 'http://www.jaraco.com/',
		packages = find_packages(exclude=['ez_setup', 'tests', 'examples']),
		namespace_packages = ['jaraco',],
		license = 'MIT',
		classifiers = [
			"Development Status :: 4 - Beta",
			"Intended Audience :: Developers",
			"Programming Language :: Python",
		],
		entry_points = {
			'console_scripts': [
				'encode-dvd = jaraco.media.dvd:encode_dvd',
				'crop-detect = jaraco.media.cropdetect:execute',
				'dvd-info = jaraco.media.dvd_info:main',
				'transcode = jaraco.media.dvd:transcode',
				'fix-fourcc = jaraco.media.dvd:fix_fourcc',
				],
		},
		install_requires=[
		],
		extras_require = {
		},
		dependency_links = [
		],
		tests_require=[
			'nose>=0.10',
		],
		test_suite = "nose.collector",
	)
