from __future__ import annotations

import json
import re
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path
from typing import Any

REQUIRED_FIELDS = {"name", "cnpj", "ibge_code"}
_CNPJ_PATTERN = re.compile(r"^\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}$")
_IBGE_PATTERN = re.compile(r"^\d{7}$")
_NS = {"x": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}


def is_valid_cnpj(value: str) -> bool:
    digits = re.sub(r"\D", "", value)
    if len(digits) != 14 or digits == digits[0] * 14:
        return False

    def check(base: str, weights: list[int]) -> str:
        remainder = sum(int(number) * weight for number, weight in zip(base, weights)) % 11
        return str(0 if remainder < 2 else 11 - remainder)

    first = check(digits[:12], [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2])
    second = check(digits[:12] + first, [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2])
    return digits[-2:] == first + second


def _cell_text(cell: ET.Element, shared_strings: list[str]) -> str:
    kind = cell.get("t")
    value = cell.find("x:v", _NS)
    if kind == "inlineStr":
        return "".join(node.text or "" for node in cell.findall(".//x:t", _NS)).strip()
    if value is None or value.text is None:
        return ""
    if kind == "s":
        return shared_strings[int(value.text)].strip()
    return value.text.strip()


def read_canonical_xlsx(path: str | Path) -> list[dict[str, str]]:
    """Read the repository's simple canonical workbook without third-party packages."""
    with zipfile.ZipFile(path) as archive:
        shared_strings: list[str] = []
        if "xl/sharedStrings.xml" in archive.namelist():
            root = ET.fromstring(archive.read("xl/sharedStrings.xml"))
            shared_strings = [
                "".join(node.text or "" for node in item.findall(".//x:t", _NS))
                for item in root.findall("x:si", _NS)
            ]
        sheet = ET.fromstring(archive.read("xl/worksheets/sheet1.xml"))

    rows: list[list[str]] = []
    for row in sheet.findall(".//x:sheetData/x:row", _NS):
        values = [_cell_text(cell, shared_strings) for cell in row.findall("x:c", _NS)]
        if any(values):
            rows.append(values)

    if not rows or rows[0][:3] != ["Municipio", "CNPJ", "IBGE"]:
        raise ValueError("Cabeçalho canônico esperado: Municipio, CNPJ, IBGE.")
    if any(len(row) < 3 for row in rows[1:]):
        raise ValueError("A planilha canônica contém linha incompleta.")
    return [
        {"name": row[0], "cnpj": row[1], "ibge_code": row[2]}
        for row in rows[1:]
    ]


def validate_portfolio(
    json_path: str | Path,
    xlsx_path: str | Path,
) -> list[dict[str, str]]:
    payload: Any = json.loads(Path(json_path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or not isinstance(payload.get("municipalities"), list):
        raise ValueError("municipalities.json deve conter a lista 'municipalities'.")
    records = payload["municipalities"]
    if len(records) != 121:
        raise ValueError(f"A carteira deve conter 121 registros; encontrados {len(records)}.")
    if payload.get("manifest", {}).get("record_count") != 121:
        raise ValueError("O manifest da carteira deve declarar record_count igual a 121.")

    cnpjs: set[str] = set()
    ibges: set[str] = set()
    for index, record in enumerate(records, 1):
        if not isinstance(record, dict) or set(record) != REQUIRED_FIELDS:
            raise ValueError(
                f"Registro {index} deve conter exatamente name, cnpj e ibge_code."
            )
        if not str(record["name"]).strip():
            raise ValueError(f"Registro {index} possui name vazio.")
        cnpj = str(record["cnpj"])
        ibge = str(record["ibge_code"])
        if not _CNPJ_PATTERN.fullmatch(cnpj):
            raise ValueError(f"Registro {index} possui CNPJ inválido: {cnpj}.")
        if not is_valid_cnpj(cnpj):
            raise ValueError(f"Registro {index} possui dígito verificador de CNPJ inválido.")
        if not _IBGE_PATTERN.fullmatch(ibge):
            raise ValueError(f"Registro {index} possui código IBGE inválido: {ibge}.")
        cnpj_digits = re.sub(r"\D", "", cnpj)
        if cnpj_digits in cnpjs or ibge in ibges:
            raise ValueError(f"Registro {index} duplica CNPJ ou código IBGE.")
        cnpjs.add(cnpj_digits)
        ibges.add(ibge)

    canonical = read_canonical_xlsx(xlsx_path)
    if records != canonical:
        raise ValueError("municipalities.json diverge da planilha canônica.")
    return records
