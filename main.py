# ░▀█▀░█▄█░█▀█░█▀█░█▀▄░▀█▀░█▀▀
# ░░█░░█░█░█▀▀░█░█░█▀▄░░█░░▀▀█
# ░▀▀▀░▀░▀░▀░░░▀▀▀░▀░▀░░▀░░▀▀▀
# text retrieved from https://textkool.com/en/ascii-art-generator?hl=default&vl=default&font=Pagga

import msvcrt
from enum import Enum
from tqdm import tqdm
import os
import sys
import git
from pathlib import Path
import locale
locale.setlocale(locale.LC_NUMERIC, 'pl_PL')

import ytb_classes
import download
import media_management

class Color(Enum):
    """ Class for coloring print statements.  Nothing to see here, move along. """
    BLACK = '\033[30m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    PURPLE = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'
    END = '\033[0m'
    BOLD = '\033[1m'

    @staticmethod
    def string(string: str, color=None, bold: bool = True) -> str:
        """ Prints the given string in a few different colors.

        Args:
            string: string to be printed
            color:  valid colors Color.RED, "blue", Color.GREEN, "yellow"...
            bold:   T/F to add ANSI bold code

        Returns:
            ANSI color-coded string (str)
        """
        boldstr = Color.BOLD.value if bold else ""
        if not isinstance(color, Color):
            color = Color.WHITE

        return f'{boldstr}{color.value}{string}{Color.END.value}'

def check_current_git_version():
    """ Check if current Git repository is up to date
    """
    # Initialize a GitPython Repo object for the existing repository
    repo = git.Repo(os.getcwd())

    # Fetch the latest changes from the remote repository
    repo.remotes.origin.fetch()

    # Get the current branch
    branch = repo.active_branch

    # Check if the local branch is up to date with the remote branch
    if branch.commit.hexsha != repo.remotes.origin.refs[branch.name].commit.hexsha:
        print(Color.string(f"Current repository is not up to date. Try updating it with git clone {Color.string(repo.remotes.origin.url, Color.CYAN)}", Color.RED))

def detect_url(in_url: str) -> tuple[str, object]:
    """ Will try to convert a URL to a special class
    Args:
        in_url: the url submitted
    Returns:
        tuple(url, custom class)
    """
    url = None
    url_type = None
    try:
        url_type = ytb_classes.Playlist(in_url)
        url = in_url
        print(Color.string("Playlist saved.", Color.GREEN))
    except ValueError:
        try:
            url_type = ytb_classes.Video(in_url)
            url = in_url
            print(Color.string("Video saved.", Color.GREEN))
        except ValueError:
            print(Color.string(
                "Provided link is not a valid Youtube link.", Color.RED))
    return url, url_type

def manage_video(video: ytb_classes.Video, media_type: str) -> str | None:
    """ Will retrieve video intel, download and convert it
    Args:
        video (Video): the video class instance
        media_type (str): either "audio" or "video"

    Returns:
        the downloaded and converted file path
    """
    # If video type, we have to download the audio first
    if media_type == "video":
        print(Color.string("I have to download the audio first", Color.YELLOW))
        audio_path = manage_video(video, "audio")

        if not audio_path:
            return None
        else:
            print(Color.string("Then I have to download the video", Color.YELLOW))

    formats = video.get_extraction_url()
    if not formats:
        print(Color.string("Cannot fetch Youtube data on provided link. Is it private?", Color.RED))
        return None

    usable_formats = []

    if len(formats[media_type]) == 0:
        print(Color.string(f"No available formats for {media_type} type. Select one from those, it will then be converted", Color.YELLOW))
        for key in formats:
            usable_formats += formats[key]
    else:
        usable_formats = formats[media_type]

    selected_format = usable_formats[0] if best_quality else None

    while not selected_format:
        print("Choose a format to download:", end="")
        i = 0
        for format in usable_formats:
            i += 1
            display_format = {"Mime": format["mime"], "Bitrate": locale.format_string('%.2d', format["bitrate"], grouping=True)}
            print(f"\n{i}. ", end="")
            for elem in display_format:
                # padding system for a better view of the stats
                if elem != list(display_format.keys())[-1]:
                    padding = " " + "." * 25
                    print_padding = "{:.70s}"
                else:
                    padding = ""
                    print_padding = "{}"
                print(print_padding.format(Color.string(elem, Color.YELLOW) + ": " + Color.string(display_format[elem], Color.GREEN) + padding), end=" ")

        print("\n\n>>> ", end="")
        choice = str(msvcrt.getch()).split("'")[1].upper()
        print(choice)

        try:
            int_choice = int(choice)
            selected_format = usable_formats[int_choice - 1]
        except:
            print(Color.string("Wrong format index.", Color.RED))
            continue

    # mime example: audio/webm; codecs="opus"
    ext = selected_format["mime"].split("/")[1].split(";")[0]
    valid_title = media_management.get_valid_filename(video.title)
    filename = f"{output_folder}\\{valid_title}.{ext}"
    thumbnail = f"{output_folder}\\{valid_title}.jpg"
    ext_destination = "mp3" if media_type == "audio" else "mp4"

    download.download_file(selected_format["url"], filename)
    download.simple_download(video.thumbnail, thumbnail)

    filename = media_management.convert_to(filename, ext_destination, verbose)
    # if ext_destination == "mp3" and os.path.getsize(filename) > 10 * 1000 * 1000:
    #     print(Color.string("Converted file is too large, re-converting...", Color.RED))
    #     filename = media_management.convert_to(filename, ext_destination, verbose)

    if not filename:
        print(Color.string(f"Could not convert to {ext_destination}. Do you have ffmpeg in PATH?", Color.RED))
        os.remove(thumbnail)
        return None
    else:
        if not media_management.add_metadata(filename, thumbnail, video.author, video.title, verbose):
            print(Color.string(f"Could not add metadata for {video.title}.", Color.RED))
        else:
            print(Color.string(f"{filename} - Done.", Color.GREEN))

    if media_type == "video" and audio_path:
        print(Color.string("Merging audio and video together... ", Color.YELLOW), end="")
        filename = media_management.merge_video_audio(filename, audio_path, verbose)
        if not filename:
            print(Color.string("Error while merging audio and video files.", Color.RED))
        else:
            print(Color.string("Done.", Color.GREEN))

    return filename


