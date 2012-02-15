import datetime
import os
import shutil

import path
from jaraco.media.srt import SubEntry
from jaraco.util.string import local_format as lf

def main():
	root = path.path(r'\\drake\videos\Movies')
	name = 'House of Flying Daggers'
	orig = root / lf('{name}.srt.orig')
	upd = root / lf('{name}.srt')
	if not os.path.exists(orig):
		shutil.copy(upd, orig)
	entries = SubEntry.get_entries(orig)
	diff = datetime.timedelta(seconds=-4.5)
	entries = SubEntry.adjust_entries(entries, diff)
	SubEntry.write_entries(upd, entries)

if __name__ == '__main__':
	main()
