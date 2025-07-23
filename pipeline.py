import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List

from constants import TABLE_HEADER_TAG, TABLE_ROW_TAG, TABLE_CELL_TAG
from image_downloader import fetch_and_save_image
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
    """
    Fetches a web page table, parses animal names and types, downloads images, and generates an HTML report.

    Args:
        base_url (str): The base URL of the website (e.g., 'https://en.wikipedia.org').
        suffix_url (str): The path to the specific page containing the table.
        name_header (str): The column header for the name field.
        types_header (str): The column header for the types field.

    Returns:
        Dict[str, List[str]]: A dictionary mapping each type to a list of animal names.
    """
    full_url = base_url + suffix_url
    # Find the target table and header indices
    header_indices, target_table = find_web_table_and_headers(name_header, types_header, full_url)

    result: Dict[str, List[str]] = {}
    rows_with_invalid_types = []
    lists_log = []

    dir_path = "tmp"
    create_dir_if_not_exist(dir_path)

    download_tasks = []
    # Process each row in the table (skip header row)
    for row in target_table.find_all(TABLE_ROW_TAG)[1:]:
        cells = row.find_all([TABLE_CELL_TAG, TABLE_HEADER_TAG])
        if is_incomplete_row(cells, header_indices):
            continue

        # Extract name and link
        name_cell = cells[header_indices['name']]
        name, href = extract_name_and_link(name_cell)

        # Queue image download if a link is present
        if href:
            download_tasks.append((base_url, href, name, dir_path))

        # Extract types
        types_cell = cells[header_indices['types']]
        types = extract_types_from_cell(types_cell)

        # Log if the name cell contains a 'list' link
        if list_link := extract_list_link(name_cell):
            lists_log.append(f"{name} | {types} | {list_link}")

        # Check for invalid types
        if has_invalid_type(types):
            rows_with_invalid_types.append(" | ".join(cell.get_text(strip=True) for cell in cells))
            types = ["undefined type"]

        # Populate dictionary
        for t in types:
            if t not in result:
                result[t] = []
            result[t].append(name)

    write_log_file("rows_with_invalid_types.log", rows_with_invalid_types)
    write_log_file("lists_log.log", lists_log)

    # use threads to download images 
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
    with open(filename, "w", encoding="utf-8") as f:
        for line in log_entries:
            f.write(line + "\n")


def create_dir_if_not_exist(dir_path: str) -> None:
    os.makedirs(dir_path, exist_ok=True)
