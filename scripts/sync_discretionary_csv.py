"""Sync official Transferegov Discricionarias e Legais CSVs, scoped to the 121 municipalities.

The source container is national. This connector never publishes the raw national files:
it streams each CSV, keeps rows whose CNPJ/IBGE matches the official portfolio, and writes
scoped JSON plus checkpoint/status metadata. Unknown relationships are preserved as fields,
not guessed.
"""
from __future__ import annotations

import argparse, csv, io, json, re, time, zipfile
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
CATALOG_URL = "https://api-publica.transferegov.gestao.gov.br/downloads/dadosgov/?restype=container&comp=list"
BLOB_BASE = "https://api-publica.transferegov.gestao.gov.br/downloads/dadosgov/"
DEFAULT_DATASETS = ("siconv_programa", "siconv_proposta", "siconv_convenio", "siconv_contrato", "siconv_empenho", "siconv_desembolso", "siconv_pagamento", "siconv_licitacao")

def digits(value: object) -> str:
    return re.sub(r"\D", "", str(value or ""))

def load_portfolio() -> tuple[set[str], set[str]]:
    rows = json.loads((ROOT / "site/data/municipalities.json").read_text(encoding="utf-8"))["municipalities"]
    return ({digits(r["cnpj"]) for r in rows}, {str(r["ibge_code"]) for r in rows})

def catalog() -> dict[str, str]:
    root = ET.fromstring(urlopen(Request(CATALOG_URL, headers={"User-Agent": "GovParcerias/1.0"}), timeout=60).read())
    return {b.findtext("./{*}Name").removesuffix(".zip"): urljoin(BLOB_BASE, b.findtext("./{*}Name")) for b in root.findall(".//{*}Blob") if b.findtext("./{*}Name")}

def row_is_scoped(row: dict[str, str], cnpjs: set[str], ibges: set[str]) -> bool:
    for key, value in row.items():
        key_norm = re.sub(r"[^a-z0-9]", "", key.lower())
        value_digits = digits(value)
        if ("cnpj" in key_norm or "cpfcnpj" in key_norm) and value_digits in cnpjs:
            return True
        if ("ibge" in key_norm or "codmunicipio" in key_norm or "municipio" in key_norm and "cod" in key_norm) and str(value or "").strip() in ibges:
            return True
    return False

def sync_dataset(name: str, url: str, out_dir: Path, cnpjs: set[str], ibges: set[str]) -> dict:
    raw = urlopen(Request(url, headers={"User-Agent": "GovParcerias/1.0"}), timeout=180).read()
    rows: list[dict[str, str]] = []
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        members = [m for m in archive.namelist() if m.lower().endswith(".csv")]
        if not members:
            raise ValueError(f"Arquivo oficial sem CSV: {name}")
        with archive.open(members[0]) as stream:
            wrapper = io.TextIOWrapper(stream, encoding="utf-8-sig", errors="replace", newline="")
            reader = csv.DictReader(wrapper, delimiter=";")
            for row in reader:
                if row_is_scoped(row, cnpjs, ibges):
                    rows.append(dict(row))
    stamp = datetime.now(timezone.utc).isoformat()
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / f"{name}.json").write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    status = {"dataset": name, "source": "Transferegov - Discricionárias e Legais", "source_url": url, "fetched_at": stamp, "scope": "121 municípios", "records": len(rows), "completed": True, "national_raw_published": False}
    (out_dir / f"{name}_sync_status.json").write_text(json.dumps(status, ensure_ascii=False, indent=2), encoding="utf-8")
    return status

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", action="append", dest="datasets", help="dataset name; repeatable")
    parser.add_argument("--sleep", type=float, default=1.0)
    args = parser.parse_args()
    cnpjs, ibges = load_portfolio()
    available = catalog()
    selected = args.datasets or list(DEFAULT_DATASETS)
    out_dir = ROOT / "data/published/transferegov_discricionarias"
    statuses = []
    for name in selected:
        if name not in available:
            raise SystemExit(f"Dataset não encontrado no catálogo oficial: {name}")
        statuses.append(sync_dataset(name, available[name], out_dir, cnpjs, ibges))
        time.sleep(args.sleep)
    (out_dir / "sync_status.json").write_text(json.dumps({"source": CATALOG_URL, "datasets": statuses, "completed": True}, ensure_ascii=False, indent=2), encoding="utf-8")

if __name__ == "__main__":
    main()
