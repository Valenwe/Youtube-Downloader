# ░▀█▀░█▄█░█▀█░█▀█░█▀▄░▀█▀░█▀▀
# ░░█░░█░█░█▀▀░█░█░█▀▄░░█░░▀▀█
# ░▀▀▀░▀░▀░▀░░░▀▀▀░▀░▀░░▀░░▀▀▀

import os
import subprocess
from mutagen.id3 import ID3, APIC, TPE1, TIT2
from mutagen.mp4 import MP4, MP4Cover

# ░█▀▀░█░█░█▀█░█▀▀░▀█▀░▀█▀░█▀█░█▀█░█▀▀
# ░█▀▀░█░█░█░█░█░░░░█░░░█░░█░█░█░█░▀▀█
# ░▀░░░▀▀▀░▀░▀░▀▀▀░░▀░░▀▀▀░▀▀▀░▀░▀░▀▀▀

def convert_to(filename: str, extension: str) -> int:
    """ Returns the new filename
    """
    if extension == filename.split(".")[-1]:
        return filename

    dir_path = os.path.dirname(filename) if len(os.path.dirname(filename)) > 0 else os.getcwd()
    new_filename = dir_path + "/" + os.path.splitext(os.path.basename(filename))[0] + "." + extension
    command = ["ffmpeg.exe", "-hide_banner", "-i", f'{filename}', "-y", f'{new_filename}']

    subprocess.call(command, shell=True)
    os.remove(filename)
    return new_filename

def add_metadata(filename: str, thumbnail: str, author: str, title: str):
    """
    Args:
        filename: the path for the mp3 file
        thumbnail: the path for the image
        author: the author of the audio
        title: the media title
    """
    if filename.endswith(".mp3"):
        return add_audio_metadata(filename, thumbnail, author, title)
    if filename.endswith(".mp4"):
        return add_video_metadata(filename, thumbnail, author, title)
    else:
        return False

def add_audio_metadata(filename: str, thumbnail: str, author: str, title: str):

    if not filename.endswith(".mp3"):
        return False

    # Open the MP3 file
    audio = ID3(filename)

    # Set the MIME type for the image
    mime_type = 'image/jpeg'

    # Open the image file and read its data
    with open(thumbnail, 'rb') as f:
        image_data = f.read()

    # Add the image data as the album art
    audio.add(APIC(mime=mime_type, type=3, desc='cover', data=image_data))

    # Add the artist name as a tag
    audio.add(TPE1(encoding=3, text=author))

    # Add the title as a tag
    audio.add(TIT2(encoding=3, text=title))

    audio.save()
    os.remove(thumbnail)
    return True

def add_video_metadata(filename: str, thumbnail: str, author: str, title: str):

    if not filename.endswith(".mp4"):
        return False

    # Open the MP4 file
    video = MP4(filename)

    # Open the image file and read its data
    with open(thumbnail, 'rb') as f:
        image_data = f.read()

    # Set the thumbnail
    image_format_code = 13  # This is the code for JPEG format
    cover = MP4Cover(image_data, imageformat=image_format_code)

    # Add the thumbnail to the video file
    video['covr'] = [cover]

    # Add the author to the video file
    video['©ART'] = [author]

    # Add the title to the video file
    video['©nam'] = [title]

    # Save the changes to the MP4 file
    video.save()
    os.remove(thumbnail)
    return True

def get_valid_filename(filename: str):
    for bad_char in ["/", "\\", "|", ":", "*", "?", "'", '"', "<", ">"]:
        filename = filename.replace(bad_char, "_")
    return filename