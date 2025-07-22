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
    full_url = base_url + suffix_url
    header_indices, target_table = find_web_table_and_headers(name_header, types_header, full_url)

    result: Dict[str, List[str]] = {}
    rows_with_invalid_types = []
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
            rows_with_invalid_types.append(" | ".join(cell.get_text(strip=True) for cell in cells))
            types = ["undefined type"]

        # Populate dictionary
        for t in types:
            if t not in result:
                result[t] = []
            result[t].append(name)

    write_log_file("rows_with_invalid_types.log", rows_with_invalid_types)
    write_log_file("lists_log.log", lists_log)

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
