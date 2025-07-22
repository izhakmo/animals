import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from typing import Dict, List, Optional

import requests
from bs4 import BeautifulSoup

from constants import TABLE_HEADER_TAG, TABLE_ROW_TAG, TABLE_CELL_TAG
from report_generator import generate_html_report
from web_scrapper import (
    find_web_table_and_headers,
    extract_name_and_link,
    extract_list_link,
    extract_types_from_cell,
    is_incomplete_row,
    has_invalid_type,
)


def fetch_and_parse_web_table(base_url: str, suffix_url: str, name_header: str, types_header: str) -> Dict[
    str, List[str]]:
    full_url = base_url + suffix_url
    header_indices, target_table = find_web_table_and_headers(name_header, types_header, full_url)

    result: Dict[str, List[str]] = {}
    animals_with_invalid_types = []
    lists_log = []

    dir_path = "tmp"
    create_dir_if_not_exist(dir_path)

    download_tasks = []
    # Process table rows
    for row in target_table.find_all(TABLE_ROW_TAG)[1:]:
        cells = row.find_all([TABLE_CELL_TAG, TABLE_HEADER_TAG])
        if is_incomplete_row(cells, header_indices):
            continue

        # Extract name and types
        name_cell = cells[header_indices['name']]
        name, href = extract_name_and_link(name_cell)

        if href:
            download_tasks.append((base_url, href, name, dir_path))

        types_cell = cells[header_indices['types']]
        types = extract_types_from_cell(types_cell)

        if list_link := extract_list_link(name_cell):
            lists_log.append(f"{name} | {types} | {list_link}")

        # Check for empty or non-alphanumeric types
        if has_invalid_type(types):
            animals_with_invalid_types.append(" | ".join(cell.get_text(strip=True) for cell in cells))
            types = ["undefined type"]

        # Populate dictionary
        for t in types:
            if t not in result:
                result[t] = []
            result[t].append(name)

    write_log_file("animals_with_invalid_types.log", animals_with_invalid_types)
    write_log_file("animals_with_lists.log", lists_log)

    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = [executor.submit(fetch_and_save_image, *args) for args in download_tasks]
        for future in as_completed(futures):
            try:
                future.result()
            except Exception as e:
                print(f"Error in image download thread: {e}, future: {future}")
    print("All image download threads have finished.")

    generate_html_report(result, dir_path, "report.html")

    return result


def write_log_file(filename: str, log_entries: List[str]) -> None:
    """Write log entries to a file, one per line."""
    with open(filename, "w", encoding="utf-8") as f:
        for line in log_entries:
            f.write(line + "\n")


def create_dir_if_not_exist(dir_path: str) -> None:
    os.makedirs(dir_path, exist_ok=True)


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
    # Sanitize name for filename
    safe_name = name.replace('/', '_')
    image_url = get_main_image_url(base_url + href)
    if image_url:
        download_image(image_url, f"{dir_path}/{safe_name}.jpg")
    elapsed = datetime.now() - start_time
    print(f"Downloaded image for '{name}' in {elapsed.total_seconds():.2f} seconds")
