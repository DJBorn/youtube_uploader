#!/usr/bin/python
import logging
import os
import os.path
import time
from datetime import datetime

from youtube_uploader.utils.youtube import (
    upload_video,
    get_playlist_id_from_date,
    insert_video_into_playlist,
    get_authenticated_service,
)

CLIENT_SECRET_FILE = "client_secret_252723081857-nr72rralklriqt6mh3d1d5idm1kbh8a9.apps.googleusercontent.com.json"

UPLOAD_DIRECTORY = r"C:\Users\Ilgoo\Videos\Bouldering"
PHOTO_DATETIME_FORMAT = "%Y%m%d_%H%M%S"

logging.basicConfig(filename="youtube_uploader_logs.log",
                    filemode='a',
                    format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                    datefmt='%H:%M:%S',
                    level=logging.DEBUG)

logging.getLogger().setLevel(logging.DEBUG)


def upload_videos(service):
    video_files = []
    for file in os.listdir(UPLOAD_DIRECTORY):
        video_files.append(file)
        video_files.sort()

    for file in video_files:
        file_path = f"{UPLOAD_DIRECTORY}/{file}"
        video_id = upload_video(service, file[:-4].replace("_", " "), file_path)

        logging.debug(f"Deleting {file_path}...")
        os.remove(file_path)

        video_date = datetime.strptime(file[:-4], PHOTO_DATETIME_FORMAT)

        playlist_id = get_playlist_id_from_date(service, video_date)

        insert_video_into_playlist(service, video_id, playlist_id)
        time.sleep(5)


def main():
    service = get_authenticated_service()

    upload_videos(service)


if __name__ == "__main__":
    main()
