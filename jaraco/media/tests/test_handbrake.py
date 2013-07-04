from __future__ import print_function

import pkg_resources
import mock

from jaraco.media import handbrake

def get_file(name):
	return pkg_resources.resource_stream('jaraco.media.tests', name)

multi_title_output = get_file('multi title output.txt').read()

@mock.patch('subprocess.check_output', side_effect=multi_title_output)
def test_title_durations(check_output):
	handbrake.title_durations()
