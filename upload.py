import os
import requests
import webbrowser
import http.server
import socketserver
import urllib.parse
from pathlib import Path
from threading import Thread
import time
import re
from tqdm import tqdm
from requests_toolbelt.multipart.encoder import MultipartEncoder, MultipartEncoderMonitor

# Configuration
CLIENT_ID = ""  # Your DeviantArt Client ID
CLIENT_SECRET = ""  # Your Client Secret
REDIRECT_URI = "http://localhost:3000/callback"  # Must be whitelisted in DeviantArt app settings
AUTH_URL = "https://www.deviantart.com/oauth2/authorize"
TOKEN_URL = "https://www.deviantart.com/oauth2/token"
STASH_SUBMIT_URL = "https://www.deviantart.com/api/v1/oauth2/stash/submit"
PUBLISH_URL = "https://www.deviantart.com/api/v1/oauth2/stash/publish"
BASE_DESCRIPTION = ""  # Base description
TAGS = [""]  # Customize tags
FOLDER_ID = ""  # Your gallery folderid; set to None for default gallery
ACCESS_TOKEN_FILE = "access_token.txt"  # File to store access token
IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png", ".gif")

# Global variable to store authorization code
auth_code = None

def parse_filename_to_title(filename):
    name_without_ext = filename.rsplit('.', 1)[0]
    name_without_resized = name_without_ext.replace('_resized', '')
    parts = name_without_resized.split('_')
    if len(parts) < 3 or not parts[0].startswith('mosaic'):
        return "Unknown", "1"
    name_part = parts[1]
    image_count = parts[2]
    cleaned_name = re.sub(r'-+', '-', name_part).replace('-', ' ').strip()
    cleaned_name = ' '.join(word.capitalize() for word in cleaned_name.split())
    return cleaned_name, image_count

def start_local_server(port=3000):
    class OAuthHandler(http.server.SimpleHTTPRequestHandler):
        def do_GET(self):
            global auth_code
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            query = urllib.parse.urlparse(self.path).query
            params = urllib.parse.parse_qs(query)
            if "code" in params:
                auth_code = params["code"][0]
                self.wfile.write(b"Authorization successful! You can close this window.")
            else:
                self.wfile.write(b"Error: No authorization code received.")
    try:
        with socketserver.TCPServer(("", port), OAuthHandler) as httpd:
            print(f"Local server started at http://localhost:{port}")
            httpd.handle_request()
            print("Local server stopped.")
    except OSError as e:
        print(f"Error starting server on port {port}: {e}")
        raise

def get_access_token():
    if os.path.exists(ACCESS_TOKEN_FILE):
        with open(ACCESS_TOKEN_FILE, "r") as f:
            token = f.read().strip()
            if token:
                print("Using stored access token.")
                return token
        os.remove(ACCESS_TOKEN_FILE)
    auth_params = {
        "response_type": "code",
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "scope": "stash browse publish",
        "state": "random_state"
    }
    auth_url = f"{AUTH_URL}?{urllib.parse.urlencode(auth_params)}"
    print(f"Opening browser for authorization: {auth_url}")
    webbrowser.open(auth_url)
    server_thread = Thread(target=start_local_server)
    server_thread.start()
    server_thread.join()
    if not auth_code:
        raise Exception("Failed to obtain authorization code.")
    token_data = {
        "grant_type": "authorization_code",
        "code": auth_code,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "redirect_uri": REDIRECT_URI
    }
    response = requests.post(TOKEN_URL, data=token_data)
    response.raise_for_status()
    token_json = response.json()
    access_token = token_json.get("access_token")
    if not access_token:
        raise Exception(f"Failed to obtain access token: {token_json}")
    with open(ACCESS_TOKEN_FILE, "w") as f:
        f.write(access_token)
    print("Access token saved to access_token.txt")
    return access_token

def get_image_files():
    root_dir = Path(__file__).parent
    return [f for f in root_dir.iterdir() if f.is_file() and f.suffix.lower() in IMAGE_EXTENSIONS]

def upload_image(file_path, caption, description, tags, access_token):
    try:
        file = open(file_path, 'rb')
        fields = []
        fields.append(('test', (file_path.name, file, 'application/octet-stream')))
        fields.append(('title', caption))
        fields.append(('artist_comments', description))
        for t in tags:
            fields.append(('tags[]', t))
        fields.append(('access_token', access_token))
        encoder = MultipartEncoder(fields=fields)
        pbar = tqdm(total=encoder.len, unit='B', unit_scale=True, desc=f"Uploading {file_path.name}", leave=True)
        monitor = MultipartEncoderMonitor(encoder, lambda m: pbar.update(m.bytes_read - pbar.n))
        headers = {'Content-Type': monitor.content_type}
        response = requests.post(STASH_SUBMIT_URL, data=monitor, headers=headers)
        pbar.close()
        file.close()
        response.raise_for_status()
        result = response.json()
        if result.get("status") == "success":
            itemid = result.get("itemid")
            stash_url = f"https://sta.sh/0{int(itemid):x}" if itemid else "https://sta.sh/"
            print(f"Successfully uploaded {file_path.name}: itemid={itemid}, url={stash_url}")
            return itemid, stash_url
        else:
            print(f"Upload failed: {result.get('error_description', 'Unknown error')}")
            return None, None
    except Exception as e:
        print(f"Error uploading {file_path.name}: {e}")
        return None, None

def publish_image(itemid, caption, description, tags, folderid, access_token):
    try:
        data = {
            "itemid": itemid,
            "title": caption,
            "artist_comments": description,
            "tags[]": tags,
            "is_mature": "false",
            "access_token": access_token
        }
        if folderid:
            data["folderid"] = folderid
        response = requests.post(PUBLISH_URL, data=data)
        response.raise_for_status()
        result = response.json()
        if result.get("status") == "success":
            print(f"Published itemid={itemid} to gallery: deviationid={result['deviationid']}")
            return True
        else:
            print(f"Publish failed: {result.get('error_description', 'Unknown error')}")
            return False
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 403:
            print("Publish failed, check 'publish' scope or FOLDER_ID.")
        else:
            print(f"Error publishing: {e}")
        return False

def main():
    try:
        access_token = get_access_token()
    except Exception as e:
        print(f"Auth error: {e}")
        return

    image_files = get_image_files()
    if not image_files:
        print("No images found.")
        return
    print(f"Found {len(image_files)} image(s) to upload.")

    for index, image_path in enumerate(image_files, start=11):
        name, image_count = parse_filename_to_title(image_path.name)
        # Split name into individual tags to avoid spaces in DeviantArt tags
        tags_list = TAGS + name.split()
        caption = f"Mosaic - {name} #{index}"
        description = f"{BASE_DESCRIPTION} Mosaic made of {image_count} images."
        print(f"Processing {image_path.name} as '{caption}' with tags: {tags_list}")

        itemid, stash_url = upload_image(image_path, caption, description, tags_list, access_token)
        if not itemid:
            print("Upload failed, skipping publish.")
            continue

        if not publish_image(itemid, caption, description, tags_list, FOLDER_ID, access_token):
            print(f"Manual publish needed: {stash_url}")

        time.sleep(2)

if __name__ == "__main__":
    main()
