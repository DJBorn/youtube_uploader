#!/usr/bin/python
import logging
import os
import os.path
import re
import shutil
import time
from datetime import datetime

from dotenv import load_dotenv
from google.auth.exceptions import RefreshError
from googleapiclient.errors import HttpError

from youtube_uploader.utils.google_photos import download_album_videos
from youtube_uploader.utils.youtube import (
    upload_video,
    get_playlist_id_from_date,
    insert_video_into_playlist,
    get_authenticated_service,
    delete_credentials,
)

load_dotenv()  # Load env variables from .env file

# Date since last Upload: Nov 16, 2024

PHOTO_DATETIME_FORMAT = "%Y%m%d_%H%M%S"

logging.basicConfig(
    filename="youtube_uploader_logs.log",
    filemode="a",
    format="%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s",
    level=logging.DEBUG,
)

logging.getLogger().setLevel(logging.DEBUG)
logging.getLogger().addHandler(logging.StreamHandler())


def rename_files_in_directory(directory):
    video_files = []

    for file in os.listdir(directory):
        # Get the full file path
        old_file_path = os.path.join(directory, file)

        # Skip if it's not a file
        if not os.path.isfile(old_file_path):
            continue

        # Extract timestamp
        new_name = find_first_timestamp(file)

        if new_name:
            # Preserve file extension
            extension = os.path.splitext(file)[1]
            new_file_path = os.path.join(directory, f"{new_name}{extension}")

            # Rename the file
            os.rename(old_file_path, new_file_path)

            # Append the new file name to the list
            video_files.append(f"{new_name}{extension}")
        else:
            # If no timestamp found, add the original file name
            video_files.append(file)

    # Sort the list of renamed files
    video_files.sort()
    return video_files


def find_first_timestamp(text):
    """
    Finds the first substring in the format 'YYYYMMDD_HHMMSS' within the given text,
    even if it is embedded within other text.

    Parameters:
        text (str): The string to search for a timestamp.

    Returns:
        str or None: The first matching substring in the format 'YYYYMMDD_HHMMSS',
                     or None if no match is found.
    """
    pattern = r"\d{8}_\d{6}"
    match = re.search(pattern, text)
    return match.group() if match else None


def upload_videos():
    current_service = 0
    youtube_secret_files = os.getenv("YOUTUBE_SECRET_FILES").split(",")
    service = get_authenticated_service(youtube_secret_files[current_service])

    upload_directory = os.getenv("UPLOAD_DIRECTORY")
    video_files = rename_files_in_directory(upload_directory)

    i = 0
    while i < len(video_files):
        file = video_files[i]
        file_path = f"{upload_directory}/{file}"
        try:
            video_id = upload_video(service, file[:-4].replace("_", " "), file_path)
        except HttpError as e:
            logging.error(e.reason)
            if current_service == len(youtube_secret_files) - 1:
                logging.debug(f"Out of client secret files")
                exit()
            current_service += 1
            service.close()
            service = get_authenticated_service(youtube_secret_files[current_service])
            continue
        except RefreshError as e:
            logging.error(e)
            logging.debug(f"Deleting {youtube_secret_files[current_service]}...")
            delete_credentials(youtube_secret_files[current_service])
            service.close()
            service = get_authenticated_service(youtube_secret_files[current_service])
            continue

        logging.debug(f"Deleting {file_path}...")
        shutil.move(file_path, f"{os.getenv('DELETED_DIRECTORY')}/{file}")

        video_date = datetime.strptime(file[:-4], PHOTO_DATETIME_FORMAT)

        playlist_id = get_playlist_id_from_date(service, video_date)

        retried = 0
        while retried < 2:
            try:
                insert_video_into_playlist(service, video_id, playlist_id)
                break
            except HttpError as e:
                logging.error(e.reason)
                if current_service == len(youtube_secret_files) - 1:
                    logging.debug(f"Out of client secret files")
                    exit()
                current_service += 1
                logging.debug(f"Out of client secret files")
                service.close()
                service = get_authenticated_service(
                    youtube_secret_files[current_service]
                )
                retried += 1

        time.sleep(30)
        i += 1


import argparse


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--download-first",
        action="store_true",
        help="First download from your Google Photos album",
    )
    parser.add_argument(
        "--album-name",
        type=str,
        default="Climbing",
        help="The name of your album from Google Photos",
    )

    args = parser.parse_args()

    if args.download_first:
        download_album_videos(args.album_name)
    upload_videos()


if __name__ == "__main__":
    main()
