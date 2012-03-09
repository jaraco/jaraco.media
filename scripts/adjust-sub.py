import datetime
import sys
import argparse
import itertools

from jaraco.media.srt import SubEntry

def get_args():
	parser = argparse.ArgumentParser()
	parser.add_argument('delta',
		type=lambda s: datetime.timedelta(seconds=float(s)))
	parser.add_argument('-s', '--start-entry', default=0, type=int)
	parser.add_argument('-e', '--end-entry', type=int)
	return parser.parse_args()

def main():
	args = get_args()
	entries = SubEntry.get_entries(sys.stdin)
	start_entries = itertools.islice(entries, args.start_entry)
	if args.end_entry:
		# since start_entries may already have been consumed, adjust the
		#  end to account for those items.
		args.end_entry = args.end_entry - args.start_entry
	adjust_entries = itertools.islice(entries, args.end_entry)
	adjust_entries = (entry + args.delta for entry in adjust_entries)
	rest = entries

	adjusted_entries = itertools.chain(start_entries, adjust_entries, rest)

	SubEntry.write_entries(sys.stdout, adjusted_entries)

if __name__ == '__main__':
	main()
