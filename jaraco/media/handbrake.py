from __future__ import print_function
import os
import subprocess
import optparse
from jaraco.util import ui
from path import path

def get_handbrake_cmd():
	input = os.environ.get('DVD', 'D:\\')
	return ['handbrake', '-i', input, '-N', 'eng']

def get_titles(root):
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
	title = raw_input("Movie title> ")
	dest = os.path.join(os.path.expanduser('~/Public/Videos/Movies'), title+'.mp4')
	cmd = get_handbrake_cmd() + ['-L', '-o', dest]
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

def multibrake():
	root = find_root()
	options, args = optparse.OptionParser().parse_args()
	for title in list(get_titles(root)):
		args = get_handbrake_cmd() + args + title
		subprocess.Popen(args).wait()
