#! python

import sys
import optparse
import re
import os
import subprocess
try:
	import win32api
except:
	pass
from os.path import join
from copy import deepcopy
from cStringIO import StringIO
import logging
from jaraco.util import flatten, ordinalth
from jaraco.media import cropdetect
from jaraco.media.arguments import *

log = logging.getLogger(__name__)

rangePattern = re.compile('(\d+)(?:-(\d+))?')
delimiterPattern = re.compile('\s*[, ;]\s*')

def guess_output_filename(name):
	"""
	>>> guess_output_filename('JEAN_DE_FLORETTE')
	'Jean De Florette'
	
	>>> guess_output_filename('')
	''
	"""
	names = name.split('_')
	names = map(str.capitalize, names)
	return ' '.join(names)

def infer_name(device):
	try:
		label = win32api.GetVolumeInformation(device)[0]
	except Exception:
		label = os.path.basename(device)
	return guess_output_filename(label)

class MEncoderCommand(object):
	"""
	>>> cmd = MEncoderCommand()
	>>> cmd.source = ['dvd://']
	>>> lavcopts = ColonDelimitedArgs(vcodec='libx264',threads='2',vbitrate='1200',autoaspect=None,)
	>>> cmd.video_options = HyphenArgs(lavcopts=lavcopts)
	>>> cmd2 = cmd.copy()
	>>> cmd_args = tuple(cmd.get_args())
	>>> cmd2_args = tuple(cmd2.get_args())
	>>> assert cmd_args == cmd2_args, '%s != %s' % (cmd_args, cmd2_args)
	"""
	
	exe_path = [r'c:\Program Files (x86)\Slysoft\CloneDVDmobile\apps\mencoder.exe']
	
	def __init__(self):
		self.other_options = HyphenArgs()

	def copy(self):
		result = MEncoderCommand()
		# we need to do a deep copy so we make copies of all the args
		result.__dict__.update(deepcopy(self.__dict__))
		return result

	def get_args(self):
		arg_order = 'exe_path', 'source', 'device', 'video_filter', 'video_options', 'audio_options', 'other_options'
		assert getattr(self, 'source', None) is not None
		for arg in arg_order:
			arg = getattr(self, arg, None)
			if arg is None: continue
			for value in arg:
				yield str(value)
	
	def set_device(self, value):
		assert os.path.exists(value), "Couldn't find device %s" % value
		self.device = HyphenArgs({'dvd-device': value})
		
	def __setitem__(self, key, value):
		self.other_options[key]=value
	
	def __getitem__(self, key):
		return self.other_options[key]

def expandRange(title_range):
	start, stop = rangePattern.match(title_range)
	stop = stop or start
	return range(int(start), int(stop) + 1)

def getTitles(title_spec_string):
	title_specs = delimiterPattern.split(title_spec_string)
	title_specs = flatten(map(expandRange, title_specs))

class MultiPassHandler(object):
	def __init__(self, command, passes=2):
		self.command = command.copy()
		self.setup_log_file()
		self.passes = passes

	def setup_log_file(self):
		#multi_pass_temp_file = join(os.environ['USERPROFILE'], 'Videos', '%(user_title)s_pass.log' % vars())
		filename, ext = os.path.splitext(self.command.other_options['o'])
		multi_pass_temp_file = filename + '_pass.log'
		self.command['passlogfile'] = multi_pass_temp_file

	def __iter__(self):
		for current_pass in range(1, self.passes+1):
			current_pass_th = ordinalth(current_pass)
			log.info('Modifying command for %s pass.' % current_pass_th)
			method = [self.early_pass, self.last_pass][current_pass == self.passes]
			yield method(current_pass)
	
	def early_pass(self, pass_number):
		command = self.command.copy()
		command.audio_options=HyphenArgs(nosound=None)
		command.video_options['lavcopts'].update(turbo=None, vpass=str(pass_number))
		command['o'] = os.path.devnull
		return command

	def last_pass(self, pass_number):
		command = self.command.copy()
		command.video_options['lavcopts'].update(vpass=str(pass_number))
		return command

	def __del__(self):
		self.cleanup_log_file()
		
	def cleanup_log_file(self):
		try:
			filename = self.command['passlogfile']
		except KeyError:
			return
		try:
			os.path.exists(filename) and os.remove(filename)
		except:
			log.error('Error removing logfile %s', filename)
		
