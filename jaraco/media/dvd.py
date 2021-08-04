import argparse
import re
import os
import subprocess
from os.path import join
from copy import deepcopy
import logging
import platform

import path
import inflect
from more_itertools import flatten

try:
    import win32api
except Exception:
    pass
from jaraco.text import trim, WordSet, FoldedCase

from jaraco.media import cropdetect
from jaraco.media.arguments import HyphenArgs, ColonDelimitedArgs

log = logging.getLogger(__name__)


rangePattern = re.compile(r'(\d+)(?:-(\d+))?')
delimiterPattern = re.compile(r'\s*[, ;]\s*')


def guess_output_filename(name):
    """
    >>> print(guess_output_filename('JEAN_DE_FLORETTE'))
    Jean De Florette

    >>> str(guess_output_filename(''))
    ''

    >>> str(guess_output_filename('COWBOYS_ALIENS_RENTAL'))
    'Cowboys Aliens'
    """
    rental = FoldedCase('rental')
    return WordSet.parse(name).trim_right(rental).capitalized().space_separated()


def get_source():
    default_device = path.Path('D:\\')
    if platform.system() == 'Linux':
        media = path.Path('/media')
        default_device = media.dirs()[0]
    if platform.system() == 'Darwin':
        volumes = path.Path('/Volumes')
        candidates = (
            subdir
            for subdir in volumes.dirs()
            if (subdir / 'BDMV').isdir() or (subdir / 'VIDEO_TS').isdir()
        )
        default_device = next(candidates, None)
    return os.environ.get('DVD', default_device)


def infer_name(device=None):
    device = device or get_source()
    try:
        label = win32api.GetVolumeInformation(device)[0]
    except Exception:
        label = os.path.basename(device)
    return guess_output_filename(label)


class MEncoderCommand:
    """
    >>> monkeypatch = getfixture('monkeypatch')
    >>> monkeypatch.setattr(
    ...     MEncoderCommand, 'find_mencoder_exe', lambda self: 'mencoder')
    >>> cmd = MEncoderCommand()
    >>> cmd.source = ['dvd://']
    >>> lavcopts = ColonDelimitedArgs(
    ...     vcodec='libx264',threads='2',vbitrate='1200',autoaspect=None,)
    >>> cmd.video_options = HyphenArgs(lavcopts=lavcopts)
    >>> cmd2 = cmd.copy()
    >>> cmd_args = tuple(cmd.get_args())
    >>> cmd2_args = tuple(cmd2.get_args())
    >>> assert cmd_args == cmd2_args, '%s != %s' % (cmd_args, cmd2_args)
    """

    def __init__(self):
        self.exe_path = [self.find_mencoder_exe()]
        self.other_options = HyphenArgs()

    @staticmethod
    def find_mencoder_exe():
        program_files = os.environ.get('PROGRAMFILES(X86)') or os.environ.get(
            'PROGRAMFILES'
        )
        search_path = [
            os.path.join(program_files, r'mencoder\mencoder.exe'),
        ]
        found = (path for path in search_path if os.path.exists(path))
        try:
            return next(found)
        except StopIteration:
            raise RuntimeError("Cannot find mencoder; admittedly didn't try very hard.")

    def copy(self):
        result = MEncoderCommand()
        # we need to do a deep copy so we make copies of all the args
        result.__dict__.update(deepcopy(self.__dict__))
        return result

    def get_args(self):
        arg_order = (
            'exe_path',
            'source',
            'device',
            'video_filter',
            'video_options',
            'audio_options',
            'other_options',
        )
        assert getattr(self, 'source', None) is not None
        for arg in arg_order:
            arg = getattr(self, arg, None)
            if arg is None:
                continue
            for value in arg:
                yield str(value)

    def set_device(self, value):
        assert os.path.exists(value), "Couldn't find device %s" % value
        self.device = HyphenArgs({'dvd-device': value})

    def __setitem__(self, key, value):
        self.other_options[key] = value

    def __getitem__(self, key):
        return self.other_options[key]


