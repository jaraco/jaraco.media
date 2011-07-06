#!/usr/bin/python
# Little script to depack Matroska file, and repack them
# in an MP4 format.

import sys
import os
import argparse
import subprocess

from jaraco.util.string import local_format as lf

def message(msg):
    print "=" * 78
    print "= %s" % msg
    print "=" * 78

def get_args():
	parser = argparse.ArgumentParser()
	parser.add_argument('filename')
	return parser.parse_args()

def handle_command_line():
	args = get_args()
	filename = args.filename
	basename = os.path.basename(filename)
	name, ext = os.path.splitext(basename)
	message("Unpacking file: %s" % filename)
	subprocess.Popen([
		r'C:\Program Files (x86)\mkvtoolnix\mkvextract', # 'mkvextract',
		'tracks', filename,
		'2:temp_video.mp4',
		'1:temp_audio.ogg',
		#lf('3:{name}.srt'),
		]).wait()

	message(lf("Repacking file: {name}.mp4"))
	subprocess.Popen([
		r'C:\Program Files\ffmpeg-git-9251942-win64-shared\bin\ffmpeg.exe', #'ffmpeg',
		'-i', 'temp_audio.ogg', '-i', 'temp_video.mp4',
		'-vcodec', 'copy', #'libx264',
		'-r', '47.95',
		name+'.mp4',]).wait()

	message("Cleaning files")
	map(os.remove, ['temp_video.mp4', 'temp_audio.ogg'])

if __name__ == "__main__":
	handle_command_line()

