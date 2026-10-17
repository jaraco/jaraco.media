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
