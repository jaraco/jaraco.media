from __future__ import print_function

import os
import subprocess
import argparse
import re
import datetime
import threading
import importlib

import six
from jaraco.util import ui
from path import path
from jaraco.util.string import local_format as lf
try:
	from jaraco.windows.power import no_sleep
except ImportError:
	from jaraco.util.context import null_context as no_sleep

from . import dvd
from . import config

def source_is_high_def():
	blueray_dir = os.path.join(dvd.get_source(), 'BDMV')
	return os.path.isdir(blueray_dir)

def get_handbrake_cmd():
	quality = 22 if source_is_high_def() else 20
	return [
		'HandBrakeCLI', '-i', dvd.get_source(), '--subtitle', 'scan',
		'--subtitle-forced', '--native-language', 'eng',
		'--encoder', 'x264',
		'--quality', str(quality),
		# '--large-file',
	]

def is_hidden(filepath):
	filepath = os.path.abspath(filepath)
	return filepath.startswith('.') or has_hidden_attribute(filepath)

def has_hidden_attribute(filepath):
	try:
		filesystem = importlib.import_module('jaraco.windows.filesystem')
	except ImportError:
		return False
	return filesystem.GetFileAttributes(filepath).hidden

path.is_hidden = is_hidden

class TitleInfo(object):
	def __init__(self, title_no, title, episode, root, ext):
		self.__dict__.update(vars())
		del self.self

	def __iter__(self):
		"Return the parameters to handbrake to rip for this title"
		return iter(['-t', str(self.title_no), '-o', self.root / self.filename])

	@property
	def filename(self):
		return '{episode:02} - {title}{ext}'.format(**vars(self))

	def __str__(self):
		return self.title

def get_titles(root):
	title_durations()
	title_no = eval(six.moves.input('enter starting DVD title number> '))
	visible_files = sorted(file for file in root.files() if not file.is_hidden())
	if visible_files:
		last_file = visible_files[-1].basename()
		print('last file is', last_file)
		last_episode = int(re.match('\d+', last_file).group(0)) + 1
	else:
		last_episode = 1
	prompt = lf('enter starting episode [{last_episode}]> ')
	episode = eval(six.moves.input(prompt) or 'None') or last_episode
	ext = '.mp4'
	while True:
		title = six.moves.input('enter title> ')
		if not title: return
		yield TitleInfo(title_no, title, episode, root, ext)
		title_no += 1
		episode += 1

def quick_brake():
	name = dvd.infer_name()
	title = six.moves.input(lf("Movie title ({name})> ")) or name
	config.movies_root.isdir() or config.movies_root.makedirs()
	dest = config.movies_root / title + '.mp4'
	cmd = get_handbrake_cmd() + [
		'--main-feature',
		'-o', dest,
	]
	with no_sleep():
		subprocess.Popen(cmd).wait()

def find_root():
	root = config.tv_root
	choices = [showdir.basename() for showdir in root.dirs()]
	show = ui.Menu(choices).get_choice('Choose show (blank for new)> ')
	if not show:
		show = six.moves.input('Show name> ')
	show_dir = root / show
	show_dir.makedirs_p()
	choices = [seasondir.basename() for seasondir in show_dir.dirs()]
	season = ui.Menu(choices).get_choice('Choose season (blank for new)> ')
	if not season:
		season = 'Season %d' % eval(six.moves.input('Season Number> '))
	season_dir = show_dir / season
	season_dir.makedirs_p()
	return season_dir

def get_starts(stream, limit):
	"""
	Read lines from a stream, but only read the first `limit` bytes of each
	line (in order to read text from an incomplete line).
	"""
	while True:
		res = stream.read(limit)
		if not res: return
		yield res
		stream.readline()

def two_stage_encode(args):
	"""
	Handbrake does a rip/encode and then multiplexes (muxes) the audio
	with the encoded video. This function watches handbrake for when the
	multiplexing begins and then returns a thread that will complete the
	multiplexing so that another rip/encode job can proceed.
	"""
	proc = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
	for start in get_starts(proc.stdout, 7):
		if 'Muxing' in start:
			# start a thread to finish the process
			print('Muxing...')
			t = threading.Thread(target=proc.communicate)
			t.start()
			return t

def multibrake():
	root = find_root()
	parser = argparse.ArgumentParser()
	parser.add_arguments('rest', nargs=argparse.REMAINDER)
	rest = parser.parse_args().rest
	threads = []
	for title in list(get_titles(root)):
		args = get_handbrake_cmd() + rest + list(title)
		print('ripping', title)
		threads.append(two_stage_encode(args))
	[t.join() for t in threads if t]

def parse_duration(str):
	hours, minutes, seconds = map(int, str.split(':'))
	return datetime.timedelta(hours=hours, minutes=minutes, seconds=seconds)

def _link_to_title(lines):
	res = []
	for line in lines:
		title = re.match(r'\+ title (?P<title>\d+):', line)
		if title:
			res.append(dict(title=title.group('title')))
			continue
		m = re.match(r'  \+ (?P<key>.*): (?P<value>.*)', line)
		d = m.groupdict()
		key, value = d['key'], d['value']
		if key == 'duration':
			value = parse_duration(value)
		res[-1].update({key: value})
	return res

def more_than_ten_min(title):
	return 'duration' in title and title['duration'] > datetime.timedelta(minutes=10)

def title_durations():
	cmd = get_handbrake_cmd() + ['-t', '0']
	print('scanning...')
	output = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
	output = output.decode('utf-8')
	lines = [
		line for line in output.splitlines()
		if '+ title' in line or '+ duration:' in line]
	lines = _link_to_title(lines)
	lines = filter(more_than_ten_min, lines)
	print("Title durations:")
	[print(line['title'], line['duration']) for line in lines]
