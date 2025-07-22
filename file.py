import requests
from bs4 import BeautifulSoup
from typing import Dict, List, Optional
import re
import os

TABLE_HEADER_TAG = "th"
TABLE_ROW_TAG = "tr"
TABLE_CELL_TAG = "td"


def fetch_and_parse_wikipedia_table(base_url: str, suffix_url: str, name_header: str, types_header: str) -> Dict[str, List[str]]:
    full_url = base_url + suffix_url
    header_indices, target_table = find_wikipedia_table_and_headers(name_header, types_header, full_url)

    result: Dict[str, List[str]] = {}
    errors_log = []
    lists_log = []

    create_dir_if_not_exist("tmp")

    # Process table rows
    for row in target_table.find_all(TABLE_ROW_TAG)[1:]:
        cells = row.find_all([TABLE_CELL_TAG, TABLE_HEADER_TAG])
        if is_incomplete_row(cells, header_indices):
            continue

        # Extract name and types
        name_cell = cells[header_indices['name']]
        name, href = extract_name_and_link(name_cell)


        # TODO - here i will later on use threads or kafka to download the images and save them to a folder
        if href:
            # response_text = fetch_url(base_url + href)
            # soup = BeautifulSoup(response_text, "html.parser")
            # image_url = soup.find('img')['src']
            # print(f"Found image: {image_url}")
            pass

        types_cell = cells[header_indices['types']]
        types = extract_types_from_cell(types_cell)

        if list_link := extract_list_link(name_cell):
            # TODO - need to handle cases where we have no types_cell, multiple types
            lists_log.append(f"{name} | {types} | {list_link}")

        # Check for empty or non-alphanumeric types
        if has_invalid_types(types):
            errors_log.append(" | ".join(cell.get_text(strip=True) for cell in cells))
            continue

        # Populate dictionary
        for t in types:
            if t not in result:
                result[t] = []
            result[t].append(name)

    write_log_file("errors.log", errors_log)
    write_log_file("animals_with_lists.log", lists_log)


    return result


def write_log_file(filename: str, log_entries: List[str]) -> None:
    """Write log entries to a file, one per line."""
    with open(filename, "w", encoding="utf-8") as f:
        for line in log_entries:
            f.write(line + "\n")


def is_incomplete_row(cells: List, header_indices: Dict[str, int]) -> bool:
    """Check if a table row has enough cells to contain both required columns."""
    return len(cells) <= max(header_indices['name'], header_indices['types'])


def extract_first_line(text: str) -> str:
    """Extract and clean the first line from a multi-line text."""
    return text.splitlines()[0].strip()


def remove_footnotes_from_types(types_cell) -> None:
    for span in types_cell.find_all("sup"):
        span.decompose()


def split_multiple_types(types_raw: str) -> List[str]:
    """Parse types from raw text by splitting on newlines and cleaning whitespace."""
    return [t.strip() for t in re.split(r'[\n\r]+', types_raw) if t.strip()]


def extract_types_from_cell(types_cell) -> List[str]:
    remove_footnotes_from_types(types_cell)
    types_raw = types_cell.get_text(separator="\n", strip=True)
    # Split types by lines
    return split_multiple_types(types_raw)


def has_invalid_types(types: List[str]) -> bool:
    # TODO - make a function of 2nd part
    return not types or all(not re.search(r'\w', t) for t in types)


def fetch_url(url: str) -> str:
    try:
        response = requests.get(url, timeout=60)
        response.raise_for_status()
        return response.text
    # we can improve this error handling by catching specific exceptions
    except Exception as e:
        print(f"Failed to fetch the URL {url}: {e}")
        raise


def find_wikipedia_table_and_headers(name_header, types_header, wikipedia_url):
    # Fetch the HTML content
    response_text = fetch_url(wikipedia_url)
    soup = BeautifulSoup(response_text, "html.parser")
    # Find all tables
    tables = soup.find_all("table")
    target_table = None
    header_indices = {}
    # Find the first table with both headers
    for table in tables:
        headers = table.find_all(TABLE_HEADER_TAG)
        header_texts = [h.get_text(strip=True) for h in headers]
        if name_header in header_texts and types_header in header_texts:
            # Map header names to their column indices
            header_row = headers[0].find_parent(TABLE_ROW_TAG)
            header_cells = header_row.find_all([TABLE_HEADER_TAG, TABLE_CELL_TAG])
            for idx, cell in enumerate(header_cells):
                text = cell.get_text(strip=True)
                if text == name_header:
                    header_indices['name'] = idx
                if text == types_header:
                    header_indices['types'] = idx
            target_table = table
            break
    if not target_table or 'name' not in header_indices or 'types' not in header_indices:
        raise ValueError(f"Could not find a table with the specified headers: {name_header=}, {types_header=}")
    return header_indices, target_table


def extract_list_link(name_cell) -> Optional[str]:
    for item in name_cell.contents:
        item_str = str(item)
        if "<i>(<a href=" in item_str and "list</a>)</i>" in item_str:
            link = BeautifulSoup(item_str, "html.parser").find('a')
            return link.get('href') if link else None
    return None


def extract_name_and_link(name_cell) -> (str, Optional[str]):
    name_raw = name_cell.get_text(separator="\n", strip=True)
    # Only consider the first line for name
    name = extract_first_line(name_raw)
    link_tag = name_cell.find('a')
    href = link_tag.get('href') if link_tag else None
    return name, href


def create_dir_if_not_exist(dir_path: str) -> None:
    os.makedirs(dir_path, exist_ok=True)
