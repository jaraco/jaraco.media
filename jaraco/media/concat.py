"""
Use ffmpeg to concatenate mpeg files.
"""

import contextlib
import functools
import re
import subprocess

import autocommand
import path


@contextlib.contextmanager
def write_names_to_file(names):
    with path.TempDir() as dir:
        file = dir.joinpath('names.txt')
        lines = (f"file '{name}'" for name in names)
        file.write_text('\n'.join(lines))
        yield file


@autocommand.autocommand(__name__)
def main(*files, out_name='out.mp4', include='.*'):
    matcher = functools.partial(re.search, include)
    matched = filter(matcher, files)
    with write_names_to_file(matched) as names_file:
        cmd = [
            'ffmpeg',
            '-f',
            'concat',
            # '-safe 0' required if input filenames are absolute :/
            '-safe',
            '0',
            '-i',
            names_file,
            '-c',
            'copy',
            out_name,
        ]
        subprocess.check_call(cmd)
