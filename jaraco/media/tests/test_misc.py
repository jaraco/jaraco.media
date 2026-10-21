import os

from jaraco.media import dvd_info, index


def test_title_info_str():
    info = dvd_info.TitleInfo(number=1, length='0:01:00', chapters=4)
    assert str(info).startswith('Number: 1\nTitle length: 0:01:00\nChapters: 4\n')


def test_is_media():
    assert index.Index.is_media('movie.mp4')
    assert not index.Index.is_media('notes.txt')


def test_isapi_factory_without_isapi(capsys):
    assert index.Site.factory() is None
    assert 'isapi_wsgi' in capsys.readouterr().err


def test_get_media_returns_only_media_files(tmp_path):
    """Only the files with a media extension are returned."""
    (tmp_path / 'movie.mp4').write_bytes(b'')
    (tmp_path / 'notes.txt').write_bytes(b'')
    (tmp_path / 'subdir').mkdir()

    result = list(index.Index().get_media(str(tmp_path)))

    assert [os.path.basename(name) for name in result] == ['movie.mp4']


def test_index_iterates_the_media_files(tmp_path):
    """Iterating the index yields the media files and not the other entries."""
    (tmp_path / 'movie.mp4').write_bytes(b'')
    (tmp_path / 'notes.txt').write_bytes(b'')

    class FakeIndex(index.Index):
        def get_named_map(self):
            return {'class': str(tmp_path)}

    movies = list(FakeIndex(filter=lambda movie: True))

    assert [os.path.basename(movie.filename) for movie in movies] == ['movie.mp4']
