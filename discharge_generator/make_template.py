#!/usr/bin/env python3
"""
Convert real discharge document to template with placeholders.
Works on raw XML level to handle text split across runs.
"""

import zipfile
import shutil
import os

# Source and destination
SOURCE = "/var/home/htsapenko/Downloads/Тимошенко.docx"
TEMPLATE = "/var/home/htsapenko/Projects/Zav/discharge_generator/template_027.docx"

# Replacements: (original text, placeholder)
REPLACEMENTS = [
    # Patient name
    ("Тимошенко Максим Вадимович", "{{ПІБ}}"),

    # Birth date (may appear as 11.03.1997 or split)
    ("11.03.1997", "{{Дата_народження}}"),

    # Address (home address)
    ("Євгена Танцюри, буд. 22 б, кв. 14, м. Одеса, Одеська область, Україна", "{{Місце_проживання}}"),

    # Workplace + position (full)
    ('солдат мобілізований, в/ч 3057 НГУ 12 бригада спеціального призначення "АЗОВ", розвідник-далекомірник', "{{Заклад}}"),

    # Where discharge is sent to (destination medical unit)
    ("МСЧ в/ч 3057 НГУ", "{{Куди_виписка}}"),
    ("У МСЧ в/ч 3057 НГУ", "У {{Куди_виписка}}"),

    # Medical record number
    ("9078", "{{№_історії}}"),

    # Dates (admission/discharge)
    ("05.11.2025", "{{Дата_госпіталізації}}"),
    ("05.12.2025", "{{Дата_виписки}}"),

    # Doctor/Surgeon name
    ("Георгій Цапенко", "{{Хірург}}"),
]


def main():
    # Copy original
    shutil.copy(SOURCE, TEMPLATE)

    # Open as zip and modify document.xml
    temp_dir = "/tmp/docx_template"
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)
    os.makedirs(temp_dir)

    # Extract
    with zipfile.ZipFile(TEMPLATE, 'r') as zf:
        zf.extractall(temp_dir)

    # Read document.xml
    doc_path = os.path.join(temp_dir, 'word', 'document.xml')
    with open(doc_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Do replacements
    for old, new in REPLACEMENTS:
        if old in content:
            content = content.replace(old, new)
            print(f"  ✓ Replaced: {old[:40]}... → {new}")
        else:
            print(f"  ✗ Not found: {old[:40]}...")

    # Write back
    with open(doc_path, 'w', encoding='utf-8') as f:
        f.write(content)

    # Repackage docx
    os.remove(TEMPLATE)
    with zipfile.ZipFile(TEMPLATE, 'w', zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(temp_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arc_name = os.path.relpath(file_path, temp_dir)
                zf.write(file_path, arc_name)

    # Cleanup
    shutil.rmtree(temp_dir)

    print(f"\n✓ Template created: {TEMPLATE}")


if __name__ == "__main__":
    main()
