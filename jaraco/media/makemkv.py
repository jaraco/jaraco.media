"""
Rip the main feature from a Blu-ray disc using MakeMKV without transcoding.
"""

import argparse
import dataclasses
import datetime
import itertools
import re
import subprocess

import path
from more_itertools import map_reduce

from jaraco.media import config, dvd, handbrake

MIN_FEATURE_LENGTH = datetime.timedelta(minutes=60)


@dataclasses.dataclass
class TitleInfo:
    number: int
    duration: datetime.timedelta
    size: str
    filename: str

    def __str__(self):
        return f"Title #{self.number}: {self.duration} — {self.size} ({self.filename})"


def _parse_duration(s):
    """
    Parse a H:MM:SS duration string to a timedelta.

    >>> _parse_duration('2:08:29')
    datetime.timedelta(seconds=7709)
    """
    h, m, sec = map(int, s.split(':'))
    return datetime.timedelta(hours=h, minutes=m, seconds=sec)


_TINFO = re.compile(r'^TINFO:(\d+),(\d+),\d+,"(.*)"')


def _parse_tinfo(line):
    """Parse a TINFO line into (title_num, attr_id, value) or None."""
    m = _TINFO.match(line)
    if m:
        return int(m.group(1)), int(m.group(2)), m.group(3)


def _build_title(num, attrs):
    """Build a TitleInfo from a (title_num, [(attr_id, value)]) pair, or None if no duration."""
    info = dict(attrs)
    if 9 not in info:
        return None
    return TitleInfo(
        number=num,
        duration=_parse_duration(info[9]),
        size=info.get(10, 'unknown'),
        filename=info.get(27, f'title_{num:02d}.mkv'),
    )


def scan_titles(disc='disc:0'):
    """Scan a disc and return a list of TitleInfo objects."""
    cmd = ['makemkvcon', '--robot', 'info', disc]
    output = subprocess.check_output(cmd, stderr=subprocess.DEVNULL, text=True)
    parsed = filter(None, map(_parse_tinfo, output.splitlines()))
    by_title = map_reduce(
        parsed, keyfunc=lambda t: t[0], valuefunc=lambda t: (t[1], t[2])
    )
    return list(filter(None, itertools.starmap(_build_title, sorted(by_title.items()))))


def choose_title(titles):
    """
    From all scanned titles, select the feature to rip.

    Filters to feature-length titles (>= MIN_FEATURE_LENGTH), then either
    returns the sole candidate automatically or prompts the user to choose.
    """
    features = [t for t in titles if t.duration >= MIN_FEATURE_LENGTH]
    if not features:
        raise SystemExit("No feature-length titles found on disc.")

    if len(features) == 1:
        return features[0]

    print("Feature-length titles:")
    for i, title in enumerate(features):
        print(f"  [{i}] {title}")

    choice = input("Select title [0]: ").strip()
    return features[int(choice) if choice else 0]


def rip_title(title, output_dir, disc='disc:0'):
    """Rip a TitleInfo to output_dir using MakeMKV (no transcoding)."""
    cmd = ['makemkvcon', 'mkv', disc, str(title.number), str(output_dir)]
    subprocess.run(cmd, check=True)


def quick_mkv():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        '--output',
        '-o',
        default=str(config.movies_root),
        help='Output directory (default: %(default)s)',
    )
    parser.add_argument(
        '--disc',
        default='disc:0',
        help='MakeMKV disc identifier (default: %(default)s)',
    )
    args = parser.parse_args()

    handbrake.init_environment()

    output_dir = path.Path(args.output)
    output_dir.makedirs_p()

    disc_name = dvd.infer_name()
    print(f"Disc: {disc_name}")
    print("Scanning titles...")
    titles = scan_titles(args.disc)

    title = choose_title(titles)
    print(f"Ripping: {title}")

    rip_title(title, output_dir, args.disc)
    print(f"Done. Saved to {output_dir / title.filename}")
