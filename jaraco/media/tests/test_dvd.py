import sys

import pytest

from jaraco.media import dvd


@pytest.fixture(autouse=True)
def mencoder(monkeypatch):
    monkeypatch.setattr(
        dvd.MEncoderCommand, 'find_mencoder_exe', staticmethod(lambda: 'mencoder')
    )


def test_infer_name():
    assert str(dvd.infer_name('/media/JEAN_DE_FLORETTE')) == 'Jean De Florette'


def test_set_device(tmp_path):
    command = dvd.MEncoderCommand()
    command.set_device(str(tmp_path))
    assert command.device == {'dvd-device': str(tmp_path)}


def make_command(tmp_path):
    command = dvd.MEncoderCommand()
    command.source = ['dvd://1']
    command.video_options = dvd.get_x264_options()
    command['o'] = str(tmp_path / 'movie.avi')
    return command


def test_multi_pass(tmp_path):
    handler = dvd.MultiPassHandler(make_command(tmp_path))
    log_file = tmp_path / 'movie_pass.log'
    assert handler.command['passlogfile'] == str(log_file)
    first, last = handler
    assert first.video_options['lavcopts']['vpass'] == '1'
    assert last.video_options['lavcopts']['vpass'] == '2'
    log_file.touch()
    handler.cleanup_log_file()
    assert not log_file.exists()


def test_multi_pass_cleanup_failure(tmp_path, monkeypatch, caplog):
    handler = dvd.MultiPassHandler(make_command(tmp_path))
    (tmp_path / 'movie_pass.log').touch()

    def fail(filename):
        raise PermissionError(filename)

    monkeypatch.setattr(dvd.os, 'remove', fail)
    handler.cleanup_log_file()
    assert 'Error removing logfile' in caplog.text


class FakeProcess:
    def __init__(self, args, **kwargs):
        self.args = tuple(args)

    def wait(self):
        return 0


@pytest.fixture
def popen(monkeypatch):
    monkeypatch.setattr(dvd.subprocess, 'Popen', FakeProcess)


@pytest.mark.usefixtures('popen')
def test_re_encode(capsys):
    dvd.re_encode('movie.avi', dvd.get_video_copy_options(), dvd.HyphenArgs())
    assert 'success' in capsys.readouterr().out


@pytest.mark.parametrize('func', [dvd.transcode, dvd.fix_fourcc])
def test_re_encode_commands(func, monkeypatch):
    calls = []
    monkeypatch.setattr(dvd, 're_encode', lambda *args: calls.append(args))
    monkeypatch.setattr(sys, 'argv', ['cmd', 'movie.avi'])
    func()
    [(source, _, _)] = calls
    assert source == 'movie.avi'


def test_command_args_render_the_options():
    """The delimited options are rendered as command line arguments."""
    command = dvd.MEncoderCommand()
    command.source = ['dvd://1']
    command.video_options = dvd.HyphenArgs(
        lavcopts=dvd.ColonDelimitedArgs(vcodec='libx264')
    )
    command.audio_options = dvd.HyphenArgs(nosound=None)
    assert list(command.get_args()) == [
        'mencoder',
        'dvd://1',
        '-lavcopts vcodec=libx264',
        '-nosound',
    ]
