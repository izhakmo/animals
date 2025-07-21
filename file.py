import requests
from bs4 import BeautifulSoup
from typing import Dict, List
import re

def fetch_and_parse_wikipedia_table(wikipedia_url: str, name_header: str, types_header: str) -> Dict[str, List[str]]:
    # Fetch the HTML content
    response = requests.get(wikipedia_url)
    # TODO - what is this
    response.raise_for_status()
    # TODO - rename this soup
    soup = BeautifulSoup(response.text, "html.parser")

    # get all tables
    tables = soup.find_all("table")
    target_table = None
    header_indices = {}

    # find table with name_header and types_header
    for table in tables:
        # get all table headers
        headers = table.find_all("th")
        # extract header texts
        header_texts = [header.get_text(strip=True) for header in headers]
        if name_header in header_texts and types_header in header_texts:
            # Map header names to their column indices
            header_row = headers[0].find_parent("tr")
            header_cells = header_row.find_all(["th", "td"])
            for idx, cell in enumerate(header_cells):
                text = cell.get_text(strip=True)
                if text == name_header:
                    header_indices['name'] = idx
                if text == types_header:
                    header_indices['types'] = idx
            target_table = table
            break

    if not target_table or 'name' not in header_indices or 'types' not in header_indices:
        raise ValueError("Could not find a table with the specified headers.")

    result: Dict[str, List[str]] = {}
    errors_log = []
    lists_log = []

    # Process table rows
    for row in target_table.find_all("tr")[1:]:
        cells = row.find_all(["td", "th"])
        if len(cells) <= max(header_indices['name'], header_indices['types']):
            continue  # skip incomplete rows

        # Extract name and types
        name_cell = cells[header_indices['name']]
        types_cell = cells[header_indices['types']]

        # Handle <br> and newlines
        name_raw = name_cell.get_text(separator="\n", strip=True)
        types_raw = types_cell.get_text(separator="\n", strip=True)

        # Only consider the first line for name
        name = name_raw.splitlines()[0].strip() if name_raw else ""
        # Split types by lines
        types = [t.strip() for t in re.split(r'[\n\r]+', types_raw) if t.strip()]

        # Check for empty or non-alphanumeric types
        if not types or all(not re.search(r'\w', t) for t in types):
            errors_log.append(" | ".join(cell.get_text(strip=True) for cell in cells))
            continue

        # Check for (list) in name
        if name.lower().endswith("(list)"):
            lists_log.append(" | ".join(cell.get_text(strip=True) for cell in cells))
            continue

        # Populate dictionary
        for t in types:
            if not name:
                continue
            if t not in result:
                result[t] = []
            result[t].append(name)

    # Write logs
    with open("errors.log", "w", encoding="utf-8") as f:
        for line in errors_log:
            f.write(line + "\n")

    with open("animals_with_lists.log", "w", encoding="utf-8") as f:
        for line in lists_log:
            f.write(line + "\n")

    return result

# Example usage:
