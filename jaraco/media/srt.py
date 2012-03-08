import datetime
import itertools

_sample_srt_entries = """
1
00:00:25,080 --> 00:00:29,580
jaraco.media.srt presents

2
00:00:29,590 --> 00:00:33,660
An SRT Subtitle Parser

3
00:00:38,370 --> 00:00:47,870
Copyright ©2009-2010 Jason R. Coombs
Licensed for redistribution under the MIT license.

""".lstrip()

class SubEntry(object):
	r"""
	An SRT subtitle entry parser and manager.
	To get the SubEntry entries from an SRT file, just call get_entries
	on a filename or file-like object.

	>>> from StringIO import StringIO
	>>> sample = StringIO(_sample_srt_entries)
	>>> entries = SubEntry.get_entries(sample)

	Entries is now a generator which will parse the entries as they're
	requested. If you have enough memory to load them all in, then you
	can load them into a list or tuple.
	>>> entries = list(entries)

	>>> len(entries)
	3
	>>> entries[0].text
	['jaraco.media.srt presents\n']
	>>> entries[1].start
	datetime.timedelta(0, 29, 590000)

	Then, you can adjust when the entries occur. For example, this adds
	one second to the start and end times for the last subtitle.
	>>> entries[2] += datetime.timedelta(seconds=1)

	Finally, you can easily re-serialize the entries.
	>>> str(entries[2])
	'3\n00:00:39,370 --> 00:00:48,870\nCopyright \xa92009-2010 Jason R. Coombs\nLicensed for redistribution under the MIT license.\n'
	"""

	time_sep = ' --> '

	def __init__(self, index, start, stop, text):
		self.__dict__.update(vars())
		del self.__dict__['self']

	@staticmethod
	def get_entries(file):
		if isinstance(file, basestring):
			file = open(file)
		while True:
			yield SubEntry.get_entry(file)

	@staticmethod
	def get_entry(items):
		items = iter(items)
		index = int(next(items))
		start, stop = SubEntry.parse_span(next(items))
		is_not_blank = lambda s: bool(s.strip())
		text = list(itertools.takewhile(is_not_blank, items))
		return SubEntry(index, start, stop, text)

	@staticmethod
	def parse_span(span_string):
		times = span_string.split(SubEntry.time_sep)
		return map(SubEntry.parse_time, times)

	@staticmethod
	def parse_time(time_string):
		hr, min, sec = time_string.split(':')
		sec, msec = sec.split(',')
		return datetime.timedelta(
			hours = int(hr),
			minutes = int(min),
			seconds = int(sec),
			milliseconds = int(msec),
			)

	def __sub__(self, difference):
		"Subtract a time difference from the start and stop values"
		start = self.start - difference
		stop = self.stop - difference
		entry = SubEntry(self.index, start, stop, self.text)
		return entry

	def __add__(self, addition):
		"Add a time value to the start and stop values"
		start = self.start + addition
		stop = self.stop + addition
		entry = SubEntry(self.index, start, stop, self.text)
		return entry

	def format_span(self):
		times = map(self.format_time, [self.start, self.stop])
		return self.time_sep.join(times)

	@staticmethod
	def format_time(time):
		# python makes us construct a datetime object in order to get the desired
		#  time object in order to use strftime

		# pick some abitrary date
		dt = datetime.datetime(2000, 1, 1)
		# add our timedelta
		dt += time
		# extract the time
		time = dt.time()
		time_string = time.strftime('%H:%M:%S,%f')
		# strip the microseconds
		time_string = time_string[:-3]
		return time_string

	def __str__(self):
		items = [
			str(self.index),
			self.format_span(),
			''.join(self.text),
			]
		return '\n'.join(items)

	@staticmethod
	def write_entries(file, entries):
		if isinstance(file, basestring):
			file = open(file, 'w')
		for entry in entries:
			file.write(str(entry))
			file.write('\n')

	@staticmethod
	def adjust_entries(entries, adjustment):
		for entry in entries:
			yield entry + adjustment
