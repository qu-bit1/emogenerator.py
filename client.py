from json import dumps
from typing import List, Tuple, Dict, Union, Any
import requests
from auth import SpotifyAuth

SEARCH_URL = "https://api.spotify.com/v1/search"
CONTAINS_URL = "https://api.spotify.com/v1/me/tracks/contains"
PLAYLIST_URL = "https://api.spotify.com/v1/users/{}/playlists"
ADD_TRACK_URL = "https://api.spotify.com/v1/playlists/{}/tracks"

class SpotifyClient:
    
    def __init__(self, auth: SpotifyAuth, user_id: str):
        self.auth = auth
        self.user_id = user_id

    def find_track_ids(self, track:str, artist:str) -> List[str]:
        query = "{} artist:{}".format(track, artist)
        request_args = {
            "url" : SEARCH_URL,
            "headers" : {"Authorization": "Bearer " + self.auth.get_access_token()},
            "params": {"q": query, "type": "track", "limit": 20}
        }
        response_json = self.send_request("GET", request_args)
        tracks_found = response_json["tracks"]["items"]
        return [result["id"] for result in tracks_found]

    def find_saved_track(self, track_ids: List[str]) -> Union[str, None]:
        request_args = {
            "url": CONTAINS_URL,
            "headers" : {"Authorization": "Bearer " + self.auth.get_access_token()},
            "params": {"ids": track_ids}
        }
        response_json = self.send_request("GET", request_args)
        return self.first_saved(list(zip(track_ids, response_json)))

    def get_track_id(self, track: str, artist: str) -> Union[str, None]:
        track_results = self.find_track_ids(track, artist)
        if not track_results:
            return None
        saved_track = self.find_saved_track(track_results)
        if not saved_track:
            return track_results[0]
        return saved_track

    def create_playlist(self, name: str) -> str:
        request_args = {
            "url": PLAYLIST_URL.format(self.user_id),
            "headers": {
                "Authorization": "Bearer " + self.auth.get_access_token(),
                "Content-Type": "application/json"
            },
            "data": dumps({"name": name})
        }
        response_json = self.send_request("POST", request_args)
        # Playlist ID used to add tracks to the playlist
        return response_json["id"]

    def add_playlist_tracks(self, pid: str, track_uris: List[str]) -> None:
        request_args = {
            "url": ADD_TRACK_URL.format(pid),
            "headers": {
                "Authorization": "Bearer " + self.auth.get_access_token(),
                "Content-Type": "application/json"
            }
        }
        # Maximum of 100 items per request
        subsets = self.subsets_of_size(track_uris, 100)
        for subset in subsets:
            request_body = {"uris": subset}
            request_args["data"] = dumps(request_body)
            self.send_request("POST", request_args)

    def make_playlist_with_tracks(
            self,
            playlist_name: str,
            tracks_with_artist: List[Tuple[str, str]]
        ) -> None:
        # Get track IDs and filter out None values
        track_ids = []
        for track, artist in tracks_with_artist:
            track_id = self.get_track_id(track, artist)
            if track_id:
                track_ids.append(track_id)
            else:
                print(f"Could not find track: {track} by {artist}")
        
        if not track_ids:
            print("No valid tracks found to add to playlist")
            return
            
        track_uris = ["spotify:track:{}".format(tid) for tid in track_ids]
        if track_uris:
            playlist_id = self.create_playlist(playlist_name)
            self.add_playlist_tracks(playlist_id, track_uris)

    def send_request(self, method: str, request_args: Dict) -> Any:
        try:
            response = requests.request(method, **request_args)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            print(f"HTTP Error: {e}")
            print(f"Response status code: {e.response.status_code}")
            print(f"Response body: {e.response.text}")
            raise
        except requests.exceptions.RequestException as e:
            print(f"Request Error: {e}")
            raise

    def first_saved(self, tracks_saved: List[Tuple[str, bool]]) -> Union[str, None]:
        for tid, saved in tracks_saved:
            if saved:
                return tid
        return None

    def subsets_of_size(self, items: List, size: int) -> List[List]:
        subsets = []
        duplicate = list(items)
        while duplicate:
            subset = duplicate[:size]
            subsets.append(subset)
            duplicate = duplicate[size:]
        return subsets
