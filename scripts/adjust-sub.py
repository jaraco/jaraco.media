#!python
from jaraco.media.srt import SubEntry

entries = SubEntry.get_entries('Sky Crawlers.srt.orig')
entries = SubEntry.adjust_entries(entries, timedelta(seconds=-22.5))
SubEntry.write_entries('Sky Crawlers.srt', entries)
