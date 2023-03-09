# ░▀█▀░█▄█░█▀█░█▀█░█▀▄░▀█▀░█▀▀
# ░░█░░█░█░█▀▀░█░█░█▀▄░░█░░▀▀█
# ░▀▀▀░▀░▀░▀░░░▀▀▀░▀░▀░░▀░░▀▀▀

import requests
import json
import re
import logging
from bs4 import BeautifulSoup
import socket
import time
from urllib.request import Request, urlopen
from urllib.parse import urlparse, parse_qs

# ░█░█░▀█▀░█▀▄░█▀▀░█▀█
# ░▀▄▀░░█░░█░█░█▀▀░█░█
# ░░▀░░▀▀▀░▀▀░░▀▀▀░▀▀▀

# HUGE THANKS TO https://github.com/ewtoombs
# => https://github.com/ytdl-org/youtube-dl/issues/28859


class Video:
    def __init__(self, url: str):
        try:
            self.id = re.search(r'(?<=v=)[^&]+', url).group(0)
            self.url = f"https://www.youtube.com/watch?v={self.id}"
        except:
            raise ValueError("Given link is not a Youtube video")

    def __repr__(self) -> str:
        return self.url

    def _get_api_key(self) -> tuple[requests.Session, str]:
        session = requests.Session()
        session.headers = {
            # This is to demonstrate how little the user agent matters
            'User-Agent': 'Hello Google :)',
        }

        # Hit the /watch endpoint, but we actually only want an API key lol.
        response = session.get(
            "https://www.youtube.com/watch",
            params={'v': id},
        ).content.decode()

        soup = BeautifulSoup(response, "html.parser")

        # get the key
        key = None
        for script_tag in soup.find_all("script"):
            script = script_tag.string
            if script is not None:
                match = re.search(r'"INNERTUBE_API_KEY":"([^"]+)"', script)
                if match is not None:
                    key = match.group(1)
                    break
        assert key is not None
        return session, key

    def _get_valid_format(self) -> dict:
        session, key = self._get_api_key()
        # OK, now use the API key to get the actual streaming data.
        post_data = {
            'context': {
                'client': {
                    'clientName': 'ANDROID',
                    'clientVersion': '16.05',
                },
            },
            'videoId': self.id,
        }

        data = json.loads(session.post(
            "https://www.youtube.com/youtubei/v1/player",
            params={'key': key},
            data=json.dumps(post_data),
        ).content)

        return data

    def get_extraction_url(self) -> dict:
        data = self._get_valid_format()

        # retry counter
        retry = 3
        while "videoDetails" not in data.keys() and retry > 0:
            data = self._get_valid_format()
            retry -= 1
            logging.error("Could not fetch video data, retrying...")
            time.sleep(2)

        if "videoDetails" not in data.keys():
            logging.error("Exiting :(")
            exit()

        # Set the video title
        self.title = data["videoDetails"]["title"]

        # Get the standard thumbnail from the youtube img domain
        # also accessible through data["videoDetails"]["thumbnail"]["thumbnails"][0]["url"]
        self.thumbnail = f"https://i.ytimg.com/vi/{self.id}/sddefault.jpg"

        # Get the author
        self.author = data["videoDetails"]["author"]

        # Now fetch the intel from the js JSON
        all_info = {"formats": []}

        raw_formats = data["streamingData"]["adaptiveFormats"] if "adaptiveFormats" in data["streamingData"].keys() else data["streamingData"]["formats"]
        for format in raw_formats:
            try:
                important_keys = {"itag": format["itag"], "mime": format["mimeType"],
                                  "url": format["url"], "bitrate": format["averageBitrate"]}

                # In case of video
                if "qualityLabel" in format.keys():
                    important_keys["video_quality"] = format["qualityLabel"]

                # In case of audio
                if "audioSampleRate" in format.keys():
                    important_keys["samplerate"] = format["audioSampleRate"]

                all_info["formats"].append(important_keys)
            except:
                logging.error(f"Could not fetch format {format}")

        # Create separate lists for audio and video
        audio_list = []
        video_list = []

        for item in all_info["formats"]:
            if 'video' in item['mime']:
                video_list.append(item)
            elif 'audio' in item['mime']:
                audio_list.append(item)

        # Sort by bitrate and media type
        audio_list = sorted(
            audio_list, key=lambda x: x['bitrate'], reverse=True)
        video_list = sorted(
            video_list, key=lambda x: x['bitrate'], reverse=True)

        return {"audio": audio_list, "video": video_list}

# ░█▀█░█░░░█▀█░█░█░█░░░▀█▀░█▀▀░▀█▀
# ░█▀▀░█░░░█▀█░░█░░█░░░░█░░▀▀█░░█░
# ░▀░░░▀▀▀░▀░▀░░▀░░▀▀▀░▀▀▀░▀▀▀░░▀░

# Code inspired from Pytube module


class Playlist:
    def __init__(self, url: str):
        try:
            # get the playlist ID
            parsed = urlparse(url)
            self.id = parse_qs(parsed.query)['list'][0]
            self.url = f"https://www.youtube.com/playlist?list={self.id}"
        except:
            raise ValueError("Given link is not a Youtube playlist")

        self._html = None

    def __repr__(self) -> str:
        return self.url

    @property
    def html(self) -> str:
        if self._html:
            return self._html

        request = Request(self.url,
                          headers={"User-Agent": "Mozilla/5.0",
                                   "accept-language": "en-US,en"},
                          method="GET")

        self._html = urlopen(request, timeout=socket._GLOBAL_DEFAULT_TIMEOUT)
        self._html = self._html.read().decode("utf-8")
        return self._html

    def _get_initial_data(self) -> dict:
        patterns = [r'ytInitialData =\s*({.+?});']

        for pattern in patterns:
            regex = re.compile(pattern)
            result = regex.search(self.html)
            if result:
                js = json.loads(result.group(1))
                if "contents" in js.keys():
                    return js

    def get_videos(self) -> list[Video]:
        """ Get videos (works only for <= 100 videos)
        """
        init_data = self._get_initial_data()
        section_contents = init_data["contents"][
            "twoColumnBrowseResultsRenderer"][
            "tabs"][0]["tabRenderer"]["content"][
            "sectionListRenderer"]["contents"]
        try:
            # Playlist without submenus
            important_content = section_contents[
                0]["itemSectionRenderer"][
                "contents"][0]["playlistVideoListRenderer"]
        except (KeyError, IndexError, TypeError):
            # Playlist with submenus
            important_content = section_contents[
                1]["itemSectionRenderer"][
                "contents"][0]["playlistVideoListRenderer"]
        videos = important_content["contents"]

        videos = [
            Video(f"https://www.youtube.com/watch?v={x['playlistVideoRenderer']['videoId']}") for x in videos]

        return videos
