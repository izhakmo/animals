from file import fetch_and_parse_wikipedia_table

if __name__ == "__main__":
    url = "https://en.wikipedia.org/wiki/List_of_animal_names"  # Example URL
    name_header = "Animal"
    types_header = "Collateral adjective"
    result = fetch_and_parse_wikipedia_table(url, name_header, types_header)
    print(result)