# ░█▄█░█▀█░▀█▀░█▀█
# ░█░█░█▀█░░█░░█░█
# ░▀░▀░▀░▀░▀▀▀░▀░▀


if __name__ == "__main__":
    # Try to get the download directory from the Windows registry
    try:
        from winreg import *
        with OpenKey(HKEY_CURRENT_USER, 'SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders') as key:
            default_save_path = str(QueryValueEx(key, '{374DE290-123F-4565-9164-39C4925E467B}')[0])
    except:
        default_save_path = os.getcwd()

    # Verbosity parameter
    verbose = len(sys.argv) > 1 and sys.argv[1].lower() == "-v"

    banner = """
░█░█░█▀█░█░█░▀█▀░█░█░█▀▄░█▀▀░░░█▀▄░█▀█░█░█░█▀█░█░░░█▀█░█▀█░█▀▄░█▀▀░█▀▄
░░█░░█░█░█░█░░█░░█░█░█▀▄░█▀▀░░░█░█░█░█░█▄█░█░█░█░░░█░█░█▀█░█░█░█▀▀░█▀▄
░░▀░░▀▀▀░▀▀▀░░▀░░▀▀▀░▀▀░░▀▀▀░░░▀▀░░▀▀▀░▀░▀░▀░▀░▀▀▀░▀▀▀░▀░▀░▀▀░░▀▀▀░▀░▀
                                                            by Valenwe
    """
    if verbose:
        banner += Color.string("(Verbosity ENABLED)\n", Color.CYAN)
    print(Color.string(banner, Color.YELLOW, True))

    # Global variables
    # The input URL
    url = None

    # The custom class resulted from the URL
    url_type = None

    # The auto choice boolean state
    best_quality = True

    # Save folder
    output_folder = default_save_path

    # The user menu choice
    input_char = None

    # The menu loop
    end_loop = False

    while not end_loop:
        menu = [
            {"action": "url",
                "text": f"Enter URL [current: {Color.string(type(url_type).__name__ + ' <=> ' + url_type.url, Color.GREEN) if url_type else Color.string(url, Color.RED)}]"},
            {"action": "audio", "text": "Download audio from URL"},
            {"action": "video", "text": "Download video from URL"},
            {"action": "best_quality", "text":
                f"Automatically get best quality [current: {Color.string(best_quality, Color.GREEN if best_quality else Color.RED)}]"},
            {"action": "output_folder", "text": f"Set folder [current: {Color.string(output_folder, Color.YELLOW)}]"},
            {"action": "exit", "text": Color.string("Exit", Color.RED)}
        ]

        check_current_git_version()

        # display menu and get user input
        print("")
        for i in range(len(menu)):
            print(f"{i + 1}. {menu[i]['text']}")

        print("\n>>> ", end="")
        input_char = str(msvcrt.getch()).split("'")[1].upper()
        print(input_char)

        # Flush input buffer
        while msvcrt.kbhit():
            msvcrt.getch()

        # Try to get the entered action
        try:
            choice = int(input_char)
            for i in range(len(menu)):
                if i+1 == choice:
                    action = menu[i]["action"]
        except:
            print(Color.string(
                "Wrong input. Please retry.", Color.RED))
            continue

        # Processes
        if action == "exit":
            print(Color.string("Goodbye.", Color.GREEN))
            exit()

        elif action == "best_quality":
            best_quality = not best_quality

        elif action == "output_folder":
            temp_folder = input("Please enter your folder's path: \n>>> ")

            # take into account relative path with ./ or ../
            temp_folder = os.path.abspath(os.path.join(output_folder, temp_folder))

            while not os.path.isdir(temp_folder):
                print(Color.string("Path does not exist. Creating directoy... ", Color.YELLOW), end="")
                try:
                    path = Path(temp_folder)
                    path.mkdir(parents=True)
                    print(Color.string("Done.", Color.GREEN))
                except:
                    print(Color.string("Impossible to create the directory. Please retry.", Color.RED))
                    temp_folder = input("Please enter your folder's path: \n>>> ")

            output_folder = temp_folder

        elif action == "url":
            in_url = input("Please enter your Youtube URL: \n>>> ")
            url, url_type = detect_url(in_url)

        elif action == "audio" or action == "video":
            if url_type == None:
                print(Color.string("No url provided.", Color.RED))

            elif isinstance(url_type, ytb_classes.Playlist):
                videos = url_type.get_videos()
                if not videos:
                    print(Color.string("Cannot fetch Youtube data on provided link. Is it private?", Color.RED))
                    continue
                else:
                    print(Color.string(f"{len(videos)} video{'s' if len(videos) > 1 else ''} found in that Playlist.", Color.YELLOW))

                for video in tqdm(videos, desc="Videos remaining: ", colour="red"):
                    manage_video(video, action)
                exit()

            elif isinstance(url_type, ytb_classes.Video):
                manage_video(url_type, action)
                exit()

        input_char = None
