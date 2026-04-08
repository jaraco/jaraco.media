"""
Rip the main feature from a Blu-ray disc using MakeMKV without transcoding.
"""

import argparse
import dataclasses
import datetime
import re
import subprocess

import path

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


def scan_titles(disc='disc:0'):
    """Scan a disc and return a list of TitleInfo objects."""
    cmd = ['makemkvcon', '--robot', 'info', disc]
    output = subprocess.check_output(cmd, stderr=subprocess.DEVNULL, text=True)

    titles: dict[int, dict] = {}
    for line in output.splitlines():
        m = re.match(r'^TINFO:(\d+),(\d+),\d+,"(.*)"', line)
        if not m:
            continue
        title_num, attr_id, value = int(m.group(1)), int(m.group(2)), m.group(3)
        titles.setdefault(title_num, {})
        if attr_id == 9:
            titles[title_num]['duration'] = _parse_duration(value)
        elif attr_id == 10:
            titles[title_num]['size'] = value
        elif attr_id == 27:
            titles[title_num]['filename'] = value

    return [
        TitleInfo(
            number=num,
            duration=info.get('duration', datetime.timedelta()),
            size=info.get('size', 'unknown'),
            filename=info.get('filename', f'title_{num:02d}.mkv'),
        )
        for num, info in sorted(titles.items())
        if 'duration' in info
    ]


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
