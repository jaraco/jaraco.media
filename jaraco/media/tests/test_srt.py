from jaraco.media import srt


def test_roundtrip_file(tmp_path):
    source = tmp_path / 'source.srt'
    source.write_text(srt._sample_srt_entries, encoding='utf-8')
    target = tmp_path / 'target.srt'
    entries = list(srt.SubEntry.get_entries(str(source)))
    srt.SubEntry.write_entries(str(target), entries)
    assert len(list(srt.SubEntry.get_entries(str(target)))) == 3
