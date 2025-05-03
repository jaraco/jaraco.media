.. image:: https://img.shields.io/pypi/v/jaraco.media.svg
   :target: https://pypi.org/project/jaraco.media

.. image:: https://img.shields.io/pypi/pyversions/jaraco.media.svg

.. image:: https://github.com/jaraco/jaraco.media/actions/workflows/main.yml/badge.svg
   :target: https://github.com/jaraco/jaraco.media/actions?query=workflow%3A%22tests%22
   :alt: tests

.. image:: https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json
    :target: https://github.com/astral-sh/ruff
    :alt: Ruff

.. .. image:: https://readthedocs.org/projects/PROJECT_RTD/badge/?version=latest
..    :target: https://PROJECT_RTD.readthedocs.io/en/latest/?badge=latest

.. image:: https://img.shields.io/badge/skeleton-2025-informational
   :target: https://blog.jaraco.com/skeleton


concat
------

FFmpeg provides a routine to
`concatenate media files <https://trac.ffmpeg.org/wiki/Concatenate>`_.
Unfortunately, the UI for that routine is so bad that even ffmpeg
provides multiple, platform-specific techniques to generate the input.
``jaraco.media.compat``, in contrast, takes a number of input files
and optionally an output file and input filter, creates the input file
in its required syntax and then runs ffmpeg against that file. Example::

    $ python -m jaraco.media.concat /Volumes/drone/DCIM/100MEDIA/DJI_*.MP4 -i '(17|18|19)' -o /Volumes/Public/Flights/2022-02-20.mp4


srt-concat
----------

Concatenate SRT files, updating the offsets based on the durations
of their associated media files. Example::

    $ python -m jaraco.media.srt-concat /Volumes/Drone/DCIM/100MEDIA/DJI_00*.SRT -i '(17|18|19)' -o /Volumes/Public/Flights/2022-02-20.srt


splice
------

Extract timestamps from a video.

    $ python -m jaraco.media.splice infile.mp4 outfile.mp4 00:00:00-01:32:46 01:47:20-01:49:17

Troubleshooting
---------------

If you see "libaacs not initialized!" or "aacs_open() failed",
remember that you have to re-register with the latest
beta key each month.

See `this blog
<http://drbobtechblog.com/handbrake-can-use-makemkv-to-automatically-process-blu-ray-discs-heres-how/>`_
for details.
