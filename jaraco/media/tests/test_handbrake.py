import pkg_resources
import mock
import path

from jaraco.media import handbrake, dvd


def get_file(name):
    return pkg_resources.resource_stream('jaraco.media.tests', name)


@mock.patch(
    'subprocess.check_output', return_value=get_file('multi title output.txt').read()
)
def test_title_durations(check_output, monkeypatch):
    monkeypatch.setattr(dvd, 'get_source', lambda: path.Path('/'))
    handbrake.title_durations()
