"""
jaraco.media assumes videos are stored under $root/Movies and $root/TV
where root is ~/Videos on Windows, ~ on other platforms, and can be
overridden by defining
VIDEOS_ROOT environment variable.
"""

import os
import platform

import path


def get_media_root():
    default = dict(
        Windows='~/Videos',
    ).get(platform.system(), '~')
    root = path.Path(os.environ.get('VIDEOS_ROOT', default))
    return root.expanduser()


movies_root = get_media_root() / 'Movies'
tv_root = get_media_root() / 'TV'
