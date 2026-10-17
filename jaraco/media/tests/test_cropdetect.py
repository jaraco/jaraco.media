import io

import pytest

from jaraco.media import cropdetect, dvd


class FakeProcess:
    def __init__(self, output=''):
        self.stdout = io.StringIO(output)
        self.terminated = False

    def terminate(self):
        self.terminated = True


class ExitedProcess(FakeProcess):
    def terminate(self):
        raise OSError("already exited")


def test_terminate_ignores_exited_process():
    cropdetect.terminate(ExitedProcess())


@pytest.fixture
def mencoder(monkeypatch):
    monkeypatch.setattr(
        dvd.MEncoderCommand, 'find_mencoder_exe', staticmethod(lambda: 'mencoder')
    )


@pytest.mark.usefixtures('mencoder')
def test_build_command():
    command = cropdetect.build_command(title='3')
    assert command.source == ['dvd://3']
    assert command.video_filter == {'vf': 'cropdetect=24:16'}


def test_process_input():
    lines = ['noise\n'] + ['[CROP] crop=720:480:0:0\n'] * 4
    process = FakeProcess(''.join(lines))
    assert cropdetect.process_input(process, n_frames=2) == '720:480:0:0'
    assert process.terminated


def test_process_input_insufficient():
    process = FakeProcess('[CROP] crop=720:480:0:0\n')
    with pytest.raises(cropdetect.InsufficientFramesError):
        cropdetect.process_input(process, n_frames=2)
