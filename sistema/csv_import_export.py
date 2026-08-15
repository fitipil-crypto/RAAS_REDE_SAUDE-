"""
Utilitários para importação/exportação CSV de cadastros (Pacientes, Profissionais, Procedimentos).
"""
import csv
import io
from typing import List, Dict, Any


def build_csv(rows: List[Dict[str, Any]], columns: List[str], headers: List[str]) -> str:
    """Gera CSV com BOM e colunas customizadas."""
    output = io.StringIO()
    output.write('\ufeff')
    writer = csv.writer(output, delimiter=';', quoting=csv.QUOTE_MINIMAL)
    writer.writerow(headers)
    for row in rows:
        writer.writerow([row.get(col, '') or '' for col in columns])
    output.seek(0)
    return output.getvalue()


def parse_csv(content: bytes) -> List[Dict[str, str]]:
    """Parseia CSV enviado (latin-1 ou utf-8) e retorna lista de dicts."""
    text = content.decode("utf-8-sig", errors="replace")
    reader = csv.DictReader(io.StringIO(text), delimiter=';')
    return [row for row in reader if any(row.values())]


def normalize_bool(value: Any) -> bool:
    if value is None:
        return True
    v = str(value).strip().lower()
    return v not in ("false", "f", "não", "nao", "n", "0", "no", "")


def normalize_sn(value: Any) -> str:
    if value is None:
        return "N"
    v = str(value).strip().lower()
    return "S" if v in ("sim", "s", "yes", "true", "1") else "N"
