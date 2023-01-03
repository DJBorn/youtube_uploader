import json
import logging
import os
import os.path
from datetime import datetime

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload

CLIENT_SECRET_FILE = "client_secret_252723081857-nr72rralklriqt6mh3d1d5idm1kbh8a9.apps.googleusercontent.com.json"

# client_secret_252723081857-nr72rralklriqt6mh3d1d5idm1kbh8a9.apps.googleusercontent.com.json
# client_secret_551581634693-mrsqtg54795liv2e5djvaph46c10fbvu.apps.googleusercontent.com.json

YOUTUBE_UPLOAD_SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtubepartner-channel-audit",
    "https://www.googleapis.com/auth/youtubepartner",
]
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"
MISSING_CLIENT_SECRETS_MESSAGE = ""

PLAYLIST_MAX_RESULTS = 50


def get_authenticated_service():
    credentials = _get_user_credentials()
    return build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, credentials=credentials)


def _get_user_credentials():
    if os.path.isfile("credentials.json"):
        return Credentials.from_authorized_user_file("credentials.json")
    flow = InstalledAppFlow.from_client_secrets_file(
        CLIENT_SECRET_FILE, YOUTUBE_UPLOAD_SCOPES
    )
    credentials = flow.run_local_server()
    with open("credentials.json", "w") as file:
        json.dump(json.loads(credentials.to_json()), file)
    return credentials


def upload_video(service, name, file_path):
    logging.debug("Uploading Video...")
    try:
        upload_response = (
            service.videos()
            .insert(
                part="snippet,status",
                body={
                    "snippet": {"categoryId": "17", "description": "", "title": name},
                    "status": {"privacyStatus": "public"},
                },
                media_body=MediaFileUpload(file_path),
            )
            .execute()
        )
    except HttpError as e:
        logging.error(e.reason)
        exit()

    return upload_response["id"]


def insert_video_into_playlist(service, video_id, playlist_id):
    logging.debug(f"Inserting video {video_id} into playlist {playlist_id}")
    try:
        service.playlistItems().insert(
            part="snippet",
            body={
                "snippet": {
                    "playlistId": playlist_id,
                    "resourceId": {"kind": "youtube#video", "videoId": video_id},
                }
            },
        ).execute()
    except HttpError as e:
        logging.error(e.reason)
        exit()


def get_playlist_id_from_date(service, video_date: datetime):
    playlist_name = video_date.strftime("%m/%d/%Y")
    playlists = _get_list_of_playlists(service)

    playlist_id_to_upload = [
        playlist["id"]
        for playlist in playlists
        if playlist["snippet"]["title"] == playlist_name
    ]
    if playlist_id_to_upload:
        logging.debug(f"Found existing playlist '{playlist_name}'")
        return playlist_id_to_upload[0]

    logging.debug(f"Creating playlist '{playlist_name}'")
    try:
        playlist_response = (
            service.playlists()
            .insert(
                part="status,snippet",
                body={
                    "snippet": {"title": playlist_name},
                    "status": {"privacyStatus": "public"},
                },
            )
            .execute()
        )
    except HttpError as e:
        logging.error(e.reason)
        exit()

    return playlist_response["id"]


def _get_list_of_playlists(service):
    channel_id = _get_users_youtube_channel_id(service)

    playlists = []
    playlists_response = (
        service.playlists()
        .list(channelId=channel_id, part="snippet", maxResults=PLAYLIST_MAX_RESULTS)
        .execute()
    )

    playlists.extend(playlists_response["items"])

    next_page_token = playlists_response.get("nextPageToken")

    while next_page_token:
        playlists_response = (
            service.playlists()
            .list(
                channelId=channel_id,
                part="snippet",
                maxResults=PLAYLIST_MAX_RESULTS,
                pageToken=next_page_token,
            )
            .execute()
        )
        playlists.extend(playlists_response["items"])
        next_page_token = playlists_response.get("nextPageToken")

    return playlists


def _get_users_youtube_channel_id(service):
    channels = service.channels().list(part="id", mine=True).execute()
    if "items" in channels and len(channels["items"]) == 1:
        return channels["items"][0]["id"]
    logging.error("Could not get channels")
