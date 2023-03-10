# ░▀█▀░█▄█░█▀█░█▀█░█▀▄░▀█▀░█▀▀
# ░░█░░█░█░█▀▀░█░█░█▀▄░░█░░▀▀█
# ░▀▀▀░▀░▀░▀░░░▀▀▀░▀░▀░░▀░░▀▀▀

import os
import re
import subprocess
from mutagen.easyid3 import EasyID3
from mutagen.mp4 import MP4

# ░█▀▀░█░█░█▀█░█▀▀░▀█▀░▀█▀░█▀█░█▀█░█▀▀
# ░█▀▀░█░█░█░█░█░░░░█░░░█░░█░█░█░█░▀▀█
# ░▀░░░▀▀▀░▀░▀░▀▀▀░░▀░░▀▀▀░▀▀▀░▀░▀░▀▀▀


def get_ffmpeg_command_starter(verbose=False) -> list[str]:
    return ["ffmpeg", "-hide_banner", "-loglevel", "error" if not verbose else "warning",
            "-stats"]


def convert_to(filename: str, extension: str, verbose=False, force=False) -> str:
    """ Convert given file to extension with ffmpeg binary.
    Returns the new filename or None if failed.
    """
    if not force and extension == filename.split(".")[-1]:
        return filename

    dir_path = os.path.dirname(filename) if len(
        os.path.dirname(filename)) > 0 else os.getcwd()
    new_filename = dir_path + "\\" + \
        os.path.splitext(os.path.basename(filename))[0] + "." + extension
    command = get_ffmpeg_command_starter(
        verbose) + ["-i", r"{}".format(filename)]

    # if we want less size output, encoding with hevc = libx265 and higher crf to 24 for less size
    # if extension == "mp4":
    #     command += ["-c:v", "hevc", "-crf", "24"]

    # remove video data from the file, if any
    if extension == "mp3":
        command += ["-vn"]

    command += ["-y", r"{}".format(new_filename)]

    if verbose:
        print(" ".join(command))

    subprocess.call(command, shell=True)

    os.remove(filename)

    if force:
        return convert_to(new_filename, "mp3", verbose)

    if not os.path.isfile(new_filename):
        return None
    return new_filename


def add_metadata(filename: str, thumbnail: str, author: str, title: str, verbose=False) -> bool:
    """ Adds metadata to a media file
    Args:
        filename: the path for the mp3 file
        thumbnail: the path for the image
        author: the author of the audio
        title: the media title
        verbosity: the command verbosity

    Returns:
        boolean success
    """
    output_filename = filename + "_temp" + os.path.splitext(filename)[1]

    command = get_ffmpeg_command_starter(verbose) + ["-i", r"{}".format(thumbnail), "-i", r"{}".format(filename),
                                                     "-map", "0", "-map", "1", "-c", "copy",
                                                     "-metadata", r'artist={}'.format(author)
                                                     , "-metadata", r'title={}'.format(title), r"{}".format(output_filename)]

    if verbose:
        print(" ".join(command))

    subprocess.call(command, shell=True)
    
    os.remove(filename)
    os.remove(thumbnail)
    os.rename(output_filename, filename)

    # Check file metadata
    try:
        if filename.endswith(".mp3"):
            metadata = EasyID3(filename)
        elif filename.endswith(".mp4"):
            metadata = MP4(filename).tags

        # Get the title metadata
        title = metadata.get("title")

        return title != None
    except:
        return False


def get_valid_filename(filename: str, backslash=False) -> str:
    """ Will remove any bad character for a filename
    """
    bad_chars = ["/", "|", ":", "*", "?", "'", '"', "<", ">"]
    if not backslash:
        bad_chars.append("\\")
    for bad_char in bad_chars:
        filename = filename.replace(bad_char, ("\\" + bad_char if backslash else "_"))
    return filename


def merge_video_audio(video_path: str, audio_path: str, verbose=False) -> str:
    """ Will merge an audio and a video file together
    """
    output_path = video_path + "_temp.mp4"
    command = get_ffmpeg_command_starter(verbose) + [
        r"{}".format(
            video_path), "-i", r"{}".format(audio_path), "-c:v", "copy", "-c:a", "aac",
        "-map", "0:v:1", "-map", "1:a:0", "-y", r"{}".format(output_path)]

    if verbose:
        print(" ".join(command))

    subprocess.call(command, shell=True)

    os.remove(video_path)
    os.remove(audio_path)
    os.rename(output_path, video_path)

    return output_path
