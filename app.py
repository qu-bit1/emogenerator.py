import os
import sys
import configparser
from typing import Dict, List, Optional, Tuple, Union
from requests import RequestException, HTTPError
from client import SpotifyClient
from auth import get_auth_from_config


class PlaylistFile:
    """File representation of a playlist."""

    def __init__(self, path: str, filename: str):
        self.path = path
        self.filename = filename
        self.lines = self.clean_lines()

    def clean_lines(self) -> List[str]:
        # Return the lines of this object's file stripped of whitespace.
        with open(self.path, "r") as f:
            lines = f.readlines()
        return [ln.strip() for ln in lines]

    def line_starts_with(self, prefix: str) -> Union[str, None]:
        # Return the first line beginning with prefix, or None.
        for ln in self.lines:
            if ln.lower().startswith(prefix):
                return ln
        return None

    def playlist_name(self) -> str:
        """Return this playlist's name on a specific line or the filename."""
        # Assumption: Line with playlist name begins with "name:"
        line = self.line_starts_with("name:")
        if not line:
            return self.filename
        colon_index = line.index(":")
        return line[colon_index + 1:].strip()

    def playlist_items(
            self,
            delimiter: str,
            order: str) -> List[Tuple[str, str]]:
        """Return a list of pairs of song names and their respective artist."""
        # Assumption: Track name and artists separated by delimiter
        # Assumption: order argument is "track artist" or "artist track"
        items = []
        track_index = order.split().index("track")
        artist_index = order.split().index("artist")
        for ln in self.lines:
            content = ln.split(delimiter)
            if len(content) < 2:
                continue
            track = content[track_index].strip()
            artist = content[artist_index].strip()
            items.append((track, artist))
        return items


def directory_files(path: str) -> List[str]:
    # Return the names of all files in a directory path
    filenames = []
    contents = os.listdir(path)
    for entry in contents:
        entry_path = os.path.join(path, entry)
        if os.path.isfile(entry_path):
            filenames.append(entry)
    return filenames

def filter_textfiles(filenames: List[str]) -> List[str]:
    # Return the names of all files with a .txt extension
    txtfile = lambda name: os.path.splitext(name)[1] == ".txt"
    return [fn for fn in filenames if txtfile(fn)]

def directory_textfiles(path: str) -> List[str]:
    # Return the names of all text files in a directory path
    if not os.path.isdir(path):
        raise NotADirectoryError('"{}" is not a directory.'.format(path))
    textfiles = filter_textfiles(directory_files(path))
    if not textfiles:
        message = '"{}" contains no textfiles'.format(path)
        raise FileNotFoundError(message)
    return textfiles

def get_playlists(directory_path: str) -> List[PlaylistFile]:
    """Return a list of PlaylistFile objects for each file to convert."""
    playlists = []
    textfiles = directory_textfiles(directory_path)
    for tf in textfiles:
        tf_path = os.path.join(directory_path, tf)
        tf_name = os.path.basename(tf_path)
        playlists.append(PlaylistFile(tf_path, tf_name))
    return playlists

parser = configparser.ConfigParser
config_error_msg = "Something went wrong reading your config file...\n"

def show_error(message: str) -> None:
    sys.stderr.write("Error: {}\n".format(message))
    sys.stderr.flush()
    sys.exit(1)

def quote_each_word(words: List[str]) -> str:
    quote = lambda word: f"'{word}'"
    return ", ".join([quote(word) for word in words])

def get_config_path() -> Optional[str]:
    project_root = os.path.dirname(__file__)
    path = os.path.join(project_root, "config", "config.ini")
    if not os.path.exists(path):
        show_error("Required configuration file 'config.ini' not found")
    return path

def read_config(config_path: str) -> parser:
    config = configparser.ConfigParser()
    with open(config_path, "r") as config_file:
        config.read_file(config_file)
    return config

def get_config_values(config: parser) -> Optional[Dict[str, str]]:
    try:
        values = {
            "directory_path": config.get("FILE_INFO", "directory_path"),
            "data_order":     config.get("FILE_INFO", "data_order"),
            "data_delimiter": config.get("FILE_INFO", "data_delimiter"),
            "user_id":        config.get("API", "user_id"),
            "client_id":      config.get("API", "client_id"),
            "client_secret":  config.get("API", "client_secret"),
            "refresh_token":  config.get("API", "refresh_token")
        }
    except configparser.Error as error:
        show_error(config_error_msg + str(error))
    else:
        return values

def check_empty(mapping: Dict[str, str]) -> None:
    empty_keys = [key for key in mapping if not mapping[key]]
    if empty_keys:
        quoted = quote_each_word(empty_keys)
        custom_msg = "Missing values for key(s) {}".format(quoted)
        show_error(config_error_msg + custom_msg)

def check_data_order(data_order: str) -> None:
    allowed = ["track artist", "artist track"]
    if data_order not in allowed:
        quoted = quote_each_word(allowed)
        custom_msg = "Key 'data_order' must equal one of {}".format(quoted)
        show_error(config_error_msg + custom_msg)

def get_playlist_files(dir_path: str) -> Optional[List[PlaylistFile]]:
    try:
        playlist_files = get_playlists(dir_path)
    except (NotADirectoryError, FileNotFoundError) as error:
        custom_msg = "Something went wrong reading the directory path...\n"
        show_error(custom_msg + str(error))
    else:
        return playlist_files

def convert_files(
        playlist_files: List[PlaylistFile],
        client: SpotifyClient,
        delimiter: str,
        order: str
        ) -> None:
    for file in playlist_files:
        name = file.playlist_name()
        items = file.playlist_items(delimiter, order)
        try:
            client.make_playlist_with_tracks(name, items)
        except HTTPError:
            show_error("Failed due to an HTTP error")
        except RequestException as error:
            custom_msg = "A request exception occurred...\n"
            show_error(custom_msg + str(error))

def run_app():
    config_path = get_config_path()
    config = get_config_values(read_config(config_path))
    check_empty(config)
    check_data_order(config["data_order"])
    files = get_playlist_files(config["directory_path"])
    
    # Initialize auth and client
    auth = get_auth_from_config(config_path)
    sp_client = SpotifyClient(auth, config["user_id"])
    
    delimiter, data_order = config["data_delimiter"], config["data_order"]
    convert_files(files, sp_client, delimiter, data_order)


if __name__ == "__main__":
    run_app()
