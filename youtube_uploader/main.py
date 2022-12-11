#!/usr/bin/python

import os

import googleapiclient
from googleapiclient.errors import HttpError
from youtube_upload.client import YoutubeUploader

CLIENT_SECRET_FILE = "client_secret_252723081857-nr72rralklriqt6mh3d1d5idm1kbh8a9.apps.googleusercontent.com.json"

# client_secret_252723081857-nr72rralklriqt6mh3d1d5idm1kbh8a9.apps.googleusercontent.com.json
# client_secret_551581634693-mrsqtg54795liv2e5djvaph46c10fbvu.apps.googleusercontent.com.json


# This OAuth 2.0 access scope allows an application to upload files to the
# authenticated user's YouTube channel, but doesn't allow other types of access.
YOUTUBE_UPLOAD_SCOPE = "https://www.googleapis.com/auth/youtube.upload"
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"
MISSING_CLIENT_SECRETS_MESSAGE = ""

UPLOAD_DIRECTORY = r"C:\Users\Ilgoo\Videos\Bouldering"
PHOTO_DATETIME_FORMAT = "%Y%m%d_%H%M%S"


def upload_video(uploader, file_name):
    try:
        options = {
            "title": file_name[:-4].replace("_", " "),
            "description": "",
            "categoryId": "17",
            "privacyStatus": "public",  # Video privacy. Can either be "public", "private", or "unlisted"
            "kids": False,  # Specifies if the Video if for kids or not. Defaults to False.
            # Optional. Specifies video thumbnail.
        }
        file_path = f"{UPLOAD_DIRECTORY}/{file_name}"
        upload_response = uploader.upload(file_path, options)

        if "id" in upload_response:
            print(f"Deleting {file_path}")
            os.delete(file_path)
        return upload_response
    except googleapiclient.errors.ResumableUploadError as e:
        print(e.reason)
        exit()


def main():
    uploader = YoutubeUploader(secrets_file_path=CLIENT_SECRET_FILE)

    uploader.authenticate()

    youtube = uploader.youtube

    # upload_videos(uploader)

    add_to_playlist(youtube, "wdhWyUWEHv4")


def upload_videos(uploader):
    video_files = []
    for file in os.listdir(UPLOAD_DIRECTORY):
        video_files.append(file)
        video_files.sort()

    for file in video_files:
        upload_response = upload_video(uploader, file)
        print(upload_response)


def add_to_playlist(youtube, video_id):
    try:
        channel = youtube.playlists().list(channelId="UCO8DUUQN0rVnvsjmrNiOjrg", part="snippet,contentDetails").execute()
        # add_video_request=youtube.playlistItem().insert(
        #     part="snippet",
        #     body={
        #         'snippet': {
        #           'playlistId': playlistID,
        #           'resourceId': {
        #                   'kind': 'youtube#video',
        #               'videoId': videoID
        #             }
        #         #'position': 0
        #         }
        #     }
        # ).execute()

        print(channel)
    except googleapiclient.errors.HttpError as e:
        print (e)


if __name__ == "__main__":
    main()