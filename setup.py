#!/usr/bin/env python

# Project skeleton maintained at https://github.com/jaraco/skeleton

import io
import sys

import setuptools

with io.open('README.rst', encoding='utf-8') as readme:
	long_description = readme.read()

needs_pytest = {'pytest', 'test'}.intersection(sys.argv)
pytest_runner = ['pytest_runner'] if needs_pytest else []
needs_sphinx = {'release', 'build_sphinx', 'upload_docs'}.intersection(sys.argv)
sphinx = ['sphinx', 'rst.linker'] if needs_sphinx else []
needs_wheel = {'release', 'bdist_wheel'}.intersection(sys.argv)
wheel = ['wheel'] if needs_wheel else []

name = 'jaraco.media'
description = 'DVD and other multimedia tools'

setup_params = dict(
	name=name,
	use_scm_version=True,
	author="Jason R. Coombs",
	author_email="jaraco@jaraco.com",
	description=description or name,
	long_description=long_description,
	url="https://github.com/jaraco/" + name,
	packages=setuptools.find_packages(),
	include_package_data=True,
	namespace_packages=name.split('.')[:-1],
	install_requires=[
		'jaraco.itertools',
		'jaraco.text',
		'jaraco.ui',
		'jaraco.context',
		'httpagentparser',
		'six',
		'more_itertools',
		'path.py',
	],
	extras_require={
	},
	setup_requires=[
		'setuptools_scm>=1.9',
	] + pytest_runner + sphinx + wheel,
	tests_require=[
		'pytest>=2.8',
		'cherrypy',
		'mock',
		'genshi',
	],
	classifiers=[
		"Development Status :: 5 - Production/Stable",
		"Intended Audience :: Developers",
		"License :: OSI Approved :: MIT License",
		"Programming Language :: Python :: 2.7",
		"Programming Language :: Python :: 3",
	],
	entry_points={
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
			'update-anydvd = jaraco.media.dvd:update_anydvd',
		],
	},
)
if __name__ == '__main__':
	setuptools.setup(**setup_params)
