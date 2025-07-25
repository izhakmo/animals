import time
from pipeline import fetch_and_parse_web_table

if __name__ == "__main__":
    base_url = "https://en.wikipedia.org"
    suffix_url = "/wiki/List_of_animal_names"
    name_header = "Animal"
    types_header = "Collateral adjective"
    
    start_time = time.time()
    result = fetch_and_parse_web_table(base_url, suffix_url, name_header, types_header)
    elapsed = time.time() - start_time
    print(f"Total program runtime: {elapsed:.2f} seconds")
    print(result)