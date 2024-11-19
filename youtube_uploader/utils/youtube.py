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

YOUTUBE_UPLOAD_SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtubepartner-channel-audit",
    "https://www.googleapis.com/auth/youtubepartner",
]
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"
MISSING_CLIENT_SECRETS_MESSAGE = ""

PLAYLIST_MAX_RESULTS = 50


def get_authenticated_service(client_secret_file):
    credentials = _get_user_credentials(client_secret_file)
    return build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, credentials=credentials)


def _get_user_credentials(client_secret_file):
    credential_id = client_secret_file.split("-")[0].split("_")[-1]
    credentials_json = f"credentials_{credential_id}.json"
    if os.path.isfile(credentials_json):
        return Credentials.from_authorized_user_file(credentials_json)
    flow = InstalledAppFlow.from_client_secrets_file(
        client_secret_file, YOUTUBE_UPLOAD_SCOPES
    )
    credentials = flow.run_local_server()
    with open(credentials_json, "w") as file:
        json.dump(json.loads(credentials.to_json()), file)
    return credentials


def delete_credentials(client_secret_file):
    credential_id = client_secret_file.split("-")[0].split("_")[-1]
    credentials_json = f"credentials_{credential_id}.json"
    os.remove(credentials_json)


def upload_video(service, name, file_path):
    logging.debug("Uploading Video...")

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

    return upload_response["id"]


def insert_video_into_playlist(service, video_id, playlist_id):
    logging.debug(f"Inserting video {video_id} into playlist {playlist_id}")
    service.playlistItems().insert(
        part="snippet",
        body={
            "snippet": {
                "playlistId": playlist_id,
                "resourceId": {"kind": "youtube#video", "videoId": video_id},
            }
        },
    ).execute()


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
