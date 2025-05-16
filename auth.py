import base64
import json
import os
from typing import Dict, Optional
import requests
from datetime import datetime, timedelta

class SpotifyAuth:
    def __init__(self, client_id: str, client_secret: str, refresh_token: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.refresh_token = refresh_token
        self.access_token = None
        self.token_expiry = None

    def get_access_token(self) -> str:
        """Get a valid access token, refreshing if necessary."""
        if self._is_token_expired():
            self._refresh_token()
        return self.access_token

    def _is_token_expired(self) -> bool:
        """Check if the current access token is expired or about to expire."""
        if not self.token_expiry:
            return True
        # Refresh if token expires in less than 5 minutes
        return datetime.now() + timedelta(minutes=5) >= self.token_expiry

    def _refresh_token(self) -> None:
        """Refresh the access token using the refresh token."""
        auth_string = f"{self.client_id}:{self.client_secret}"
        auth_bytes = auth_string.encode('utf-8')
        auth_base64 = base64.b64encode(auth_bytes).decode('utf-8')

        headers = {
            'Authorization': f'Basic {auth_base64}',
            'Content-Type': 'application/x-www-form-urlencoded'
        }

        data = {
            'grant_type': 'refresh_token',
            'refresh_token': self.refresh_token
        }

        response = requests.post('https://accounts.spotify.com/api/token', headers=headers, data=data)
        response.raise_for_status()
        
        token_data = response.json()
        self.access_token = token_data['access_token']
        # Set token expiry to 1 hour from now
        self.token_expiry = datetime.now() + timedelta(seconds=token_data.get('expires_in', 3600))

def get_auth_from_config(config_path: str) -> SpotifyAuth:
    """Create SpotifyAuth instance from config file."""
    import configparser
    config = configparser.ConfigParser()
    config.read(config_path)
    
    return SpotifyAuth(
        client_id=config.get('API', 'client_id'),
        client_secret=config.get('API', 'client_secret'),
        refresh_token=config.get('API', 'refresh_token')
    ) 