"""
Concatenate SRT files based on the length of associated media files.
"""

import functools
import re
import subprocess
import itertools
import datetime
import sys

import autocommand
import path
from . import srt
from tempora import parse_timedelta
from more_itertools import islice_extended as islice
from jaraco.itertools import accumulate


def get_duration(media_file):
    """
    https://superuser.com/questions/650291/how-to-get-video-duration-in-seconds
    """
    cmd = [
        'ffprobe',
        '-v',
        'error',
        '-show_entries',
        'format=duration',
        '-of',
        'default=noprint_wrappers=1:nokey=1',
        media_file,
    ]
    return parse_timedelta(subprocess.check_output(cmd, text=True))


@autocommand.autocommand(__name__)
def main(*files, include='.*', outfile=sys.stdout):
    matcher = functools.partial(re.search, include)
    matched = map(path.Path, filter(matcher, files))
    srt_files = list(matched)
    media_files = [srt_file.with_suffix('.mp4') for srt_file in srt_files]
    durations = map(get_duration, media_files)
    incr_additions = itertools.chain((datetime.timedelta(),), islice(durations, -1))
    additions = accumulate(incr_additions)
    with autocommand.smart_open(outfile, mode='w') as strm:
        for srt_file, addition in zip(srt_files, additions):
            entries = srt.SubEntry.get_entries(srt_file)
            for entry in entries:
                print(entry + addition, file=strm)
