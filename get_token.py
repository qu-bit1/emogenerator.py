import base64
import configparser
import json
import os
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse
import requests

# Spotify API endpoints
AUTH_URL = 'https://accounts.spotify.com/authorize'
TOKEN_URL = 'https://accounts.spotify.com/api/token'
REDIRECT_URI = 'http://localhost:8888/callback'

class CallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Handle the callback from Spotify authorization."""
        # Parse the authorization code from the callback URL
        query_components = parse_qs(urlparse(self.path).query)
        if 'code' in query_components:
            self.server.auth_code = query_components['code'][0]
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b"Authorization successful! You can close this window.")
        else:
            self.send_response(400)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b"Authorization failed! Please try again.")

def get_refresh_token(client_id: str, client_secret: str) -> str:
    """Get a refresh token from Spotify."""
    # Create the authorization URL
    auth_params = {
        'client_id': client_id,
        'response_type': 'code',
        'redirect_uri': REDIRECT_URI,
        'scope': 'playlist-modify-public playlist-modify-private user-library-read'
    }
    auth_url = f"{AUTH_URL}?{'&'.join(f'{k}={v}' for k, v in auth_params.items())}"
    
    # Start local server to receive the callback
    server = HTTPServer(('localhost', 8888), CallbackHandler)
    server.auth_code = None
    
    # Open the authorization URL in the default browser
    print("Opening browser for Spotify authorization...")
    webbrowser.open(auth_url)
    
    # Wait for the callback
    print("Waiting for authorization...")
    server.handle_request()
    
    if not server.auth_code:
        raise Exception("Failed to get authorization code")
    
    # Exchange the authorization code for a refresh token
    auth_string = f"{client_id}:{client_secret}"
    auth_bytes = auth_string.encode('utf-8')
    auth_base64 = base64.b64encode(auth_bytes).decode('utf-8')
    
    headers = {
        'Authorization': f'Basic {auth_base64}',
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    
    data = {
        'grant_type': 'authorization_code',
        'code': server.auth_code,
        'redirect_uri': REDIRECT_URI
    }
    
    response = requests.post(TOKEN_URL, headers=headers, data=data)
    response.raise_for_status()
    
    return response.json()['refresh_token']

def get_user_id(access_token: str) -> str:
    """Get the user's Spotify ID."""
    headers = {
        'Authorization': f'Bearer {access_token}'
    }
    response = requests.get('https://api.spotify.com/v1/me', headers=headers)
    response.raise_for_status()
    return response.json()['id']

def update_config(config_path: str, client_id: str, client_secret: str, refresh_token: str, user_id: str) -> None:
    """Update the config file with the new credentials."""
    config = configparser.ConfigParser()
    config.read(config_path)
    
    config['API']['client_id'] = client_id
    config['API']['client_secret'] = client_secret
    config['API']['refresh_token'] = refresh_token
    config['API']['user_id'] = user_id
    
    with open(config_path, 'w') as f:
        config.write(f)

def main():
    # Get the config file path
    project_root = os.path.dirname(__file__)
    config_path = os.path.join(project_root, "config", "config.ini")
    
    # Get credentials from user
    print("Please enter your Spotify API credentials:")
    client_id = input("Client ID: ").strip()
    client_secret = input("Client Secret: ").strip()
    
    try:
        # Get the refresh token
        refresh_token = get_refresh_token(client_id, client_secret)
        
        # Get initial access token to fetch user ID
        auth_string = f"{client_id}:{client_secret}"
        auth_bytes = auth_string.encode('utf-8')
        auth_base64 = base64.b64encode(auth_bytes).decode('utf-8')
        
        headers = {
            'Authorization': f'Basic {auth_base64}',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        data = {
            'grant_type': 'refresh_token',
            'refresh_token': refresh_token
        }
        
        response = requests.post(TOKEN_URL, headers=headers, data=data)
        response.raise_for_status()
        access_token = response.json()['access_token']
        
        # Get user ID
        user_id = get_user_id(access_token)
        
        # Update the config file
        update_config(config_path, client_id, client_secret, refresh_token, user_id)
        
        print("\nSuccess! Your config file has been updated with the new credentials.")
        print("You can now run app.py to create your playlists.")
        
    except Exception as e:
        print(f"\nError: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 