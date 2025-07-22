from typing import Dict, List
import os

def generate_html_report(result: Dict[str, List[str]], dir_path: str, html_filename: str):
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