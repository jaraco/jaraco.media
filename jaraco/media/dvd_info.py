#!/usr/bin/python
# -*- coding: utf-8 -*-

u'''
routines for acquiring dvd details, based on dvdinfo.py (many thanks
to Sybren Stüvel, http://stuvel.eu/dvdinfo).
'''

import re
import sys
import datetime
from itertools import count
from optparse import OptionParser
from subprocess import Popen, PIPE, STDOUT

__author__ = '$Author$'[9:-2]
__email__ = 'jaraco@jaraco.com'
__revision__ = '$Rev$'[6:-2]
__url__ = 'http://www.jaraco.com'

def banner():
	'''Display the banner'''

	print 50*'='
	print '%s version %s' % (__name__, __revision__)
	print '%s <%s>' % (__author__, __email__)
	print __url__
	print 50*'='
	print

class MetaTitleParser(type):
	"""
	A metaclass for title parsers that keeps track of all of them.
	"""
	
	_all_parsers = set()
	
	def __init__(cls, name, bases, attrs):
		cls._all_parsers.add(cls)
		# remove any base classes
		cls._all_parsers -= set(bases)

class TitleParser(object):
	__metaclass__ = MetaTitleParser
	
	def __init__(self, info):
		# info is the object that stores title info
		self.info = info
		self.pattern = re.compile(self.pattern)
	
	def __call__(self, line):
		self.parse(line)

	def parse(self, line):
		match = self.pattern.search(line)
		match and self.handle(match)
	
	@classmethod
	def create_all(cls, info):
		"Create all of the title parsers associated with this info"
		return [parser(info) for parser in cls._all_parsers]

class MaxTitlesParser(TitleParser):
	pattern = '^There are (?P<max_titles>\d+) titles'
	def handle(self, match):
		self.info['max_titles'] = int(match.groupdict()['max_titles'])

class ChaptersParser(TitleParser):
	pattern = '^There are (?P<chapters>\d+) chapters'
	def handle(self, match):
		self.info['chapters'] = int(match.groupdict()['chapters'])

class AudioParser(TitleParser):
	pattern = '^audio stream: (?P<stream>\d+) format: (?P<format>.+) language: (?P<language>.+) aid: (?P<aid>\d+)'
	def handle(self, match):
		'''Parse a single audio-channel line'''
		d = match.groupdict()
		d['aid'] = int(d['aid'])
		self.info['audiotracks'][d['aid']] = d

class SubtitleParser(TitleParser):
	pattern = '^subtitle \(\s*sid\s*\): (?P<sid>\d+) language: (?P<language>.*)'
	def handle(self, match):
		'''Parse a single subtitle-channel line'''
		d = match.groupdict()
		d['sid'] = int(d['sid'])
		self.info['subtitles'].append(d)

class NaviParser(TitleParser):
	pattern = 'Found NAVI packet!'
	def handle(self, match):
		self.info['navi_count']+=1

class LengthParser(TitleParser):
	pattern = 'ID_LENGTH=(?P<length>[\d.]+)'
	def handle(self, match):
		length = float(match.groupdict()['length'])
		length = datetime.timedelta(seconds=length)
		self.info['length'] = length

class TitleInfo(dict):
	def __init__(self, *args, **kwargs):
		self.update(max_titles=0, chapters=0, audiotracks={}, subtitles=[], navi_count=0)
		dict.__init__(self, *args, **kwargs)

	def __str__(self):
		buffer = []
		buffer.append('Number: %(number)s' % self)
		buffer.append('Title length: %(length)s' % self)
		buffer.append('Chapters: %(chapters)s' % self)
		buffer.append('Audio tracks:')
		aud_fmt = '\taid=%(aid)3i lang=%(language)s fmt=%(format)s'
		fmt_aud_info = lambda i: aud_fmt % i
		buffer.extend(map(fmt_aud_info, self['audiotracks'].values()))
		buffer.append('Subtitles:')
		sub_fmt = '\tsid=%(sid)3i lang=%(language)s'
		fmt_sub_info = lambda i: sub_fmt % i
		buffer.extend(map(fmt_sub_info, self['subtitles']))
		return '\n'.join(buffer)
	
	def has_audio(self):
		return self['audiotracks']

def title_info(device, title):
	'''Get title information about a single title.
	
	expects device to be available globally.
	
	Returns a TitleInfo object
	'''

	# need at least two -v to get "Found NAVI packet"
	mpcmd = 'mplayer -v -v -v -identify -nosound -frames 0 -dvd-device %s dvd://%i -vo null'

	cmd = mpcmd % (device, title)
	mplayer = Popen(cmd, stdout=PIPE, stderr=STDOUT)

	info = TitleInfo(number=title)

	parsers = TitleParser.create_all(info)

	for line in mplayer.stdout:
		for parser in parsers:
			parser(line)
		if info['navi_count'] > 100: break
	
	return info

def main():
	longest_title_info = None

	banner()

	parser = OptionParser(usage=__doc__)
	parser.add_option('-t', '--title', help='only search a specific title', type=int, default=0)
	parser.add_option('-d', '--device', help='the device (default d:)', default='d:')
	options, args = parser.parse_args()
	
	if not len(args) == 0: parser.error('This program takes no arguments')

	if not options.title:
		titles = []
		max_title = '?'
		# Walk through all titles
		for title in count(1):
			if isinstance(max_title, int) and title > max_title: break
			sys.stdout.write('Reading title %i/%s   \r' % (title, max_title))
			sys.stdout.flush()

			info = title_info(options.device, title)
			titles.append(info)
			# Remember info about the title with the most chapters,
			# but only if it has audio tracks.
			if info['audiotracks'] and (longest_title_info is None or info['chapters'] > longest_title_info['chapters']):
				longest_title_info = info

			max_title = info['max_titles']

		print 'Done reading.            '

		titles_with_audio = filter(TitleInfo.has_audio, titles)
		titles_with_audio.sort(key=lambda t: -t['chapters'])

		if not titles_with_audio:
			raise SystemExit("Unable to find any titles with audio on %s" % options.device)
		
		for title in titles_with_audio:
			print
			print title
	else:
		print 'Reading title: %i' % options.title
		# Get info about given title
		info = title_info(options.device, options.title)

		print info

if __name__ == '__main__':
	main()

