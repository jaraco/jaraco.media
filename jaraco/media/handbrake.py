from __future__ import print_function
import os
import subprocess
import optparse
from jaraco.util import ui
from path import path
from threading import Thread
from jaraco.util.string import local_format as lf

from dvd import infer_name

def get_handbrake_cmd():
	input = os.environ.get('DVD', 'D:\\')
	return ['HandbrakeCLI', '-i', input, '-N', 'eng']

def get_titles(root):
	title_durations()
	title_no = eval(raw_input('enter starting DVD title number> '))
	if root.files():
		print('last is', sorted(root.files())[-1].basename())
	episode = eval(raw_input('enter starting episode> '))
	ext = '.mp4'
	while True:
		title = raw_input('enter title> ')
		if not title: return
		filename = '{episode:02} - {title}{ext}'.format(**vars())
		yield ['-t', str(title_no), '-o', root/filename]
		title_no += 1
		episode += 1

def quick_brake():
	name = infer_name()
	title = raw_input(lf("Movie title ({name})> ")) or name
	dest = os.path.join(os.path.expanduser('~/Public/Videos/Movies'), title+'.mp4')
	cmd = get_handbrake_cmd() + ['--main-feature', '-o', dest]
	subprocess.Popen(cmd).wait()

def find_root():
	root = path('~/Public/Videos/TV').expanduser()
	choices = [showdir.basename() for showdir in root.dirs()]
	show = ui.Menu(choices).get_choice('Choose show (blank for new)> ')
	if not show:
		show = raw_input('Show name> ')
	show_dir = root/show
	show_dir.makedirs_p()
	choices = [seasondir.basename() for seasondir in show_dir.dirs()]
	season = ui.Menu(choices).get_choice('Choose season (blank for new)> ')
	if not season:
		season = 'Season %d' % eval(raw_input('Season Number> '))
	season_dir = show_dir/season
	season_dir.makedirs_p()
	return season_dir

def two_stage_encode(args):
	proc = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
	for line in proc.stdout:
		if 'Muxing:' in line:
			# start a thread to finish the process
			print('Muxing.')
			t = Thread(target=proc.wait)
			t.start()
			return t
	
def multibrake():
	root = find_root()
	options, cmd_args = optparse.OptionParser().parse_args()
	threads = []
	for title in list(get_titles(root)):
		args = get_handbrake_cmd() + cmd_args + title
		print('running', args)
		threads.append(two_stage_encode(args))
	[t.join() for t in threads]

def title_durations():
	cmd = get_handbrake_cmd() + ['-t', '0']
	print('scanning...')
	output = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
	lines = [
		line for line in output.splitlines()
		if '+ title' in line or '+ duration:' in line]
	for line in lines: print(line)