def expandRange(title_range):
    start, stop = rangePattern.match(title_range)
    stop = stop or start
    return range(int(start), int(stop) + 1)


def getTitles(title_spec_string):
    title_specs = delimiterPattern.split(title_spec_string)
    title_specs = flatten(map(expandRange, title_specs))


class MultiPassHandler:
    def __init__(self, command, passes=2):
        self.command = command.copy()
        self.setup_log_file()
        self.passes = passes

    def setup_log_file(self):
        filename, ext = os.path.splitext(self.command.other_options['o'])
        multi_pass_temp_file = filename + '_pass.log'
        self.command['passlogfile'] = multi_pass_temp_file

    def __iter__(self):
        inflect_eng = inflect.engine()
        for current_pass in range(1, self.passes + 1):
            current_pass_th = inflect_eng.ordinal(current_pass)
            log.info('Modifying command for %s pass.' % current_pass_th)
            method = [self.early_pass, self.last_pass][current_pass == self.passes]
            yield method(current_pass)

    def early_pass(self, pass_number):
        command = self.command.copy()
        command.audio_options = HyphenArgs(nosound=None)
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
        except Exception:
            log.error('Error removing logfile %s', filename)


def get_x264_options():
    lavcopts = ColonDelimitedArgs()
    lavcopts.update(vcodec='libx264')
    lavcopts.update(threads='2')
    lavcopts.update(vbitrate='1200')
    lavcopts.update(autoaspect=None)
    options = HyphenArgs()
    options.update(ovc='lavc')
    options.update(lavcopts=lavcopts)
    return options


def get_mpeg4_options():
    lavcopts = ColonDelimitedArgs()
    lavcopts.update(vcodec='mpeg4')
    lavcopts.update(vhq=None)
    lavcopts.update(vbitrate='1200')
    lavcopts.update(autoaspect=None)
    options = HyphenArgs()
    options.update(ovc='lavc')
    options.update(lavcopts=lavcopts)
    options.update(ffourcc='XVID')
    return options


def get_video_copy_options():
    return HyphenArgs(ovc='copy', ffourcc='XVID')


def get_audio_copy_options():
    return HyphenArgs(
        oac='copy',
    )


def get_mp3_options():
    return HyphenArgs(
        oac='mp3lame',
        lameopts=ColonDelimitedArgs(
            abr=None,
            br='96',
            vol='6',
        ),
    )


def encode_dvd():
    """
    %prog <dvd_source>

    Encode a DVD where the source is a DVD drive or RIP directory of a DVD.
    """
    parser = argparse.ArgumentParser(usage=trim(encode_dvd.__doc__))
    # parser.add_argument(
    #     '-t', '--titles',
    #     'enter the title or titles to process (i.e. 1 or 1,5 or 1-5)',
    #     default='')
    parser.add_argument(
        '-t', '--title', help='enter the dvd title number to process', default=''
    )
    parser.add_argument('-s', '--subtitle', help='enter the subtitle ID')
    parser.add_argument(
        '--test', help='just encode one chapter', default=False, action='store_true'
    )
    parser.add_argument(
        '-l',
        '--log-level',
        help='log level (debug, info, warning, error)',
        default='info',
    )
    parser.add_argument('device', nargs='?')
    args = parser.parse_args()

    logging.basicConfig(level=getattr(logging, args.log_level.upper()))

    command = MEncoderCommand()

    device = args.device or input('enter device> ')

    print('device is', device)
    command.set_device(device)

    videos_path = join(os.environ['PUBLIC'], 'Videos', 'Movies')

    default_title = infer_name(device)
    title_prompt = 'Enter output filename [%s]> ' % default_title
    user_title = input(title_prompt) or default_title

    filename = '%(user_title)s.avi' % vars()
    target = os.path.join(videos_path, user_title)
    output_filename = os.path.join(videos_path, filename)

    command['o'] = output_filename

    dvd_title = args.title
    command.source = ['dvd://%(dvd_title)s' % vars()]
    if args.test:
        command['chapter'] = '2-2'

    command.audio_options = get_audio_copy_options()
    command.audio_args.update(aid='128')

    crop = cropdetect.get_crop(device, dvd_title)
    log.info('crop is %s', crop)
    command.video_filter = HyphenArgs(
        sws='2',
        vf=ColonDelimitedArgs(crop=crop),
    )

    command.video_options = get_mpeg4_options()

    if args.subtitle:
        command['sid'] = args.subtitle
        command['vobsubout'] = target
        command['vobsuboutindex'] = '0'

    assert not os.path.exists(command.other_options['o']), (
        'Output file %s already exists' % command.other_options['o']
    )

    errors = open(os.devnull, 'w')
    two_pass_handler = MultiPassHandler(command)
    for _pass in two_pass_handler:
        _pass_args = tuple(_pass.get_args())
        log.debug('executing with %s', _pass_args)
        proc = subprocess.Popen(_pass_args, stderr=errors)
        proc.wait()


