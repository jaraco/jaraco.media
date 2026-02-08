import subprocess

import path
from importlib_resources import files

from jaraco.media import dvd, handbrake


def test_title_durations(monkeypatch):
    mocked = files(__package__).joinpath('multi title output.txt').read_bytes()
    monkeypatch.setattr(subprocess, 'check_output', lambda *args, **kw: mocked)
    monkeypatch.setattr(dvd, 'get_source', lambda: path.Path('/'))
    handbrake.title_durations()
