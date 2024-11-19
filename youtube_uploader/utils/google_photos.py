import os
from pathlib import Path

import requests
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/photoslibrary"]


def authenticate():
    """Authenticate the user and return the Photos Library service."""
    creds = None
    token_path = "../token.json"
    creds_path = os.getenv("GOOGLE_PHOTOS_SECRET_FILE")

    # Check if token.json exists
    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)

    # If there are no valid credentials, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(creds_path):
                raise FileNotFoundError(
                    f"{creds_path} not found. Please provide OAuth 2.0 credentials."
                )
            flow = InstalledAppFlow.from_client_secrets_file(creds_path, SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open(token_path, "w") as token:
            token.write(creds.to_json())

    service = build("photoslibrary", "v1", credentials=creds, static_discovery=False)
    return service


def get_album_id(service, album_name):
    """Retrieve the album ID for the given album name."""
    albums = []
    next_page_token = None

    while True:
        results = (
            service.albums().list(pageSize=50, pageToken=next_page_token).execute()
        )
        albums.extend(results.get("albums", []))
        next_page_token = results.get("nextPageToken")
        if not next_page_token:
            break

    for album in albums:
        if album.get("title") == album_name:
            return album.get("id")

    raise ValueError(f"Album with name '{album_name}' not found.")


def list_media_items(service, album_id):
    """List all media items in the specified album."""
    media_items = []
    next_page_token = None

    while True:
        body = {
            "albumId": album_id,
            "pageSize": 100,
            "pageToken": next_page_token,
            # Removed the 'filters' section to include all media items
        }

        response = service.mediaItems().search(body=body).execute()
        items = response.get("mediaItems", [])

        media_items.extend(items)

        next_page_token = response.get("nextPageToken")
        if not next_page_token:
            break

    return media_items


def download_media_items(media_items, download_dir):
    """Download the media items to the specified directory."""
    Path(download_dir).mkdir(parents=True, exist_ok=True)

    for item in media_items:
        filename = item.get("filename")
        base_url = item.get("baseUrl")
        # To download the original quality, append "=dv" to the baseUrl
        download_url = f"{base_url}=dv"
        filepath = os.path.join(download_dir, filename)

        if os.path.exists(filepath):
            print(f"File {filename} already exists. Skipping download.")
            continue

        print(f"Downloading {filename}...")
        response = requests.get(download_url, stream=True)
        if response.status_code == 200:
            with open(filepath, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            print(f"Downloaded {filename} successfully.")
        else:
            print(
                f"Failed to download {filename}. HTTP Status Code: {response.status_code}"
            )


def remove_media_items_from_album(service, album_id, media_item_ids):
    """Remove media items from the specified album."""
    if not media_item_ids:
        print("No media items to remove from the album.")
        return

    print(f"Removing {len(media_item_ids)} media item(s) from album '{album_id}'...")
    request_body = {"mediaItemIds": media_item_ids}

    try:
        response = (
            service.albums()
            .batchRemoveMediaItems(albumId=album_id, body=request_body)
            .execute()
        )
        print(
            f"Successfully removed {len(media_item_ids)} media item(s) from the album."
        )
    except Exception as e:
        print(f"An error occurred while removing media items from the album: {e}")


def download_album_videos(album_name):
    download_directory = os.getenv(
        "UPLOAD_DIRECTORY"
    )  # Directory to save downloaded videos

    # Authenticate and build the service
    service = authenticate()

    try:
        # Get the album ID
        album_id = get_album_id(service, album_name)
        print(f"Album ID for '{album_name}': {album_id}")

        # List media items
        media_items = list_media_items(service, album_id)
        print(f"Found {len(media_items)} media item(s) in album '{album_name}'.")

        if not media_items:
            print("No media items to download.")
            return

        # Download media items
        download_media_items(media_items, download_directory)

        # Extract media item IDs
        media_item_ids = [item["id"] for item in media_items]

        # Remove media items from the album
        remove_media_items_from_album(service, album_id, media_item_ids)

    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    download_album_videos()
