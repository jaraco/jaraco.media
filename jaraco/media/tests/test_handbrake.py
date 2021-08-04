from importlib_resources import files

import mock
import path

from jaraco.media import handbrake, dvd


@mock.patch(
    'subprocess.check_output',
    return_value=files(__package__).joinpath('multi title output.txt').read_bytes(),
)
def test_title_durations(check_output, monkeypatch):
    monkeypatch.setattr(dvd, 'get_source', lambda: path.Path('/'))
    handbrake.title_durations()
