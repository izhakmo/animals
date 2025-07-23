import requests
from bs4 import BeautifulSoup
from typing import Dict, List, Optional
import re

from constants import TABLE_HEADER_TAG, TABLE_ROW_TAG, TABLE_CELL_TAG


def _fetch_url(url: str) -> str:
    try:
        response = requests.get(url, timeout=60)
        response.raise_for_status()
        return response.text
    except Exception as e:
        print(f"Failed to fetch the URL {url}: {e}")
        raise


def find_web_table_and_headers(name_header, types_header, url):
    response_text = _fetch_url(url)
    soup = BeautifulSoup(response_text, "html.parser")
    tables = soup.find_all("table")
    target_table = None
    header_indices = {}
    for table in tables:
        headers = table.find_all(TABLE_HEADER_TAG)
        header_texts = [h.get_text(strip=True) for h in headers]
        if name_header in header_texts and types_header in header_texts:
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


def extract_name_and_link(name_cell) -> (str, Optional[str]):
    name_raw = name_cell.get_text(separator="\n", strip=True)
    name = extract_first_line(name_raw)
    link_tag = name_cell.find('a')
    href = link_tag.get('href') if link_tag else None
    return name, href


def extract_list_link(name_cell) -> Optional[str]:
    for i_tag in name_cell.find_all('i'):
        a_tag = i_tag.find('a')
        if a_tag and 'list' in a_tag.get_text(strip=True).lower():
            return a_tag.get('href')
    return None


def extract_types_from_cell(types_cell) -> List[str]:
    _remove_footnotes_from_types(types_cell)
    types_raw = types_cell.get_text(separator="\n", strip=True)
    return split_multiple_types(types_raw)


def _remove_footnotes_from_types(types_cell) -> None:
    for span in types_cell.find_all("sup"):
        span.decompose()


def split_multiple_types(types_raw: str) -> List[str]:
    return [t.strip() for t in re.split(r'[\n\r]+', types_raw) if t.strip()]


def is_incomplete_row(cells: List, header_indices: Dict[str, int]) -> bool:
    return len(cells) <= max(header_indices['name'], header_indices['types'])


def _is_invalid_type(type_str: str) -> bool:
    return not re.search(r'\w', type_str)


def has_invalid_type(types: List[str]) -> bool:
    return not types or all(_is_invalid_type(t) for t in types)


def extract_first_line(text: str) -> str:
    return text.splitlines()[0].strip()
