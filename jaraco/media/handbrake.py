import os
import subprocess
import optparse

def get_handbrake_cmd():
	input = os.environ['DVD']
	return ['handbrake', '-i', input, '-N', 'eng']

def get_titles():
	title_no = eval(raw_input('enter starting DVD title number> '))
	episode = eval(raw_input('enter starting episode> '))
	ext = '.mp4'
	while True:
		title = raw_input('enter title> ')
		if not title: return
		filename = '{episode:02} - {title}{ext}'.format(**vars())
		yield ['-t', str(title_no), '-o', filename]
		title_no += 1
		episode += 1

def quick_brake():
	title = raw_input("Movie title> ")
	dest = os.path.join(os.path.expanduser('~/Public/Videos/Movies'), title+'.mp4')
	cmd = get_handbrake_cmd() + ['-L', '-o', dest]
	subprocess.Popen(cmd).wait()

def multibrake():
	titles = get_titles()
	options, args = optparse.OptionParser().parse_args()
	for title in list(get_titles()):
		args = get_handbrake_cmd() + args + title
		subprocess.Popen(args).wait()
