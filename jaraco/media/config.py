"""
jaraco.media assumes videos are stored under $root/Movies and $root/TV
where root is ~/Videos by default and can be overridden by defining
VIDEOS_ROOT environment variable.
"""

import os
import getpass

from path import path

def get_media_root():
	default = '~/Videos'
	if getpass.getuser() == 'jaraco':
		default = '//drake/videos'
	root = path(os.environ.get('VIDEOS_ROOT', default))
	return root.expanduser()

movies_root = get_media_root() / 'Movies'
tv_root = get_media_root() / 'TV'
