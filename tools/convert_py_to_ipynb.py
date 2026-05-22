import json
import re
import sys
from pathlib import Path

def convert_py_to_ipynb(py_path, ipynb_path):
    print(f"Converting {py_path} to {ipynb_path}...")
    with open(py_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Split by cell dividers: `# %%` at start of line
    parts = re.split(r'^# %%\s*', content, flags=re.MULTILINE)
    
    cells = []
    
    # The first part before any '# %%' might be a module docstring
    first_part = parts[0].strip()
    if first_part:
        if first_part.startswith('"""') and first_part.endswith('"""'):
            docstring_content = first_part[3:-3].strip()
            # Convert header lines like '=====' or '-----' to markdown headings
            doc_lines = docstring_content.splitlines()
            md_lines = []
            i = 0
            while i < len(doc_lines):
                line = doc_lines[i]
                if i + 1 < len(doc_lines) and re.match(r'^[=\-]+$', doc_lines[i + 1].strip()):
                    # Next line is a header underline
                    underline = doc_lines[i + 1].strip()
                    heading_level = 1 if underline.startswith('=') else 2
                    md_lines.append("#" * heading_level + " " + line + "\n")
                    i += 2  # skip the underline line
                else:
                    md_lines.append(line + "\n")
                    i += 1
            cells.append({
                "cell_type": "markdown",
                "metadata": {},
                "source": md_lines
            })
        else:
            cells.append({
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": first_part.splitlines(keepends=True)
            })
            
    for part in parts[1:]:
        lines = part.splitlines(keepends=True)
        if not lines:
            continue
        first_line = lines[0].strip()
        cell_source = lines[1:] if len(lines) > 1 else []
        
        # Check if it is a markdown cell
        if first_line.startswith('[markdown]'):
            clean_lines = []
            for line in cell_source:
                # Strip leading '#' and one optional space
                stripped = line.lstrip()
                if stripped.startswith('#'):
                    match = re.match(r'^\s*#\s?(.*)', line)
                    if match:
                        clean_lines.append(match.group(1) + '\n')
                    else:
                        clean_lines.append(line)
                else:
                    clean_lines.append(line)
            cells.append({
                "cell_type": "markdown",
                "metadata": {},
                "source": clean_lines
            })
        else:
            # Code cell. Keep the first line as part of the code
            cell_code = [lines[0]] + cell_source
            cells.append({
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": cell_code
            })
            
    notebook = {
        "cells": cells,
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3 (ipykernel)",
                "language": "python",
                "name": "python3"
            },
            "language_info": {
                "name": "python"
            }
        },
        "nbformat": 4,
        "nbformat_minor": 2
    }
    
    with open(ipynb_path, 'w', encoding='utf-8') as f:
        json.dump(notebook, f, indent=1)
    print(f"Successfully created {ipynb_path}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        # Default conversion for our tutorial files
        convert_py_to_ipynb(
            'tutorial_optimisation_accim_custom_model.py',
            'tutorial_optimisation_accim_custom_model.ipynb'
        )
        convert_py_to_ipynb(
            'tutorial_analysis_accim_custom_model.py',
            'tutorial_analysis_accim_custom_model.ipynb'
        )
    else:
        convert_py_to_ipynb(sys.argv[1], sys.argv[2])
