import requests
from bs4 import BeautifulSoup
from typing import Dict, List, Optional
import re
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

TABLE_HEADER_TAG = "th"
TABLE_ROW_TAG = "tr"
TABLE_CELL_TAG = "td"


def fetch_and_parse_wikipedia_table(base_url: str, suffix_url: str, name_header: str, types_header: str) -> Dict[
    str, List[str]]:
    full_url = base_url + suffix_url
    header_indices, target_table = find_wikipedia_table_and_headers(name_header, types_header, full_url)

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
        if has_invalid_types(types):
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

    generate_html_report(result, dir_path)

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


def get_main_image_url(wikipedia_url: str) -> Optional[str]:
    response = requests.get(wikipedia_url)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'html.parser')

    infobox = soup.find("table", class_="infobox")
    if infobox:
        img = infobox.find("img")
        if img and img.get("src"):
            # Wikipedia image paths are relative; prepend with protocol
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


def generate_html_report(result: Dict[str, List[str]], dir_path: str, html_filename: str = "report.html"):
    with open(html_filename, "w", encoding="utf-8") as f:
        f.write("<html><head><title>Animal Report</title></head><body>\n")
        f.write("<h1>Animal Types and Images</h1>\n")
        for key in sorted(result.keys()):
            values = result[key]
            f.write(f"<h2>{key}</h2>\n<ul>\n")
            for value in values:
                safe_name = value.replace('/', '_')
                image_path = os.path.join(dir_path, f"{safe_name}.jpg")
                f.write(f"<li>{value}<br>")
                if os.path.exists(image_path):
                    f.write(f'<img src="{image_path}" alt="{value}" style="max-width:200px;"><br>')
                else:
                    f.write("(could not find image)<br>")
                f.write("</li>\n")
            f.write("</ul>\n")
        f.write("</body></html>\n")
    

    