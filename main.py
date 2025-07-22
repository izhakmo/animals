from file import fetch_and_parse_wikipedia_table

if __name__ == "__main__":
    base_url = "https://en.wikipedia.org"
    suffix_url = "/wiki/List_of_animal_names"
    name_header = "Animal"
    types_header = "Collateral adjective"
    result = fetch_and_parse_wikipedia_table(base_url, suffix_url, name_header, types_header)
    print(result)