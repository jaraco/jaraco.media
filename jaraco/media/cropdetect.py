import re
import os
import itertools
import logging
import argparse

log = logging.getLogger(__name__)


def terminate(process):
    try:
        process.terminate()
    except WindowsError:
        pass  # process has probably already terminated on its own


class consecutive_count:
    def __init__(self):
        self.count = 0
        self.last = None

    def __call__(self, item):
        if item == self.last:
            self.count += 1
        else:
            self.count = 0
            self.last = item
        return self.count


def consecutive_same(items):
    """A generator that returns the count of consecutive
    preceeding items that match the current item.
    >>> tuple(consecutive_same([1,1,2,2,3,3,3]))
    (0, 1, 0, 1, 0, 1, 2)

    Note this will trivially produce zeros for most
    inputs.
    >>> tuple(consecutive_same([1,2,3]))
    (0, 0, 0)
    """
    counter = consecutive_count()
    return map(counter, items)


def within_consecutive_limit(limit):
    counter = consecutive_count()

    def within_limit(item):
        return counter(item) < limit

    return within_limit


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-t', '--title', help="The title to use", default="")
    parser.add_argument('device', nargs='?')
    args = parser.parse_args()
    title = args.title
    device = args.device
    log.info(['using default device', 'using device %s' % device][bool(device)])
    log.info(['using default title', 'using title %s' % title][bool(title)])
    return device, title


def build_command(dvd_device=None, title=""):
    from jaraco.media.dvd import MEncoderCommand, HyphenArgs

    command = MEncoderCommand()
    command.source = ['dvd://%(title)s' % vars()]
    command.audio_options = HyphenArgs(nosound=None)
    limit = 24
    round = 16
    command.video_filter = HyphenArgs(vf='cropdetect=%(limit)s:%(round)s' % locals())
    command.video_options = HyphenArgs(ovc='lavc')
    command['o'] = os.path.devnull
    # command['ss'] = '20' # skip the first 20 seconds
    # As a rule-of-thumb, use the 2nd or 3rd chapter to determine the crop;
    #  The first chapter can tend to have a different format.
    command['chapter'] = '2'

    dvd_device and command.set_device(dvd_device)
    return command


def get_input(command=None):
    from subprocess import Popen, PIPE, list2cmdline

    null = open('NUL', 'w')
    command = command or build_command(*parse_args())
    args = tuple(command.get_args())
    log.debug(list2cmdline(args))
    mencoder = Popen(args, stdout=PIPE, stderr=null)
    return mencoder


class InsufficientFramesError(RuntimeError):
    pass


def process_input(process, n_frames=1000):
    pattern = re.compile(r'.*crop=(\d+:\d+:\d+:\d+).*')

    crop_matches = filter(None, map(pattern.match, process.stdout))
    crop_values = map(lambda match: match.group(1), crop_matches)
    preceeding_items = itertools.takewhile(
        within_consecutive_limit(n_frames), crop_values
    )

    log.info('processed %d frames', len(tuple(preceeding_items)))
    try:
        target = crop_values.next()
    except StopIteration:
        raise InsufficientFramesError(
            "Not enough frames to detect %d consecutive same" % n_frames
        )
    finally:
        clean_up(process)
    return target


def clean_up(process):
    terminate(process)
    process.stdout.flush()


def get_crop(dvd_device=None, title=''):
    log.info('Detecting crop')
    return process_input(get_input(build_command(dvd_device, title)))


def execute(command=None):
    logging.basicConfig(level=logging.INFO)
    mencoder = get_input(command)
    try:
        log.info('crop is %s', process_input(mencoder))
    except InsufficientFramesError as e:
        log.warning(e)


if __name__ == '__main__':
    execute()
