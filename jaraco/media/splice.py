import contextlib
import datetime
import pathlib
import subprocess
import tempfile

import autocommand


TIME_PRECISION = 2

FFPROBE_FRAME_TIME_OPTION = ["packet=pts_time,flags"]
FFPROBE_TIME_BASE_OPTION = ["stream=time_base"]


def convert_path(input_path):
    return pathlib.Path(input_path).expanduser().resolve()


def split_range(time_range):
    return tuple(time_range.split("-"))


def convert_timestamp_to_isoformat(input_timestamp):
    if input_timestamp.count(":") == 1:
        if len(input_timestamp.split(":")[0]) == 1:
            input_timestamp = f"0{input_timestamp}"
        input_timestamp = f"00:{input_timestamp}"
    if input_timestamp.count(".") == 1:
        time, milliseconds = input_timestamp.split(".")
        input_timestamp = f"{time}{int(milliseconds):0>6}"
    return input_timestamp


def convert_timestamp_to_s(input_timestamp):
    try:
        return float(input_timestamp)
    except ValueError:
        pass

    if isinstance(input_timestamp, str):
        input_timestamp = convert_timestamp_to_isoformat(input_timestamp)
        input_timestamp = datetime.time.fromisoformat(input_timestamp)

    if isinstance(input_timestamp, datetime.time):
        input_timestamp = datetime.datetime.combine(datetime.date.min, input_timestamp)
    if isinstance(input_timestamp, datetime.datetime):
        return (input_timestamp - datetime.datetime.min).total_seconds()

    raise TypeError(
        f"Timestamp must be float, string or date/time, not {type(input_timestamp)!r}"
    )


def get_ffprobe_values(input_file, options):
    input_file = convert_path(input_file)
    ffprobe_command = (
        "ffprobe",
        "-loglevel",
        "error",
        "-select_streams",
        "v:0",
        "-show_entries",
        *options,
        "-of",
        "csv=print_section=0",
        input_file,
    )
    keyframe_output = subprocess.run(
        ffprobe_command, capture_output=True, check=True, encoding="UTF-8"
    )
    return keyframe_output.stdout


def get_keyframe_times_raw(input_file):
    keyframe_output = get_ffprobe_values(input_file, FFPROBE_FRAME_TIME_OPTION)
    keyframe_times_raw = [
        line.split(",")[0]
        for line in keyframe_output.split("\n")
        if line.strip() and line.strip()[-2] == "K"
    ]
    return keyframe_times_raw


def convert_keyframe_times(keyframe_times_raw):
    return [float(raw_time) for raw_time in keyframe_times_raw]


def get_keyframe_times(input_file):
    return convert_keyframe_times(get_keyframe_times_raw(input_file))


def file_block_natural(
    end, idx, input_file, keyframe_times, keyframe_times_rounded, start, temp_path
):
    next_keyframe = keyframe_times[keyframe_times_rounded.index(round(start))]
    post_output_path = temp_path / f"post_copy_{idx}.mp4"
    post_duration = round(end - next_keyframe, TIME_PRECISION + 1)
    copy_command = (
        "ffmpeg",
        "-y",
        "-ss",
        str(next_keyframe),
        "-i",
        input_file,
        "-t",
        str(post_duration),
        "-c",
        "copy",
        post_output_path,
    )
    subprocess.run(copy_command, check=True)
    return post_output_path, post_duration


def file_block_adjusted(
    idx, input_file, keyframe_times, keyframe_times_rounded, start, temp_path
):
    if round(start, TIME_PRECISION) in keyframe_times_rounded:
        # no adjustment needed
        return
    next_keyframe = min([time for time in keyframe_times if time > start])
    time_base_raw = get_ffprobe_values(input_file, FFPROBE_TIME_BASE_OPTION)
    time_base = time_base_raw.split("/")[-1]
    pre_output_path = temp_path / f"pre_encode_{idx}.mp4"
    pre_duration = round(next_keyframe - start, TIME_PRECISION + 1)
    encode_command = (
        "ffmpeg",
        "-y",
        "-ss",
        str(start),
        "-i",
        input_file,
        "-t",
        str(pre_duration),
        "-video_track_timescale",
        time_base,
        "-c:v",
        "libx264",
        "-preset",
        "veryfast",
        pre_output_path,
    )
    subprocess.run(encode_command, check=True)
    return pre_output_path, pre_duration


def gen_file_block(
    end, idx, input_file, keyframe_times, keyframe_times_rounded, start, temp_path
):
    print(f"\nPreparing segment {start} to {end}\n")
    start = convert_timestamp_to_s(start)
    end = convert_timestamp_to_s(end)

    output_path, duration = file_block_adjusted(
        idx, input_file, keyframe_times, keyframe_times_rounded, start, temp_path
    ) or file_block_natural(
        end, idx, input_file, keyframe_times, keyframe_times_rounded, start, temp_path
    )
    return f"file '{output_path}'\nduration {duration}\n"


@contextlib.contextmanager
def TemporaryPath():
    with tempfile.TemporaryDirectory() as temp_dir:
        yield pathlib.Path(temp_dir)


@autocommand.autocommand(__name__)
def splice_video(
    input_file: (  # type: ignore
        convert_path,
        "The media file to read in",  # noqa: F722
    ),
    output_file: (  # type: ignore
        convert_path,
        "The file to output the edited result to",  # noqa: F722
    ),
    *timestamps_include: (  # type: ignore
        split_range,
        "Start and end timestamps to include in the final video, "  # noqa: F722
        "in the form HH:MM:SS.ffffff-HH:MM:SS.ffffff or SS.fff-SS.fff",
    ),
):
    "Split and combine specific chunks from a media w/ffmpeg."

    print("Retrieving keyframes")
    keyframe_times = get_keyframe_times(input_file)
    keyframe_times_rounded = [
        round(frame_time, TIME_PRECISION) for frame_time in keyframe_times
    ]
    with TemporaryPath() as temp_path:
        concat_file_contents = "\n".join(
            gen_file_block(
                end,
                idx,
                input_file,
                keyframe_times,
                keyframe_times_rounded,
                start,
                temp_path,
            )
            for idx, (start, end) in enumerate(timestamps_include)
        )

        print("\nWriting concat file contents:\n")
        print(concat_file_contents)
        concat_file_path = temp_path / "splice_concat_file_list.txt"
        concat_file_path.write_text(concat_file_contents, encoding="UTF-8")

        print("\nRunning concat\n")
        concat_command = (
            "ffmpeg",
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            concat_file_path,
            "-c",
            "copy",
            output_file,
        )
        subprocess.run(concat_command, check=True)