def re_encode(file, video_options, audio_options):
    command = MEncoderCommand()
    fn, ext = os.path.splitext(file)
    dest = ''.join((fn, ' (fixed)', ext))
    command['o'] = dest
    command.source = [file]
    command.audio_options = audio_options
    command.video_options = video_options
    errors = open(os.devnull, 'w')
    print('executing with', tuple(command.get_args()))
    proc = subprocess.Popen(command.get_args(), stderr=errors)
    if proc.wait() == 0:
        print('success')


def transcode():
    """
    %prog <source_file>

    Transcode a video by copying the video, but encoding the audio
    into mp3 format.
    """
    parser = argparse.ArgumentParser(usage=trim(fix_fourcc.__doc__))
    parser.add_argument('source')
    args = parser.parse_args()

    re_encode(args.source, get_video_copy_options(), get_mp3_options())


def fix_fourcc():
    """
    %prog <source_file>

    Re-encode the video, but change the ffourcc to XVID
    """
    parser = argparse.ArgumentParser(usage=trim(fix_fourcc.__doc__))
    parser.add_argument('source')
    options, args = parser.parse_args()

    re_encode(args.source, get_video_copy_options(), get_audio_copy_options())


def rip_subtitles():
    """
    %prog <dvd_source>
    """
    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser(usage=trim(encode_dvd.__doc__))
    parser.add_argument(
        '-t', '--title', help='enter the dvd title number to process', default=''
    )
    parser.add_argument('-s', '--subtitle', help='enter the subtitle ID')
    parser.add_argument('device', nargs='?')
    args = parser.parse_args()

    command = MEncoderCommand()

    device = args.device or input('enter device> ')

    print('device is', device)
    command.set_device(device)

    videos_path = join(os.environ['PUBLIC'], 'Videos', 'Movies')

    default_title = infer_name(device)
    title_prompt = 'Enter output filename [%s]> ' % default_title
    user_title = input(title_prompt) or default_title
    target = os.path.join(videos_path, user_title)

    command.source = ['dvd://%(title)s' % vars(args)]

    command['o'] = os.devnull

    command.audio_options = HyphenArgs(nosound=None)
    command.video_options = HyphenArgs(ovc='frameno')

    command['sid'] = args.subtitle or '0'

    command['vobsubout'] = target
    command['vobsuboutindex'] = command['sid']
    # command['vobsuboutid'] = 'en'

    command = tuple(command.get_args())
    errors = open(os.devnull, 'w')
    proc = subprocess.Popen(command, stderr=errors)
    proc.wait()


def update_anydvd():
    import jaraco.net.http

    url = 'http://static.slysoft.com/SetupAnyDVD.exe'
    file = jaraco.net.http.get_url(url)
    subprocess.check_call([file, '-S'])
    os.remove(file)
    os.remove(r'C:\Users\Public\Desktop\AnyDVD.lnk')
