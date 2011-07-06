# -*- coding: UTF-8 -*-

"""
Setup script for building jaraco.media distribution

Copyright © 2009-2010 Jason R. Coombs
"""

from setuptools import find_packages

__author__ = 'Jason R. Coombs <jaraco@jaraco.com>'

name = 'jaraco.media'

setup_params = dict(
	name = name,
	use_hg_version=True,
	description = 'DVD and other multimedia tools',
	author = 'Jason R. Coombs',
	author_email = 'jaraco@jaraco.com',
	url = 'http://bitbucket.org/'+name,
	packages = find_packages(),
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
			'rip-subtitles = jaraco.media.dvd:rip_subtitles',
			'crop-detect = jaraco.media.cropdetect:execute',
			'dvd-info = jaraco.media.dvd_info:main',
			'transcode = jaraco.media.dvd:transcode',
			'fix-fourcc = jaraco.media.dvd:fix_fourcc',
			'serve-index = jaraco.media.index:serve',
			'multibrake = jaraco.media.handbrake:multibrake',
			'quick-brake = jaraco.media.handbrake:quick_brake',
			'mkv-to-mp4 = jaraco.media.matroska:handle_command_line',
			],
	},
	install_requires=[
		'jaraco.util',
	],
	extras_require = {
	},
	dependency_links = [
	],
	tests_require=[
		'nose>=0.10',
	],
	test_suite = "nose.collector",
	setup_requires = [
		'hgtools',
	],
)

if __name__ == '__main__':
	from setuptools import setup
	setup(**setup_params)
