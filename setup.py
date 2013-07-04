# -*- coding: UTF-8 -*-

"""
Setup script for building jaraco.media distribution

Copyright © 2009-2011 Jason R. Coombs
"""

import sys
import platform
import collections

import setuptools

__author__ = 'Jason R. Coombs <jaraco@jaraco.com>'

name = 'jaraco.media'

py26reqs = ['jaraco.compat'] if sys.version_info < (2, 7) else []
platform_reqs = collections.defaultdict(list,
	Windows = ['jaraco.windows>=2.13']
)[platform.system()]

setup_params = dict(
	name = name,
	use_hg_version=True,
	description = 'DVD and other multimedia tools',
	author = 'Jason R. Coombs',
	author_email = 'jaraco@jaraco.com',
	url = 'http://bitbucket.org/jaraco/' + name,
	packages = setuptools.find_packages(),
	namespace_packages = ['jaraco'],
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
			'adjust-sub = jaraco.media.srt:AdjustCommand.run',
			],
	},
	install_requires=[
		'jaraco.util>=6.1',
		'httpagentparser',
	] + py26reqs + platform_reqs,
	extras_require = {
	},
	dependency_links = [
	],
	setup_requires = [
		'hgtools',
	],
	use_2to3=True,
)

if __name__ == '__main__':
	setuptools.setup(**setup_params)