def get_x264_options():
	lavcopts = ColonDelimitedArgs()
	lavcopts.update(vcodec='libx264')
	lavcopts.update(threads='2')
	lavcopts.update(vbitrate='1200')
	lavcopts.update(autoaspect=None)
	options=HyphenArgs()
	options.update(ovc='lavc')
	options.update(lavcopts=lavcopts)
	return options

def get_mpeg4_options():
	lavcopts = ColonDelimitedArgs()
	lavcopts.update(vcodec='mpeg4')
	lavcopts.update(vhq=None)
	lavcopts.update(vbitrate='1200')
	lavcopts.update(autoaspect=None)
	options=HyphenArgs()
	options.update(ovc='lavc')
	options.update(lavcopts=lavcopts)
	return options

def encode_dvd():
	logging.basicConfig(level=logging.INFO)
	
	parser = optparse.OptionParser()
	#parser.add_option('-t', '--titles', 'enter the title or titles to process (i.e. 1 or 1,5 or 1-5)' default='')
	parser.add_option('-t', '--title', help='enter the dvd title number to process', default='')
	parser.add_option('-s', '--subtitle', help='enter the subtitle ID')
	options, args = parser.parse_args()

	command = MEncoderCommand()
	# todo, print "device" list
	rips = join(os.environ['USERPROFILE'], 'videos', 'rips')

	assert len(args) <= 1
	if args:
		device = args[0]
	else:
		device = raw_input('enter device> ')

	print 'device is', device
	command.set_device(device)

	videos_path = join(os.environ['PUBLIC'], 'Videos', 'Movies')

	default_title = infer_name(device)
	title_prompt = 'Enter output filename [%s]> ' % default_title
	user_title = raw_input(title_prompt) or default_title

	filename = '%(user_title)s.avi' % vars()
	target = os.path.join(videos_path, user_title)
	output_filename = os.path.join(videos_path, filename)

	command['o'] = output_filename
	
	dvd_title = options.title
	command.source = ['dvd://%(dvd_title)s' % vars()]
	
	audio_options = HyphenArgs(
		oac='copy',
		aid='128',
		)
	command.audio_options = audio_options

	crop = cropdetect.get_crop(device, dvd_title)
	log.info('crop is %s', crop)
	command.video_filter = HyphenArgs(
		sws='2',
		vf=ColonDelimitedArgs(crop=crop),
		)

	command.video_options = get_mpeg4_options()
	
	if options.subtitle:
		command['sid'] = options.subtitle

	assert not os.path.exists(command.other_options['o']), 'Output file %s alread exists' % command.other_options['o']

	errors = open('nul', 'w')
	two_pass_handler = MultiPassHandler(command)
	for _pass in two_pass_handler:
		_pass_args = tuple(_pass.get_args())
		print 'executing with', _pass_args
		proc = subprocess.Popen(_pass_args, stderr=errors)
		proc.wait()
		
	#C:\Users\jaraco\Public>"C:\Program Files (x86)\Slysoft\CloneDVDmobile\apps\mencoder.exe" -dvd-device "C:\Users\jaraco\Videos\rips\JEAN_DE_FLORETTE" dvd:// -sws 2 -vf crop=720:352:0:62 -nosound -ovc lavc -lavcopts vcodec=libx264:threads=2:vbitrate=1200:autoaspect:turbo:vpass=1  -sid 0 -o nul -passlogfile"C:\Users\jaraco\Videos\Jean de Florette_pass.log"  2>nul
