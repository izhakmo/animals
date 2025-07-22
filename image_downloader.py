from datetime import datetime
from typing import Optional

import requests
from bs4 import BeautifulSoup


def get_main_image_url(url: str) -> Optional[str]:
    response = requests.get(url)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'html.parser')
    infobox = soup.find("table", class_="infobox")
    if infobox:
        img = infobox.find("img")
        if img and img.get("src"):
            return "https:" + img["src"]
    return None

def log_image_download_error(image_url: str, filename: str, error: Exception):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_message = f"[{timestamp}] file: {filename}, failed to download image from url: {image_url}. error: {error}"
    print(log_message)
    with open("image_download_errors.log", "a", encoding="utf-8") as f:
        f.write(log_message + "\n")

def download_image(image_url: str, filename: str):
    try:
        response = requests.get(image_url)
        response.raise_for_status()
        with open(filename, "wb") as f:
            f.write(response.content)
    except Exception as e:
        log_image_download_error(image_url, filename, e)

def fetch_and_save_image(base_url: str, href: str, name: str, dir_path: str):
    start_time = datetime.now()
    safe_name = name.replace('/', '_')
    image_url = get_main_image_url(base_url + href)
    if image_url:
        download_image(image_url, f"{dir_path}/{safe_name}.jpg")
    elapsed = datetime.now() - start_time
    print(f"Downloaded image for '{name}' in {elapsed.total_seconds():.2f} seconds") 