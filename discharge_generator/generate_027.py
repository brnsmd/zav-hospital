#!/usr/bin/env python3
"""
Discharge Document Generator (Форма 027/о)
Simple template-based approach: load template, replace placeholders, save.
"""

import zipfile
import shutil
import os
from datetime import datetime

# Paths
TEMPLATE = os.path.join(os.path.dirname(__file__), "template_027.docx")
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")


def generate_discharge(patient_data: dict, output_path: str = None) -> str:
    """
    Generate a 027/о discharge document from template.

    Args:
        patient_data: dict with keys matching placeholders (without {{ }})
        output_path: optional output path, defaults to output/<ПІБ>_027.docx

    Returns:
        Path to generated document
    """
    # Ensure output directory exists
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Default output path
    if not output_path:
        name = patient_data.get('ПІБ', 'patient').replace(' ', '_')
        date = datetime.now().strftime('%Y%m%d')
        output_path = os.path.join(OUTPUT_DIR, f"{name}_{date}_027.docx")

    # Extract template to temp dir
    temp_dir = "/tmp/docx_gen_" + datetime.now().strftime('%H%M%S')
    os.makedirs(temp_dir, exist_ok=True)

    with zipfile.ZipFile(TEMPLATE, 'r') as zf:
        zf.extractall(temp_dir)

    # Read document.xml
    doc_path = os.path.join(temp_dir, 'word', 'document.xml')
    with open(doc_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Replace all placeholders
    for key, value in patient_data.items():
        placeholder = "{{" + key + "}}"
        if placeholder in content:
            # Escape XML special characters
            safe_value = str(value or '')
            safe_value = safe_value.replace('&', '&amp;')
            safe_value = safe_value.replace('<', '&lt;')
            safe_value = safe_value.replace('>', '&gt;')
            content = content.replace(placeholder, safe_value)

    # Write back
    with open(doc_path, 'w', encoding='utf-8') as f:
        f.write(content)

    # Repackage docx
    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(temp_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arc_name = os.path.relpath(file_path, temp_dir)
                zf.write(file_path, arc_name)

    # Cleanup
    shutil.rmtree(temp_dir)

    return output_path


def generate_from_airtable(record: dict) -> str:
    """
    Generate discharge from Airtable record format.
    Maps Airtable field names to template placeholders.
    """
    # Map Airtable fields to template placeholders
    patient_data = {
        'ПІБ': record.get('ПІБ'),
        'Дата_народження': record.get('Дата народження'),
        'Місце_проживання': record.get('Місце проживання'),
        'Заклад': record.get('Заклад'),
        'Куди_виписка': record.get('Куди виписка', 'МСЧ в/ч'),
        'Дата_госпіталізації': record.get('Дата госпіталізації'),
        'Дата_виписки': record.get('Дата виписки', datetime.now().strftime('%d.%m.%Y')),
        '№_історії': record.get('№ історії'),
        'Діагноз': record.get('Повний діагноз') or record.get('Діагноз'),
        'Скарги': record.get('Скарги пацієнта'),
        'Анамнез_хвороби': record.get('Анамнез хвороби'),
        'Анамнез_життя': record.get('Анамнез життя'),
        "Об'єктивний_стан": record.get("Об'єктивний стан"),
        'Лабораторні': record.get('Обстеження лабораторні'),
        'Інструментальні': record.get('Обстеження інструментальні'),
        'Консультації': record.get('Консультації'),
        'Операції': record.get('Операції'),
        'Лікування': record.get('Лікування'),
        'Результат': record.get('Результат лікування', 'Виписаний з поліпшенням'),
        'Рекомендації': record.get('Рекомендації'),
        'МВТН_початок': record.get('МВТН початок'),
        'МВТН_кінець': record.get('МВТН кінець'),
        'Хірург': record.get('Хірург'),
    }

    return generate_discharge(patient_data)


# ═══════════════════════════════════════════════════════════════════
# CLI INTERFACE (for n8n Execute Command)
# ═══════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    import sys
    import json

    # Mode 1: JSON from stdin (n8n mode)
    if not sys.stdin.isatty():
        try:
            input_data = json.load(sys.stdin)
            output_path = generate_from_airtable(input_data)
            print(json.dumps({
                "success": True,
                "file_path": output_path,
                "file_name": os.path.basename(output_path)
            }))
        except Exception as e:
            print(json.dumps({
                "success": False,
                "error": str(e)
            }))
            sys.exit(1)

    # Mode 2: Test mode (no stdin)
    else:
        test_patient = {
            'ПІБ': 'Тестовий Пацієнт Іванович',
            'Дата_народження': '01.01.1990',
            'Місце_проживання': 'м. Київ, вул. Тестова, 1',
            'Заклад': 'солдат, в/ч А0000',
            'Куди_виписка': 'МСЧ в/ч А0000',
            'Дата_госпіталізації': '01.01.2026',
            'Дата_виписки': '24.01.2026',
            '№_історії': '12345',
            'Діагноз': 'Тестовий діагноз. Код МКХ-10: Z00.0',
            'Скарги': 'Скарги на біль у тестовій ділянці',
            'Анамнез_хвороби': 'Захворів тестово 01.01.2026',
            'Анамнез_життя': 'Алергії немає. Шкідливі звички заперечує.',
            "Об'єктивний_стан": 'Стан задовільний. АТ 120/80.',
            'Лабораторні': 'ЗАК: Hb 140 г/л, Ер 4.5',
            'Інструментальні': 'Рентген: без патології',
            'Консультації': 'Терапевт: протипоказань немає',
            'Операції': 'Не проводились',
            'Лікування': 'Симптоматичне лікування',
            'Результат': 'Виписаний з поліпшенням',
            'Рекомендації': '1. Спостереження у хірурга\n2. Контроль через 2 тижні',
            'МВТН_початок': '01.01.2026',
            'МВТН_кінець': '24.01.2026',
            'Хірург': 'Тестовий Лікар',
        }

        output = generate_discharge(test_patient)
        print(f"✓ Generated: {output}")
