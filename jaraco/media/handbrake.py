from __future__ import print_function

import os
import subprocess
import optparse
import re
from threading import Thread

from jaraco.util import ui
from path import path
from jaraco.util.string import local_format as lf

from jaraco.windows import filesystem

from . import dvd
from . import config

def get_source():
	return os.environ.get('DVD', 'D:\\')

def source_is_high_def():
	blueray_dir = os.path.join(get_source(), 'BDMV')
	return os.path.isdir(blueray_dir)

def get_handbrake_cmd():
	quality = 22 if source_is_high_def() else 20
	return [
		'HandbrakeCLI', '-i', get_source(), '--subtitle', 'scan',
		'--subtitle-forced', '--native-language', 'eng',
		'--encoder', 'x264',
		'--quality', str(quality),
	]

def is_hidden(filepath):
	filepath = os.path.abspath(filepath)
	return filepath.startswith('.') or has_hidden_attribute(filepath)

def has_hidden_attribute(filepath):
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
	title_no = eval(raw_input('enter starting DVD title number> '))
	visible_files = sorted(file for file in root.files() if not file.is_hidden())
	if visible_files:
		last_file = visible_files[-1].basename()
		print('last file is', last_file)
		last_episode = int(re.match('\d+', last_file).group(0)) + 1
	else:
		last_episode = 1
	prompt = lf('enter starting episode [{last_episode}]> ')
	episode = eval(raw_input(prompt) or 'None') or last_episode
	ext = '.mp4'
	while True:
		title = raw_input('enter title> ')
		if not title: return
		yield TitleInfo(title_no, title, episode, root, ext)
		title_no += 1
		episode += 1

def quick_brake():
	name = dvd.infer_name()
	title = raw_input(lf("Movie title ({name})> ")) or name
	dest = config.movies_root / title + '.mp4'
	cmd = get_handbrake_cmd() + [
		'--main-feature',
		'-o', dest,
	]
	subprocess.Popen(cmd).wait()

def find_root():
	root = config.tv_root
	choices = [showdir.basename() for showdir in root.dirs()]
	show = ui.Menu(choices).get_choice('Choose show (blank for new)> ')
	if not show:
		show = raw_input('Show name> ')
	show_dir = root / show
	show_dir.makedirs_p()
	choices = [seasondir.basename() for seasondir in show_dir.dirs()]
	season = ui.Menu(choices).get_choice('Choose season (blank for new)> ')
	if not season:
		season = 'Season %d' % eval(raw_input('Season Number> '))
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
			t = Thread(target=proc.communicate)
			t.start()
			return t

def multibrake():
	root = find_root()
	options, cmd_args = optparse.OptionParser().parse_args()
	threads = []
	for title in list(get_titles(root)):
		args = get_handbrake_cmd() + cmd_args + list(title)
		print('ripping', title)
		threads.append(two_stage_encode(args))
	[t.join() for t in threads if t]

def _link_to_title(lines):
	res = []
	for line in lines:
		title = re.match(r'\+ title (?P<title>\d+):', line)
		if title:
			res.append(dict(title=title.group('title')))
			continue
		m = re.match(r'  \+ (?P<key>.*): (?P<value>.*)', line)
		d = m.groupdict()
		res[-1].update({d['key']: d['value']})
	return res

def title_durations():
	cmd = get_handbrake_cmd() + ['-t', '0']
	print('scanning...')
	output = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
	lines = [
		line for line in output.splitlines()
		if '+ title' in line or '+ duration:' in line]
	lines = _link_to_title(lines)
	map(print, lines)
