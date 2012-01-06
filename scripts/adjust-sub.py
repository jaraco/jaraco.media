import datetime

from jaraco.media.srt import SubEntry

def main():
	entries = SubEntry.get_entries('Sky Crawlers.srt.orig')
	entries = SubEntry.adjust_entries(entries, datetime.timedelta(seconds=-22.5))
	SubEntry.write_entries('Sky Crawlers.srt', entries)

if __name__ == '__main__':
	main()
