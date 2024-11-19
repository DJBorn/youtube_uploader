# YouTube Uploader

This script automates the process of:
1. Downloading videos from **Google Photos** to a local directory.
2. Uploading those videos to **YouTube**.

When downloading videos, the script will search for filenames in the format `YYYYMMDD_HHMMSS` and use that as the title for the YouTube upload (formatted as `YYYYMMDD HHMMSS`).

For example:
- A video file named `InShot_20241118_195443306` will be uploaded to YouTube with the title: **`20241118 195443`**.

---

## Prerequisites

### 1. Install Python
Ensure Python is installed on your system. You can download it from [python.org/downloads](https://www.python.org/downloads/).

### 2. Install Poetry
Poetry is used to manage dependencies. Install Poetry by following the [official installation guide](https://python-poetry.org/docs/#installation).

---

## Install Dependencies
Run the following command to install the required Python packages:
```bash
poetry install
```

## Setup Instructions
### 1. Generate Client Secrets
This script requires OAuth2 client secret keys for accessing Google Services:

- Google Photos: One client secret for downloading videos.
- YouTube: One or more client secrets for uploading videos (comma-separated if multiple accounts are used).

Follow these steps to generate the keys:

- Create client secrets from the Google Cloud Console.
- Save the secret files in the same directory as the script.


### 2. Create a .env File
Create a .env file in the root directory of the project with the following variables:

```
YOUTUBE_SECRET_FILES="<youtube_client_secret_file_1>,<youtube_client_secret_file_2>"
GOOGLE_PHOTOS_SECRET_FILE="<google_photos_client_secret_file>"

UPLOAD_DIRECTORY="<path_to_store_google_photos_videos>"
DELETED_DIRECTORY="<path_to_store_deleted_google_photos_videos>"
```

## How to Run the Script
### 1. Ensure your .env file is properly configured.
### 2. Run the script using Poetry:
```bash
poetry run python main.py [options]
```

## Available Options
- `--download-first`: Download videos from your Google Photos album before uploading to YouTube.
```shell
poetry run python main.py --download-first
```

- `--album-name <name>`: Specify the name of the Google Photos album to download videos from. Defaults to `Climbing` if not provided.
```shell
poetry run python main.py --download-first --album-name "Hiking"
```

## Important Notes
- **Backup Directory**: The script moves uploaded videos from the UPLOAD_DIRECTORY to the DELETED_DIRECTORY. This serves as a backup to prevent accidental data loss.
- **Client Secrets**: Make sure you do not share or expose your client secret files publicly.