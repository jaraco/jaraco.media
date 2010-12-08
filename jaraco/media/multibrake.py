import subprocess
import optparse

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

def main():
	src = 'f:\\'
	titles = get_titles()
	options, args = optparse.OptionParser().parse_args()
	for title in list(get_titles()):
		args = ['handbrake', '-i', src, '-N', 'eng'] + args + title
		subprocess.Popen(args).wait()

if __name__ == '__main__': main()
